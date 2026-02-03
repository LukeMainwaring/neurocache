"""Pydantic schemas for PDF parsing."""

from pydantic import Field

from ..base import BaseSchema


class TOCEntry(BaseSchema):
    """A table of contents entry from a PDF."""

    level: int = Field(description="Nesting level (1 = top-level chapter)")
    title: str = Field(description="Chapter/section title")
    page: int = Field(description="1-indexed page number")


class PageContent(BaseSchema):
    """Extracted content from a single PDF page."""

    page_number: int = Field(description="1-indexed page number")
    text: str = Field(description="Extracted text content")
    chapter: str | None = Field(default=None, description="Chapter title if available from TOC")
