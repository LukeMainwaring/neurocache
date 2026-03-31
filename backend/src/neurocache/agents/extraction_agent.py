"""Extraction agent for conversation-to-knowledge pipeline.

Uses Pydantic AI structured output to extract reusable knowledge from
conversations and produce Obsidian-native note content.
"""

import logging

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel

from neurocache.core.config import get_settings
from neurocache.schemas.extraction import ExtractionOutput

logger = logging.getLogger(__name__)

config = get_settings()

SYSTEM_PROMPT = """\
You are a knowledge extraction specialist. Given a conversation between a user and an AI assistant, \
identify and extract reusable knowledge — insights, decisions, mental models, facts learned, \
and connections discovered.

Your output must include:

1. **Title**: A concise, descriptive title (3-8 words) that captures the core topic or insight.

2. **Summary**: 2-3 sentences summarizing the key takeaways from the conversation.

3. **Insights**: Organized sections, each with a heading and markdown body. Focus on:
   - Concrete decisions made and their reasoning
   - New mental models or frameworks discussed
   - Facts or knowledge gained
   - Connections between ideas
   - Action items or next steps identified

   Each section should be self-contained and useful as a reference. Use Obsidian-native markdown: \
bullet points, bold, inline code where appropriate. Do NOT include # headers in the body \
(the heading field provides the section header).

4. **Tags**: 5-10 Obsidian tags, lowercase-hyphenated (e.g., "machine-learning", "system-design"). \
Tags should reflect the topics and domains discussed.

5. **Wiki Links**: Suggest links to existing notes from the provided list. Only use note names \
that appear in the provided list — do not invent note names. Link to notes that are directly \
relevant to the conversation content.

Guidelines:
- Skip small talk, greetings, and meta-conversation (e.g., "can you help me with...")
- Skip things that are common knowledge or trivially obvious
- If the conversation has no extractable insights (e.g., simple greetings, troubleshooting with no resolution), \
return an empty insights list
- Write in a neutral, reference-friendly tone — these notes should be useful months later
- Prefer specific, actionable content over vague summaries"""

_model = OpenAIChatModel(model_name=config.EXTRACTION_MODEL)

extraction_agent = Agent(
    model=_model,
    output_type=ExtractionOutput,
    instructions=SYSTEM_PROMPT,
)
