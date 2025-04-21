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

from app.config import get_settings
from app.infrastructure.clinical_trials_gov.api_requests import (
    fetch_study,
    list_studies,
)
from app.services.clinical_trials_agent import GPT_41_MINI, template_manager

ToolType = FunctionTool | FileSearchTool | WebSearchTool | ComputerTool

settings = get_settings()


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
