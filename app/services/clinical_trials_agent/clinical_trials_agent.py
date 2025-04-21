from collections.abc import AsyncGenerator
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
from app.services.clinical_trials_agent.template_manager import jinja_template_manager

settings = get_settings()

GPT_41_MINI = "gpt-4.1-mini"

ctg_tools = [
    list_studies,
    fetch_study,
]

hosted_tools = [
    WebSearchTool(),
]

agent_system_prompt = jinja_template_manager.render(
    "clinical_trials_agent.jinja",
)

ToolType = FunctionTool | FileSearchTool | WebSearchTool | ComputerTool

agent = Agent(
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
