"""Chat API endpoints for clinical trials conversational interface.

This module contains FastAPI endpoints that handle chat functionality,
allowing users to interact with the clinical trials agent, send messages,
and retrieve conversation history.
"""

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import inject_db
from app.services.clinical_trials_agent.clinical_trials_agent import (
    ChatResponse,
    get_session_messages,
    post_turn,
)

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request schema.

    Contains the user's message text to be processed by the clinical trials agent.

    Attributes:
        text: The user's message text
    """
    text: str


@router.post("/chat", response_model=ChatResponse)
async def post_chat_new_session(request: ChatRequest,
                                correlation_id: str = Header(
                                    alias="X-Correlation-ID"),
                                db: AsyncSession = Depends(inject_db)) -> ChatResponse:
    """Process a new chat message and return the updated conversation.

    Handles incoming chat messages, processes them through the clinical trials agent,
    and returns the updated conversation history.
    """
    return await post_turn(None, request.text, correlation_id, db)


@router.post("/chat/{session_uuid}", response_model=ChatResponse)
async def post_chat_existing_session(session_uuid: str | None,
                                     request: ChatRequest,
                                     correlation_id: str = Header(lias="X-Correlation-ID"),
                                     db: AsyncSession = Depends(inject_db)) -> ChatResponse:
    """Process a new chat message and return the updated conversation.

    Handles incoming chat messages, processes them through the clinical trials agent,
    and returns the updated conversation history.

    Args:
        session_uuid: Optional unique identifier for the chat session.
                      If not provided, a new session will be created.
        request: The chat request containing the user's message text
        correlation_id: Request correlation ID for tracing and logging
        db: Database session for persisting chat data

    Returns:
        ChatResponse: Object containing the updated conversation messages
    """
    return await post_turn(session_uuid, request.text, correlation_id, db)


@router.get("/chat/{session_uuid}", response_model=ChatResponse)
async def get_chat(session_uuid: str,
                   db: AsyncSession = Depends(inject_db)) -> ChatResponse:
    """Retrieve the conversation history for a specific chat session.

    Gets all messages for the specified chat session from the database.

    Args:
        session_uuid: Unique identifier for the chat session
        db: Database session for retrieving chat data

    Returns:
        ChatResponse: Object containing the conversation messages
    """
    return await get_session_messages(session_uuid, db)
