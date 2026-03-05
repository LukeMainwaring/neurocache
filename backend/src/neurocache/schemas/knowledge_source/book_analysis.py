"""Schemas for AI-powered book analysis."""

from pydantic import Field

from neurocache.schemas.base import BaseSchema


class KeyConcept(BaseSchema):
    """A group of key concepts under a chapter or thematic heading."""

    heading: str = Field(description="Chapter title or thematic heading")
    concepts: list[str] = Field(description="Key concept descriptions (1-2 sentences each)")


class BookAnalysis(BaseSchema):
    """Structured analysis output for a book."""

    tags: list[str] = Field(description="5-10 topical keyword tags, lowercase hyphenated")
    summary: str = Field(description="2-3 paragraph high-level summary")
    key_concepts: list[KeyConcept] = Field(description="Key concepts organized by chapter or theme")
