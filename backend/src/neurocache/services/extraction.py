import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from openai import AsyncOpenAI
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from neurocache.agents.extraction_agent import extraction_agent
from neurocache.agents.tools.knowledge_base_tools import build_obsidian_url
from neurocache.models.document import Document
from neurocache.models.extraction import Extraction
from neurocache.models.knowledge_source import KnowledgeSource
from neurocache.models.message import Message
from neurocache.schemas.extraction import (
    ExtractionOutput,
    ExtractionPreview,
    ExtractionResponse,
    ExtractionStatusResponse,
    ExtractionSummary,
)
from neurocache.services.knowledge_source.ingestion import VAULT_MOUNT_PATH, ingest_document
from neurocache.utils.message_serialization import deserialize_messages

logger = logging.getLogger(__name__)

INSIGHTS_DIR = "Neurocache Insights"


def _format_conversation(raw_messages: list[dict[str, Any]]) -> str:
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
    sources = await KnowledgeSource.list_for_user(db, user_id)
    if not sources:
        return []

    source_ids = [s.id for s in sources]
    result = await db.execute(
        select(Document.title, Document.relative_path).where(Document.knowledge_source_id.in_(source_ids))
    )
    rows = result.all()

    titles: list[str] = []
    for title, relative_path in rows:
        if title:
            titles.append(title)
        else:
            name = Path(relative_path).stem
            if name:
                titles.append(name)

    return titles


def _compose_obsidian_markdown(output: ExtractionOutput, thread_id: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    tags_yaml = "\n".join(f"  - {tag}" for tag in output.tags)
    frontmatter = f"""---
type: chat_insight
source_thread: {thread_id}
created: {today}
tags:
{tags_yaml}
---"""

    sections: list[str] = [frontmatter, f"# {output.title}", output.summary]

    for insight in output.insights:
        sections.append(f"## {insight.heading}")
        sections.append(insight.body)

    if output.wiki_links:
        links = "\n".join(f"- [[{link}]]" for link in output.wiki_links)
        sections.append(f"## Related\n\n{links}")

    return "\n\n".join(sections) + "\n"


def _sanitize_filename(title: str) -> str:
    # Strip control characters and null bytes
    sanitized = re.sub(r"[\x00-\x1f\x7f]", "", title)
    # Replace characters invalid in filenames
    sanitized = re.sub(r'[<>:"/\\|?*]', "-", sanitized)
    # Collapse multiple dashes/spaces
    sanitized = re.sub(r"-{2,}", "-", sanitized)
    sanitized = sanitized.strip(" -.")
    # Limit length
    if len(sanitized) > 80:
        sanitized = sanitized[:80].rsplit(" ", 1)[0].rstrip(" -.")
    return sanitized or "Untitled Insight"


def _resolve_filename(title: str, vault_path: str = VAULT_MOUNT_PATH) -> tuple[str, Path]:
    """Returns (relative_path, absolute_path) with filename collision handling."""
    vault = Path(vault_path)
    expected_parent = (vault / INSIGHTS_DIR).resolve()
    base_name = _sanitize_filename(title)

    def _check_and_return(rel: str) -> tuple[str, Path] | None:
        abs_path = vault / rel
        # Path traversal guard — ensure resolved path stays within insights dir
        if abs_path.resolve().parent != expected_parent:
            msg = f"Filename resolves outside vault: {title}"
            raise ValueError(msg)
        if not abs_path.exists():
            return rel, abs_path
        return None

    # Try base name first
    result = _check_and_return(f"{INSIGHTS_DIR}/{base_name}.md")
    if result:
        return result

    # Append incrementing suffix on collision
    counter = 2
    while True:
        result = _check_and_return(f"{INSIGHTS_DIR}/{base_name}-{counter}.md")
        if result:
            return result
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
    raw_messages = await Message.get_history(db, thread_id, agent_type)
    if not raw_messages:
        raise HTTPException(status_code=404, detail="No messages found for this thread")

    conversation_text = _format_conversation(raw_messages)

    note_titles = await _get_existing_note_titles(db, user_id)
    titles_context = "\n".join(f"- {t}" for t in note_titles[:200]) if note_titles else "(no existing notes)"

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


async def write_and_ingest_note(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
    knowledge_source_id: uuid.UUID,
    title: str,
    content: str,
    vault_path: str = VAULT_MOUNT_PATH,
) -> tuple[str, str]:
    """Write a markdown note to the vault and ingest it. Cleans up the file if ingestion fails."""
    # Ensure insights directory exists
    insights_dir = Path(vault_path) / INSIGHTS_DIR
    insights_dir.mkdir(parents=True, exist_ok=True)

    # Resolve unique filename
    relative_path, absolute_path = _resolve_filename(title, vault_path)

    # Write file to vault
    absolute_path.write_text(content, encoding="utf-8")
    logger.info(f"Wrote note to {relative_path}")

    try:
        await ingest_document(db, openai_client, knowledge_source_id, relative_path, vault_path=vault_path)
    except Exception:
        absolute_path.unlink(missing_ok=True)
        logger.exception(f"Failed to ingest note {relative_path}, cleaned up file")
        raise

    obsidian_url = build_obsidian_url(relative_path)
    return relative_path, obsidian_url


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
    relative_path, obsidian_url = await write_and_ingest_note(db, openai_client, knowledge_source_id, title, content)

    # Look up the document that was just ingested for the provenance record
    doc = await Document.get_by_relative_path(db, knowledge_source_id, relative_path)
    if not doc:
        msg = f"Document not found after ingestion: {relative_path}"
        raise RuntimeError(msg)

    extraction = await Extraction.create(
        db,
        thread_id=thread_id,
        agent_type=agent_type,
        knowledge_source_id=knowledge_source_id,
        document_id=doc.id,
    )

    return ExtractionResponse(
        extraction_id=extraction.id,
        relative_path=relative_path,
        obsidian_url=obsidian_url,
    )


def compose_insight_markdown(title: str, content: str, tags: list[str] | None = None) -> str:
    """Compose an Obsidian markdown note with chat_insight frontmatter.

    Used by the MCP save_to_knowledge_base tool where the client LLM
    provides the content directly (no extraction agent needed).
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tags = tags or []

    tags_yaml = "\n".join(f"  - {tag}" for tag in tags) if tags else ""
    tag_block = f"\ntags:\n{tags_yaml}" if tags_yaml else ""

    return f"""---
type: chat_insight
created: {today}{tag_block}
---

# {title}

{content}
"""


async def get_extraction_status(
    db: AsyncSession,
    thread_id: str,
    agent_type: str,
) -> ExtractionStatusResponse:
    rows = await Extraction.get_by_thread_with_paths(db, thread_id, agent_type)

    summaries = [
        ExtractionSummary(
            id=ext.id,
            document_id=ext.document_id,
            relative_path=relative_path,
            created_at=ext.created_at,
        )
        for ext, relative_path in rows
    ]

    return ExtractionStatusResponse(extractions=summaries)


async def get_user_knowledge_source_id(db: AsyncSession, user_id: str) -> uuid.UUID:
    sources = await KnowledgeSource.list_for_user(db, user_id)
    if not sources:
        raise HTTPException(
            status_code=400,
            detail="No knowledge source configured. Add one in Settings.",
        )
    return sources[0].id
