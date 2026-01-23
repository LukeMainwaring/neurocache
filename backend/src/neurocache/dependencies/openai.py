from typing import Annotated

from fastapi import Depends
from openai import AsyncOpenAI

from neurocache.core.config import get_settings

config = get_settings()

_openai_client: AsyncOpenAI = AsyncOpenAI()


def get_openai_client() -> AsyncOpenAI:
    return _openai_client


OpenAIClientDep = Annotated[AsyncOpenAI, Depends(get_openai_client)]
