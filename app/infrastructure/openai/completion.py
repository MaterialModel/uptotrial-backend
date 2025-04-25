import logging
from collections.abc import AsyncGenerator
from typing import Any

from openai import AsyncOpenAI
from openai.types.responses import ResponseStreamEvent, ResponseTextDeltaEvent

from app.config import get_settings
from app.infrastructure.openai.engines import GPT_41_MINI

settings = get_settings()

logger = logging.getLogger(__name__)


async def stream_response(input_text: str,
                          *,
                          model: str = GPT_41_MINI,
                          **kwargs: Any,
                          ) -> AsyncGenerator[ResponseStreamEvent, None]:
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response_stream = await client.responses.create(
        model=model,
        input=input_text,
        stream=True,
        **kwargs,
    )
 
    async for event in response_stream:
        yield event

async def stream_response_text(input_text: str,
                               *,
                               model: str = GPT_41_MINI,
                               **kwargs: Any,
                               ) -> AsyncGenerator[str, None]:
    async for event in stream_response(input_text, model=model, **kwargs):
        if isinstance(event, ResponseTextDeltaEvent):
            yield event.delta