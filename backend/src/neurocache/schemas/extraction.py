"""Pydantic schemas for conversation-to-knowledge extraction."""

import uuid
from datetime import datetime

from pydantic import Field

from neurocache.schemas.base import BaseSchema

# --- Agent structured output ---


class InsightSection(BaseSchema):
    """A single insight section within the extracted note."""

    heading: str = Field(description="Section heading (concise, descriptive)")
    body: str = Field(description="Markdown body for this section")


class ExtractionOutput(BaseSchema):
    """Structured output from the extraction agent."""

    title: str = Field(description="Concise, descriptive title for the note (3-8 words)")
    summary: str = Field(description="2-3 sentence summary of key takeaways from the conversation")
    insights: list[InsightSection] = Field(
        description="Organized insight sections. Empty list if no extractable insights."
    )
    tags: list[str] = Field(description="5-10 Obsidian tags, lowercase-hyphenated (e.g., 'machine-learning')")
    wiki_links: list[str] = Field(
        description="Names of existing notes to link to (without [[ ]] brackets). Only use names from the provided list."
    )


# --- API schemas ---


class ExtractionPreviewRequest(BaseSchema):
    """Request to generate an extraction preview from a conversation."""

    thread_id: str = Field(description="Thread ID to extract insights from")


class ExtractionPreview(BaseSchema):
    """LLM-generated preview for user review before saving."""

    thread_id: str
    title: str = Field(description="Suggested note title")
    content: str = Field(description="Full Obsidian markdown (with frontmatter)")
    tags: list[str] = Field(description="Suggested Obsidian tags")
    wiki_links: list[str] = Field(description="Suggested [[links]] to existing notes")


class ExtractionConfirmRequest(BaseSchema):
    """User-edited content to save to the vault."""

    thread_id: str
    title: str = Field(description="Note title (may be edited by user)")
    content: str = Field(description="Full markdown content (may be edited by user)")


class ExtractionResponse(BaseSchema):
    """Result after saving an extraction to the vault."""

    extraction_id: uuid.UUID
    relative_path: str = Field(description="Path relative to vault root")
    obsidian_url: str = Field(description="Deep link to open in Obsidian")


class ExtractionSummary(BaseSchema):
    """Summary of a previous extraction for status checking."""

    id: uuid.UUID
    document_id: uuid.UUID
    relative_path: str = Field(description="Path of the created note")
    created_at: datetime


class ExtractionStatusResponse(BaseSchema):
    """Response for checking extraction status of a thread."""

    extractions: list[ExtractionSummary]
