"""Chat agent router.

Provides the POST /chat/stream endpoint for general conversational
interaction with the user's knowledge base.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from pydantic_ai.messages import BuiltinToolReturnPart, ModelResponse
from pydantic_ai.models.openai import OpenAIResponsesModelSettings
from pydantic_ai.ui.vercel_ai import VercelAIAdapter
from starlette.requests import Request
from starlette.responses import Response

from neurocache.agents.chat_agent import chat_agent
from neurocache.agents.deps import AgentDeps
from neurocache.dependencies.auth.auth import AuthenticatedUser
from neurocache.dependencies.db import AsyncPostgresSessionDep
from neurocache.dependencies.openai import get_openai_client
from neurocache.models.message import Message
from neurocache.models.thread import Thread
from neurocache.models.user import User as UserModel
from neurocache.schemas.agent_type import AgentType
from neurocache.services.title_generator import generate_thread_title
from neurocache.utils.message_serialization import extract_latest_user_text, prepare_messages_for_storage

logger = logging.getLogger(__name__)

chat_router = APIRouter(prefix="/chat", tags=["chat"])


def _extract_web_sources(content: Any) -> list[dict[str, str]]:
    """Extract web source URLs from web search tool return content.

    Content shape: {"status": "completed", "sources": [{"type": "url", "url": "..."}]}
    Some returns have no sources (just {"status": "completed"}).
    """
    sources: list[dict[str, str]] = []
    if isinstance(content, dict):
        for item in content.get("sources", []):
            if isinstance(item, dict) and "url" in item:
                source: dict[str, str] = {"url": item["url"]}
                if "title" in item:
                    source["title"] = item["title"]
                sources.append(source)
    return sources


@chat_router.post("/stream")
async def stream_chat(
    request: Request,
    db: AsyncPostgresSessionDep,
    user_id: AuthenticatedUser,
) -> Response:
    """Chat agent streaming endpoint.

    Uses VercelAIAdapter to handle parsing, agent execution, and streaming
    in Vercel AI SDK protocol format.
    """
    # Pre-parse body to extract thread_id and user text for on_complete
    body = await request.body()
    run_input = VercelAIAdapter.build_run_input(body)
    thread_id = run_input.id

    # Setup deps
    user = await UserModel.get(db, user_id)
    user_query = extract_latest_user_text(run_input.messages)

    openai_client = get_openai_client()
    deps = AgentDeps(user=user, db=db, openai_client=openai_client)

    async def on_complete(result):  # type: ignore[no-untyped-def]
        # Extract web search sources from builtin tool return parts
        web_sources: list[dict[str, str]] = []
        for msg in result.all_messages():
            if isinstance(msg, ModelResponse):
                for part in msg.parts:
                    if isinstance(part, BuiltinToolReturnPart) and part.tool_name == "web_search":
                        web_sources.extend(_extract_web_sources(part.content))

        # Save the full conversation: all_messages() includes the adapter's
        # converted history + new response. save_history is append-only (counts
        # existing DB rows, inserts only messages at indexes beyond that).
        all_msgs = prepare_messages_for_storage(result.all_messages(), deps.rag_sources, web_sources)
        await Thread.get_or_create(db, thread_id, AgentType.CHAT.value, user_id)
        await Message.save_history(db, thread_id, AgentType.CHAT.value, all_msgs)

        thread = await Thread.get(db, thread_id, AgentType.CHAT.value)
        if thread:
            thread.updated_at = datetime.now(timezone.utc)
            await db.flush()

        if thread and thread.title is None and result.output:
            asyncio.create_task(
                generate_thread_title(
                    thread_id=thread_id,
                    agent_type=AgentType.CHAT.value,
                    user_message=user_query,
                    assistant_response=str(result.output),
                )
            )

    return await VercelAIAdapter.dispatch_request(
        request,
        agent=chat_agent,
        deps=deps,
        on_complete=on_complete,
        sdk_version=6,
        model_settings=OpenAIResponsesModelSettings(
            openai_include_web_search_sources=True,
        ),
    )
