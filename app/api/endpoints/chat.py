"""Chat API endpoints for clinical trials conversational interface.

This module contains FastAPI endpoints that handle chat functionality,
allowing users to interact with the clinical trials agent, send messages,
and retrieve conversation history.
"""


from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.clinical_trials_agent.clinical_trials_agent import (
    ChatResponse,
    get_session_messages,
    post_turn,
    post_turn_streamed,
)

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request schema.

    Contains the user's message text to be processed by the clinical trials agent.

    Attributes:
        text: The user's message text
    """
    text: str


@router.post("/", response_model=ChatResponse)
async def create_chat_session(request: ChatRequest,
                          correlation_id: str = Header(alias="X-Correlation-ID"),
                          db: AsyncSession = Depends(get_db)) -> ChatResponse:
    """Create a new chat session with the initial message.

    Processes the first message through the clinical trials agent and
    creates a new session with the conversation.
    """
    return await post_turn(None, request.text, correlation_id, db)


@router.post("/{session_uuid}", response_model=ChatResponse)
async def add_message_to_session(session_uuid: str,
                               request: ChatRequest,
                               correlation_id: str = Header(alias="X-Correlation-ID"),
                               db: AsyncSession = Depends(get_db)) -> ChatResponse:
    """Add a new message to an existing chat session.

    Processes a message through the clinical trials agent within the context
    of an existing chat session.

    Args:
        session_uuid: Unique identifier for the chat session
        request: The chat request containing the user's message text
        correlation_id: Request correlation ID for tracing and logging
        db: Database session for persisting chat data

    Returns:
        ChatResponse: Object containing the updated conversation messages
    """
    return await post_turn(session_uuid, request.text, correlation_id, db)


@router.get("/{session_uuid}", response_model=ChatResponse)
async def get_session_history(session_uuid: str,
                           db: AsyncSession = Depends(get_db)) -> ChatResponse:
    """Retrieve the conversation history for a specific chat session.

    Gets all messages for the specified chat session from the database.

    Args:
        session_uuid: Unique identifier for the chat session
        db: Database session for retrieving chat data

    Returns:
        ChatResponse: Object containing the conversation messages
    """
    return await get_session_messages(session_uuid, db)


@router.post(
    "/streaming/new",
    responses={
        200: {
            "content": {"text/event-stream": {"schema": {"type": "string"}}},
            "description": "A stream of Server-Sent Events.",
        },
    },
)
async def stream_new_session(
    chat: ChatRequest,
    correlation_id: str = Header(alias="X-Correlation-ID"),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream the clinical trials agent's response for a new session as Server-Sent Events.

    Creates a new chat session and streams the agent's response in real-time using
    Server-Sent Events. The client will receive events in the following XML-like format:
    
    - `<event><key>session_uuid</key><value>{uuid}</value></event>` - First event with session identifier
    - `<event><key>data</key><value>{chunk}</value></event>` - Response content chunks
    - `<event><key>event</key><value>end_ok</value></event>` - Final event indicating successful completion
    - `<event><key>event</key><value>end_error</value></event>` - Final event indicating an error occurred
    - `<event><key>event</key><value>error</value></event>` followed by 
      `<event><key>data</key><value>{error_message}</value></event>` - Error details
    
    The complete response is automatically saved to the database after streaming completes.
    
    Args:
        chat: The chat request containing the user's message text
        correlation_id: Request correlation ID for tracing and logging
        db: Database session for persisting chat data
        
    Returns:
        StreamingResponse: A streaming response with content-type text/event-stream
    """

    return StreamingResponse(
        post_turn_streamed(
            None,
            chat.text,
            correlation_id,
            db,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post(
    "/streaming/{session_uuid}",
    responses={
        200: {
            "content": {"text/event-stream": {"schema": {"type": "string"}}},
            "description": "A stream of Server-Sent Events.",
        },
    },
)
async def stream_existing_session(
    session_uuid: str,
    chat: ChatRequest,
    correlation_id: str = Header(alias="X-Correlation-ID"),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream the clinical trials agent's response for an existing session as Server-Sent Events.

    Continues an existing chat session and streams the agent's response in real-time using
    Server-Sent Events. The client will receive events in the following XML-like format:
    
    - `<event><key>session_uuid</key><value>{uuid}</value></event>` - For reference (new sessions only)
    - `<event><key>data</key><value>{chunk}</value></event>` - Response content chunks
    - `<event><key>event</key><value>end_ok</value></event>` - Final event indicating successful completion
    - `<event><key>event</key><value>end_error</value></event>` - Final event indicating an error occurred
    - `<event><key>event</key><value>error</value></event>` followed by 
      `<event><key>data</key><value>{error_message}</value></event>` - Error details
    
    The complete response is automatically saved to the database after streaming completes.
    
    Args:
        session_uuid: Unique identifier for the existing chat session
        chat: The chat request containing the user's message text
        correlation_id: Request correlation ID for tracing and logging
        db: Database session for persisting chat data
        
    Returns:
        StreamingResponse: A streaming response with content-type text/event-stream
    """

    return StreamingResponse(
        post_turn_streamed(
            session_uuid,
            chat.text,
            correlation_id,
            db,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
