"""Chat agent for general conversational interaction with knowledge base.

This module provides a simple chat agent that:
- Engages in natural conversation with the user
- Has access to the user's personal knowledge base via a tool
- Maintains conversation history across sessions
"""

import logging

import logfire
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel

from neurocache.agents.deps import AgentDeps
from neurocache.agents.tools.knowledge_base_tools import register_knowledge_base_tools
from neurocache.core.config import get_settings

logfire.configure()
logfire.instrument_pydantic_ai()

logger = logging.getLogger(__name__)

config = get_settings()

# ============================================================================
# Chat Agent System Prompt
# ============================================================================

SYSTEM_PROMPT = """You are the user's personal AI assistant and "second brain"—an extension of their thinking that understands their context, interests, and goals.

Your core traits:
- Thoughtful: Consider the user's background and perspective when responding
- Connective: Draw links between ideas, even across different domains
- Direct: Be concise and honest. Say "I don't know" when appropriate
- Adaptive: Match your tone and depth to what the user needs

When helping the user:
- Build on what you know about them rather than treating each conversation as isolated
- Proactively surface relevant connections when they might be useful
- Ask clarifying questions when the user's intent is ambiguous

## Knowledge Base
You have access to the user's personal knowledge base via the search_knowledge_base tool. Use it when:
- The user asks about topics they may have notes on
- You need to reference their reading, research, or personal writing
- Drawing connections across their knowledge would be valuable

Do NOT search for every message. Skip searches for:
- Casual conversation, greetings, or small talk
- Follow-up questions about content already in the conversation
- Requests that clearly don't relate to the user's knowledge base

When you find relevant results, naturally weave insights from the knowledge base into your response. Reference specific sources when helpful.""".strip()

# ============================================================================
# Agent Creation and Instructions
# ============================================================================


def build_chat_instructions(ctx: RunContext[AgentDeps]) -> str:
    """Build instructions for the chat agent.

    Args:
        ctx: Pydantic AI RunContext containing AgentDeps

    Returns:
        Complete chat instructions with user context
    """
    user = ctx.deps.user

    sections = [SYSTEM_PROMPT]

    # User context section
    user_context = []
    name = user.nickname or user.name
    if name:
        user_context.append(f"You're chatting with {name}.")
    if user.occupation:
        user_context.append(f"They work as a {user.occupation}.")
    if user.about_you:
        user_context.append(f"Background: {user.about_you}")

    if user_context:
        sections.append("## About the User\n" + "\n".join(user_context))

    # Custom instructions get their own prominent section with explicit priority
    if user.custom_instructions:
        sections.append(
            "## User's Custom Instructions\n"
            "Follow these instructions from the user. "
            "They take priority over default behavior:\n\n"
            f"{user.custom_instructions}"
        )

    return "\n\n".join(sections)


_model = OpenAIChatModel(model_name=config.AGENT_MODEL)

chat_agent = Agent(
    model=_model,
    deps_type=AgentDeps,
    instructions=build_chat_instructions,
)

register_knowledge_base_tools(chat_agent)
