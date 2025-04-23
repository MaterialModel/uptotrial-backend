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
from app.services.clinical_trials_agent import GPT_41_MINI, template_manager

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
    ]

    hosted_tools = [
        WebSearchTool(),
    ]

    agent_system_prompt = template_manager.render("clinical_trials_agent.jinja")

    return Agent(
        name="Clinical Trials Agent",
        instructions=agent_system_prompt,
        model=GPT_41_MINI,
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


async def post_turn_streamed(session_uuid: str | None,
                             text: str,
                             correlation_id: str,
                             db: AsyncSession) -> AsyncGenerator[str, None]:
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
    chunks: list[str] = []

    with trace("Clinical Trials Agent", trace_id=session.openai_trace_id) as trace_obj:
        streamed_response = await Runner.run_streamed(agent, messages)  # type: ignore[arg-type]
        session.openai_trace_id = trace_obj.trace_id
        async for chunk in streamed_response:
            yield chunk
            chunks.append(chunk)

    await session.add_turn(text, ''.join(chunks), correlation_id, db)
    return


async def get_session_messages(session_uuid: str, db: AsyncSession) -> ChatResponse:
    """Get all messages from a session."""

    session = await db.execute(select(Session).where(Session.session_uuid == session_uuid))
    session = session.scalar_one()
    dialogue_turns = await session.get_dialogue_turns(db)
    return ChatResponse(messages=make_messages_from_dialogue_turns(dialogue_turns),
                             session_uuid=session_uuid)
