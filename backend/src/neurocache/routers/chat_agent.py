"""Chat agent router.

Provides the POST /chat/stream endpoint for general conversational
interaction with the user's knowledge base.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from neurocache.agents.chat_agent import chat_agent_stream
from neurocache.dependencies.auth.auth import AuthenticatedUser
from neurocache.dependencies.db import get_async_sqlalchemy_session
from neurocache.dependencies.openai import get_openai_client
from neurocache.schemas.message import UserMessage

logger = logging.getLogger(__name__)

chat_router = APIRouter(prefix="/chat", tags=["chat"])


@chat_router.post("/stream")
async def stream_chat(message: UserMessage, user_id: AuthenticatedUser) -> StreamingResponse:
    """Chat agent streaming endpoint.

    Provides general conversational interaction with the user's knowledge base.

    Args:
        message: User message containing query and thread_id

    Returns:
        Server-Sent Events stream of agent responses
    """

    async def sse_generator() -> AsyncGenerator[str, None]:
        try:
            # Manage DB session inside the generator to ensure proper lifecycle
            async with get_async_sqlalchemy_session() as db:
                openai_client = get_openai_client()
                async for sse_data in chat_agent_stream(message, db, user_id, openai_client):
                    yield sse_data
        except asyncio.CancelledError:
            logger.info("Chat agent streaming cancelled (client disconnected)")
            raise
        except Exception:
            logger.exception("Error during chat agent streaming")
            raise

    return StreamingResponse(
        sse_generator(),
        media_type="text/plain",  # Vercel AI SDK expects text/plain for data stream protocol
        headers={
            "x-vercel-ai-ui-message-stream": "v1",  # Required for new data stream protocol
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
