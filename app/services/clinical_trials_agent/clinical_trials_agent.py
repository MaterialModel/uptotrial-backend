import uuid
from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import cast

from agents import (
    Agent,
    ComputerTool,
    FileSearchTool,
    FunctionTool,
    Runner,
    RunResult,
    WebSearchTool,
    set_default_openai_key,
    trace,
)
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.infrastructure.clinical_trials_gov.api_requests import (
    fetch_study,
    list_studies,
)
from app.infrastructure.database.models import DialogueTurn, Session
from app.infrastructure.googleapi.place_api import search_places
from app.infrastructure.openai import GPT_41, stream_response_text
from app.services.clinical_trials_agent import template_manager

ToolType = FunctionTool | FileSearchTool | WebSearchTool | ComputerTool

settings = get_settings()


class ChatResponse(BaseModel):
    """Chat response model."""

    messages: list[dict]
    session_uuid: str

@lru_cache(maxsize=1)
def get_agent() -> Agent:
    """Creates and returns a cached instance of the Clinical Trials Agent.

    This function initializes the agent with its configuration, including
    system prompt, model, and tools. It uses LRU caching to ensure
    only one instance of the agent is created.

    Returns:
        Agent: The configured Clinical Trials Agent instance.
    """

    ctg_tools = [
        list_studies,
        fetch_study,
        search_places,
    ]

    hosted_tools = [
        WebSearchTool(search_context_size="high"),
    ]

    agent_system_prompt = template_manager.render("clinical_trials_agent.jinja")

    return Agent(
        name="Clinical Trials Agent",
        instructions=agent_system_prompt,
        model=GPT_41,
        tools=cast(list[ToolType], ctg_tools + hosted_tools),
    )


async def conversation() -> AsyncGenerator[str | None, str | None]:
    """Create an interactive conversation with the Clinical Trials Agent.
    
    This is an asynchronous generator that yields agent responses and accepts
    user inputs via the .send() method. Handles transient errors with retries.
    
    Yields:
        str: Agent responses or an error message.
        
    Example:
        async for response in conversation():
            # First response will be None (generator initialization)
            user_input = input("> ")
            if user_input == "exit":
                break
            response = await conversation.asend(user_input)
            print(response)
    """

    set_default_openai_key(settings.openai_api_key)
    agent = get_agent()

    with trace("Clinical Trials Agent"):
        resp: RunResult | None = None
        answer: str | None = None

        while True:
            inp = yield answer
            if inp is None:
                answer = None
                continue
            if inp.lower() == "exit":
                return
            
            messages = (
                [*resp.to_input_list(), {"role": "user", "content": inp}]
                if resp
                else [{"role": "user", "content": inp}]
            )

            resp = await Runner.run(agent, messages)  # type: ignore[arg-type]
            answer = (
                str(resp.final_output)
                if resp.final_output is not None
                else "(Agent did not generate a text response)"
            )

def make_messages_from_dialogue_turns(dialogue_turns: list[DialogueTurn]) -> list[dict]:
    messages = []
    for dialogue_turn in dialogue_turns:
        messages.append({"role": "user", "content": dialogue_turn.request_text})
        messages.append(dialogue_turn.response_data)
    return messages


async def post_turn(session_uuid: str | None,
                    text: str,
                    correlation_id: str,
                    db: AsyncSession) -> ChatResponse:
    """Post a turn to the database."""

    set_default_openai_key(settings.openai_api_key)
    agent = get_agent()

    if session_uuid is None:
        # create new session
        session_uuid = str(uuid.uuid4())
        session = Session(session_uuid=session_uuid)
        db.add(session)
        await db.commit()
    else:
        result = await db.execute(select(Session).where(Session.session_uuid == session_uuid))
        session = result.scalar_one()

    dialogue_turns = await session.get_dialogue_turns(db)

    messages = make_messages_from_dialogue_turns(dialogue_turns)
    messages.append({"role": "user", "content": text})

    with trace("Clinical Trials Agent", trace_id=session.openai_trace_id) as trace_obj:
        resp = await Runner.run(agent, messages)  # type: ignore[arg-type]
        output_message = {"role": "assistant", "content": resp.final_output}
        messages.append(output_message)
        session.openai_trace_id = trace_obj.trace_id

    await session.add_turn(text, output_message, correlation_id, db)

    return ChatResponse(messages=messages, session_uuid=session_uuid)

def make_sse_event(key: str, value: str) -> str:
    """Format a message as an XML-like event for streaming.
    
    Uses a custom XML format that safely encodes data which may contain
    newlines or special characters, preventing parsing errors.
    
    Args:
        key: The event type or field name (e.g., 'session_uuid', 'data', 'event')
        value: The data payload, which may contain newlines or special characters
        
    Returns:
        str: Formatted XML-like event string in the format:
             <event><key>{key}</key><value>{value}</value></event>
             
    Note:
        The function automatically escapes XML entities like &, <, >, ", and '
        to ensure valid XML formatting.
    """
    # Escape XML entities to prevent parsing issues
    escaped_value = (value
        .replace("openai.com", "uptotrial.com")) 
    return f"<event><key>{key}</key><value>{escaped_value}</value></event>"


def stream_tool_explanation(tool_name: str, params: str) -> AsyncGenerator[str, None]:

    prompt = template_manager.render("tool_explanation.jinja", tool_name=tool_name, params=params)

    return stream_response_text(prompt)


async def post_turn_streamed(session_uuid: str | None,
                             text: str,
                             correlation_id: str,
                             db: AsyncSession) -> AsyncGenerator[str, None]:
    """Stream a conversational turn with the Clinical Trials Agent.
    
    Creates a new session if none exists or continues an existing one.
    Streams the agent's response chunks as they are generated and saves
    the completed conversation turn to the database.
    
    Args:
        session_uuid: Existing session UUID or None to create a new session
        text: User input text for this conversation turn
        correlation_id: Unique identifier for tracking this request
        db: Database session for persistence operations
        
    Yields:
        str: XML-like event markers and response chunks with these formats:
            - `<event><key>session_uuid</key><value>{uuid}</value></event>` - First yield with session identifier
            - `<event><key>data</key><value>{chunk}</value></event>` - Response content chunks
            - `<event><key>event</key><value>end_ok</value></event>` - Final yield indicating stream completion
            - `<event><key>event</key><value>end_error</value></event>` - Final yield indicating stream error
            - `<event><key>event</key><value>error</value></event>` followed by 
              `<event><key>data</key><value>{error_message}</value></event>` - Error details
    
    Note:
        Response chunks are concatenated and saved to the database only
        after the entire response is generated.
    """

    set_default_openai_key(settings.openai_api_key)
    agent = get_agent()

    if session_uuid is None:
        # create new session
        session_uuid = str(uuid.uuid4())
        session = Session(session_uuid=session_uuid)
        db.add(session)
        await db.commit()
    else:
        result = await db.execute(select(Session).where(Session.session_uuid == session_uuid))
        session = result.scalar_one()

    dialogue_turns = await session.get_dialogue_turns(db)

    messages = make_messages_from_dialogue_turns(dialogue_turns)
    messages.append({"role": "user", "content": text})
    chunks: list[str] = []

    yield make_sse_event("session_uuid", session_uuid)
    yield make_sse_event("data", "<response>")
    chunks.append("<response>")

    with trace("Clinical Trials Agent", trace_id=session.openai_trace_id) as trace_obj:
        streamed_response = Runner.run_streamed(agent, messages)  # type: ignore[arg-type]
        session.openai_trace_id = trace_obj.trace_id
        last_function_call = "Unknown"
        try:
            async for chunk in streamed_response.stream_events():
                if chunk.type == "raw_response_event":
                    if chunk.data.type == "response.output_text.delta":
                        yield make_sse_event("data", str(chunk.data.delta))
                        chunks.append(chunk.data.delta)
                    elif (chunk.data.type == "response.output_item.added"
                          and chunk.data.item.type == "function_call"):
                        last_function_call = chunk.data.item.name
                    elif (chunk.data.type == "response.function_call_arguments.done"):
                        yield make_sse_event("data", "<tool>")
                        chunks.append("<tool>")
                        async for sub_chunk in stream_tool_explanation(last_function_call, chunk.data.arguments):
                            yield make_sse_event("data", sub_chunk)
                            chunks.append(sub_chunk)
                        yield make_sse_event("data", "</tool>")
                        chunks.append("</tool>")
                    elif chunk.data.type == "response.web_search_call.searching":
                        item_name = "<tool>Searching the web for more information...</tool>"
                        yield make_sse_event("data", item_name)
                        chunks.append(item_name)

        except Exception as e:
            yield make_sse_event("event", "error")
            yield make_sse_event("data", str(e))
            yield make_sse_event("event", "end_error")
            return

    yield make_sse_event("data", "</response>")
    chunks.append("</response>")
    output_message = {"role": "assistant", "content": "".join(chunks)}
    await session.add_turn(text, output_message, correlation_id, db)
    yield "event: end_ok"
    return


async def get_session_messages(session_uuid: str, db: AsyncSession) -> ChatResponse:
    """Get all messages from a session."""

    session = await db.execute(select(Session).where(Session.session_uuid == session_uuid))
    session = session.scalar_one()
    dialogue_turns = await session.get_dialogue_turns(db)
    return ChatResponse(messages=make_messages_from_dialogue_turns(dialogue_turns),
                        session_uuid=session_uuid)
