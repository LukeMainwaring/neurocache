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
full text or sampled pages), produce a structured analysis.

Your output must include:

1. **Tags**: 5-10 topical keywords that capture the book's main themes and subject domains. \
Use lowercase, hyphenated phrases (e.g., "machine-learning", "distributed-systems", "cognitive-psychology").

2. **Summary**: A 2-3 paragraph high-level summary covering what the book is about, its central \
thesis or approach, and who would benefit from reading it.

3. **Key Concepts**: A breakdown of the most important ideas, organized by chapter or thematic section. \
For each section, provide 4-8 key concept descriptions (1-2 sentences each) that capture the core ideas.

If the content includes a table of contents, organize key concepts by chapter headings. \
If no table of contents is available, organize by the major themes you identify.

Focus on substance over structure. Capture the actual ideas and arguments, not just topic names."""

_model = OpenAIChatModel(
    model_name=config.BOOK_ANALYSIS_MODEL,
    settings=ModelSettings(temperature=config.BOOK_ANALYSIS_TEMPERATURE),
)

book_analysis_agent = Agent(
    model=_model,
    output_type=BookAnalysis,
    instructions=SYSTEM_PROMPT,
)
