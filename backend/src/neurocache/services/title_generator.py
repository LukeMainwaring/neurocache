"""Title generation service for chat threads."""

import logging

from openai import AsyncOpenAI

from neurocache.dependencies.db import get_async_sqlalchemy_session
from neurocache.models.thread import Thread

logger = logging.getLogger(__name__)

TITLE_MODEL = "gpt-5-mini"

TITLE_PROMPT = (
    "Generate a short, descriptive title (3-6 words) for this conversation. "
    "Return ONLY the title text, no quotes or punctuation at the end.\n\n"
    "User: {user_message}\n\n"
    "Assistant: {assistant_response}"
)

MAX_FALLBACK_LENGTH = 40


def _create_fallback_title(user_message: str) -> str:
    """Create a fallback title from the user message when LLM fails."""
    title = user_message.strip()
    if len(title) <= MAX_FALLBACK_LENGTH:
        return title
    truncated = title[:MAX_FALLBACK_LENGTH].rsplit(" ", 1)[0]
    return f"{truncated}..."


async def generate_thread_title(
    thread_id: str,
    agent_type: str,
    user_message: str,
    assistant_response: str,
) -> None:
    """Background task to generate and save thread title.

    Creates its own database session since this runs independently
    of the original request context.
    """
    try:
        client = AsyncOpenAI()
        prompt = TITLE_PROMPT.format(
            user_message=user_message[:500],
            assistant_response=assistant_response[:500],
        )
        response = await client.chat.completions.create(
            model=TITLE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=20,
            temperature=0.3,
        )

        title = response.choices[0].message.content
        if title:
            title = title.strip().strip('"').strip("'")
            async with get_async_sqlalchemy_session() as db:
                await Thread.update_title(db, thread_id, agent_type, title)
                await db.commit()
            logger.info(f"Generated title for thread {thread_id}: {title}")

    except Exception:
        logger.exception(f"Failed to generate title for thread {thread_id}")
        fallback = _create_fallback_title(user_message)
        try:
            async with get_async_sqlalchemy_session() as db:
                await Thread.update_title(db, thread_id, agent_type, fallback)
                await db.commit()
            logger.info(f"Used fallback title for thread {thread_id}: {fallback}")
        except Exception:
            logger.exception(f"Failed to save fallback title for thread {thread_id}")
