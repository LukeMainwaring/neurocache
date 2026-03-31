"""Extraction service for conversation-to-knowledge pipeline.

Provides preview (LLM extraction) and save (vault write + ingestion) operations.
"""

import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart
from sqlalchemy.ext.asyncio import AsyncSession

from neurocache.agents.extraction_agent import extraction_agent
from neurocache.agents.tools.knowledge_base_tools import build_obsidian_url
from neurocache.models.document import Document
from neurocache.models.extraction import Extraction
from neurocache.models.knowledge_source import KnowledgeSource
from neurocache.models.message import Message
from neurocache.schemas.extraction import ExtractionOutput, ExtractionPreview, ExtractionResponse
from neurocache.services.knowledge_source.ingestion import VAULT_MOUNT_PATH, ingest_document
from neurocache.utils.message_serialization import deserialize_messages

logger = logging.getLogger(__name__)

INSIGHTS_DIR = "Neurocache Insights"


def _format_conversation(raw_messages: list[dict[str, Any]]) -> str:
    """Format stored messages into readable conversation text for the extraction agent."""
    messages = deserialize_messages(raw_messages)

    parts: list[str] = []
    for msg in messages:
        if isinstance(msg, ModelRequest):
            for req_part in msg.parts:
                if isinstance(req_part, UserPromptPart):
                    text = req_part.content if isinstance(req_part.content, str) else str(req_part.content)
                    parts.append(f"User: {text}")
        elif isinstance(msg, ModelResponse):
            for resp_part in msg.parts:
                if isinstance(resp_part, TextPart):
                    parts.append(f"Assistant: {resp_part.content}")

    return "\n\n".join(parts)


async def _get_existing_note_titles(db: AsyncSession, user_id: str) -> list[str]:
    """Load document titles from the user's knowledge source for wiki-link suggestions."""
    sources = await KnowledgeSource.list_for_user(db, user_id)
    if not sources:
        return []

    titles: list[str] = []
    for source in sources:
        docs = await Document.get_all_by_source(db, source.id)
        for doc in docs:
            if doc.title:
                titles.append(doc.title)
            else:
                # Use filename without extension as fallback
                name = Path(doc.relative_path).stem
                if name:
                    titles.append(name)

    return titles


def _compose_obsidian_markdown(output: ExtractionOutput, thread_id: str) -> str:
    """Compose full Obsidian markdown note from extraction agent output."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Build YAML frontmatter
    tags_yaml = "\n".join(f"  - {tag}" for tag in output.tags)
    frontmatter = f"""---
type: chat_insight
source_thread: {thread_id}
created: {today}
tags:
{tags_yaml}
---"""

    # Build note body
    sections: list[str] = [frontmatter, f"# {output.title}", output.summary]

    for insight in output.insights:
        sections.append(f"## {insight.heading}")
        sections.append(insight.body)

    # Add related notes section with wiki-links
    if output.wiki_links:
        links = "\n".join(f"- [[{link}]]" for link in output.wiki_links)
        sections.append(f"## Related\n\n{links}")

    return "\n\n".join(sections) + "\n"


def _sanitize_filename(title: str) -> str:
    """Sanitize a title for use as a filename."""
    # Replace characters invalid in filenames
    sanitized = re.sub(r'[<>:"/\\|?*]', "-", title)
    # Collapse multiple dashes/spaces
    sanitized = re.sub(r"-{2,}", "-", sanitized)
    sanitized = sanitized.strip(" -.")
    # Limit length
    if len(sanitized) > 80:
        sanitized = sanitized[:80].rsplit(" ", 1)[0].rstrip(" -.")
    return sanitized or "Untitled Insight"


def _resolve_filename(title: str) -> tuple[str, Path]:
    """Resolve a unique filename in the insights directory.

    Returns (relative_path, absolute_path) with collision handling.
    """
    vault = Path(VAULT_MOUNT_PATH)
    base_name = _sanitize_filename(title)
    relative = f"{INSIGHTS_DIR}/{base_name}.md"
    absolute = vault / relative

    if not absolute.exists():
        return relative, absolute

    # Append incrementing suffix on collision
    counter = 2
    while True:
        relative = f"{INSIGHTS_DIR}/{base_name}-{counter}.md"
        absolute = vault / relative
        if not absolute.exists():
            return relative, absolute
        counter += 1


async def preview_extraction(
    db: AsyncSession,
    thread_id: str,
    agent_type: str,
    user_id: str,
) -> ExtractionPreview:
    """Generate an extraction preview from a conversation thread.

    Runs the extraction agent to analyze the conversation and produce
    structured insight content formatted as an Obsidian note.
    """
    # Load conversation
    raw_messages = await Message.get_history(db, thread_id, agent_type)
    if not raw_messages:
        msg = f"No messages found for thread {thread_id}"
        raise ValueError(msg)

    conversation_text = _format_conversation(raw_messages)

    # Load existing note titles for wiki-link suggestions
    note_titles = await _get_existing_note_titles(db, user_id)
    titles_context = "\n".join(f"- {t}" for t in note_titles[:200]) if note_titles else "(no existing notes)"

    # Build prompt with conversation + note titles context
    prompt = f"""Analyze this conversation and extract reusable knowledge:

---
{conversation_text}
---

Existing notes in the vault (for wiki-link suggestions):
{titles_context}"""

    result = await extraction_agent.run(prompt)
    output: ExtractionOutput = result.output

    # Compose full Obsidian markdown
    content = _compose_obsidian_markdown(output, thread_id)

    return ExtractionPreview(
        thread_id=thread_id,
        title=output.title,
        content=content,
        tags=output.tags,
        wiki_links=output.wiki_links,
    )


async def save_extraction(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
    knowledge_source_id: uuid.UUID,
    thread_id: str,
    agent_type: str,
    title: str,
    content: str,
) -> ExtractionResponse:
    """Save an extraction to the vault and ingest it.

    Writes the markdown file, runs the ingestion pipeline (chunk, embed, index),
    and creates an Extraction provenance record.
    """
    # Ensure insights directory exists
    insights_dir = Path(VAULT_MOUNT_PATH) / INSIGHTS_DIR
    insights_dir.mkdir(parents=True, exist_ok=True)

    # Resolve unique filename
    relative_path, absolute_path = _resolve_filename(title)

    # Write file to vault
    absolute_path.write_text(content, encoding="utf-8")
    logger.info(f"Wrote extraction note to {relative_path}")

    # Ingest via existing pipeline (chunk → embed → TSVECTOR)
    document = await ingest_document(db, openai_client, knowledge_source_id, relative_path)

    # Create provenance record
    extraction = await Extraction.create(
        db,
        thread_id=thread_id,
        agent_type=agent_type,
        knowledge_source_id=knowledge_source_id,
        document_id=document.id,
    )

    obsidian_url = build_obsidian_url(relative_path)

    return ExtractionResponse(
        extraction_id=extraction.id,
        relative_path=relative_path,
        obsidian_url=obsidian_url,
    )
