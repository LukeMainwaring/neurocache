"""Knowledge base capability bundling RAG search tools."""

from dataclasses import dataclass

from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.toolsets.function import FunctionToolset

from neurocache.agents.deps import AgentDeps
from neurocache.agents.tools.knowledge_base_tools import search_knowledge_base


@dataclass
class KnowledgeBaseCapability(AbstractCapability[AgentDeps]):
    """RAG search over the user's personal knowledge base."""

    def get_toolset(self) -> FunctionToolset[AgentDeps]:
        ts: FunctionToolset[AgentDeps] = FunctionToolset()
        ts.tool(search_knowledge_base)
        return ts
