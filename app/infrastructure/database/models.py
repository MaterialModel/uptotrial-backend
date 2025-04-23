from datetime import datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, aliased, mapped_column

from app.infrastructure.database.session import DeclarativeBase


class User(DeclarativeBase):
    """User model.
    
    Represents a user in the system with authentication and permission information.
    
    Attributes:
        id: Unique identifier for the user
        created_at: Timestamp when the user record was created
        email: User's email address, must be unique
        password: Hashed password for authentication
        name: User's full name
        is_active: Whether the user account is active
        is_logged_in: Current login status of the user
        user_type: Type of user account (e.g., "admin", "patient", "doctor")
        user_permissions: List of permission strings granted to this user
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())

    email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_logged_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    user_type: Mapped[str] = mapped_column(String, nullable=False)
    user_permissions: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)


class DialogueTurn(DeclarativeBase):
    """Dialogue turn model.
    
    Represents a single exchange (request and response) in a conversation session.
    Dialogue turns form a linked list via the previous_turn_id field, allowing
    the system to trace conversation history.
    
    Attributes:
        id: Unique identifier for the dialogue turn
        created_at: Timestamp when the turn was created
        session_id: Foreign key to the parent session
        correlation_id: Identifier for tracking this exchange across systems
        request_text: The text input from the user
        response_data: JSON data containing the system's response
        previous_turn_id: Foreign key to the previous turn in this conversation
    """
    __tablename__ = "dialogue_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())

    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    request_text: Mapped[str] = mapped_column(String, nullable=False)
    response_data: Mapped[dict] = mapped_column(JSONB, nullable=True)

    previous_turn_id: Mapped[int] = mapped_column(ForeignKey("dialogue_turns.id"), nullable=True)


class Session(DeclarativeBase):
    """Session model.
    
    Represents a conversation session between a user and the system.
    Sessions contain dialogue turns and track the most recent turn through
    the head_turn_id field. Sessions support methods to retrieve the full
    conversation history and to add new turns.
    
    Attributes:
        id: Unique identifier for the session
        created_at: Timestamp when the session was created
        updated_at: Timestamp when the session was last updated
        head_turn_id: Foreign key to the most recent dialogue turn
        session_uuid: Externally-facing unique identifier for the session
        user_id: Foreign key to the user who owns this session (optional)
    """
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    head_turn_id: Mapped[int] = mapped_column(ForeignKey("dialogue_turns.id"), nullable=True)
    session_uuid: Mapped[str] = mapped_column(String, nullable=False, index=True, unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)

    async def get_dialogue_turns(self, db: AsyncSession) -> list[DialogueTurn]:
        """Get all dialogue turns for this session using a recursive CTE with SQLAlchemy ORM.
        
        Args:
            db: Database session
            
        Returns:
            list[DialogueTurn]: All dialogue turns in this session, ordered from newest to oldest
        """
        if self.head_turn_id is None:
            return []
        # Create base query for the head turn
        base_query = (
            select(DialogueTurn)
            .where(DialogueTurn.id == self.head_turn_id)
        )
        
        # Create recursive CTE
        turn_chain = base_query.cte(name="turn_chain", recursive=True)
        
        # Create an alias for the CTE
        tc = aliased(turn_chain, name="tc")
        
        # Create an alias for DialogueTurn
        dt = aliased(DialogueTurn, name="dt")
        
        # Create the recursive part of the CTE
        recursive_query = (
            select(dt)
            .join(tc, dt.id == tc.c.previous_turn_id)
        )
        
        # Combine base and recursive parts
        turn_chain = turn_chain.union_all(recursive_query)
        
        # Final query that selects from the CTE
        final_query = select(DialogueTurn).join(
            turn_chain, DialogueTurn.id == turn_chain.c.id,
        )
        
        result = await db.execute(final_query)
        dialogue_turns = result.scalars().all()
        
        return list(dialogue_turns)
    
    async def add_turn(
        self, 
        request_text: str, 
        response_data: dict,
        correlation_id: str, 
        db: AsyncSession,
        *,
        commit: bool = True,
    ) -> DialogueTurn:
        """Add a new dialogue turn to this session.
        
        Creates a new DialogueTurn linked to the current head turn and
        updates the session's head_turn_id to point to the new turn.
        
        Args:
            request_text: The user's request text
            response_data: Response data as a JSON-serializable dict
            correlation_id: Correlation ID for tracking
            db: Database session
            commit: Whether to commit the transaction immediately
            
        Returns:
            DialogueTurn: The newly created dialogue turn
        """
        # Create new turn
        new_turn = DialogueTurn(
            session_id=self.id,
            correlation_id=correlation_id,
            request_text=request_text,
            response_data=response_data,
            previous_turn_id=self.head_turn_id,
        )
        
        # Add new turn to the session
        db.add(new_turn)
        await db.flush()
        
        # Update session to point to the new head turn
        self.head_turn_id = new_turn.id
        db.add(self)
        if commit:
            await db.commit()
        else:
            await db.flush()
        
        return new_turn
