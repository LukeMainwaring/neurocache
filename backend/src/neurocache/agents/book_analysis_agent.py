"""Book analysis agent for generating tags, summary, and key concepts from PDFs.

Uses Pydantic AI structured output to produce a BookAnalysis from condensed book content.
"""

import logging

from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel

from neurocache.core.config import get_settings
from neurocache.schemas.knowledge_source.book_analysis import BookAnalysis

logger = logging.getLogger(__name__)

config = get_settings()

SYSTEM_PROMPT = """You are a book analyst. Given content extracted from a book (table of contents, \
full text or sampled pages), produce a thorough structured analysis.

Your output must include:

1. **Tags**: 5-10 topical keywords that capture the book's main themes and subject domains. \
Use lowercase, hyphenated phrases (e.g., "machine-learning", "distributed-systems", "cognitive-psychology").

2. **Summary**: Write exactly 3 substantial paragraphs. \
Paragraph 1: What the book is about — its subject, scope, and central thesis. \
Paragraph 2: How the book approaches the topic — its structure, methodology, and what makes it distinctive. \
Paragraph 3: Who would benefit from reading it and what they will take away.

3. **Key Concepts**: A detailed breakdown of the most important ideas. \
IMPORTANT: Create one entry per individual chapter, NOT grouped by part or section. \
Use the exact chapter title from the table of contents as each heading. \
For each chapter, provide 4-8 key concept descriptions (2-3 sentences each) that capture the \
core ideas, arguments, and takeaways — not just topic names. Be specific and substantive.

If no table of contents is available, organize by the major themes you identify, \
but still aim for granular chapter-level groupings rather than broad categories."""

_model = OpenAIChatModel(
    model_name=config.BOOK_ANALYSIS_MODEL,
    settings=ModelSettings(temperature=config.BOOK_ANALYSIS_TEMPERATURE),
)

book_analysis_agent = Agent(
    model=_model,
    output_type=BookAnalysis,
    instructions=SYSTEM_PROMPT,
)
