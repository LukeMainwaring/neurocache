# Neurocache: Future Feature Brainstorm

## The Strategic Question

Claude Desktop and ChatGPT now have memory, file upload, MCP, and web search. What makes Neurocache worth building?

**Your moat is depth of integration with YOUR knowledge.** Commercial tools give everyone the same shallow memory. Neurocache can offer: your entire vault as always-on context, structured retrieval with provenance, agent tool use against your data, a portable knowledge API, and custom retrieval logic tuned to your content. Every feature below is evaluated against this.

---

## Quick Wins (1-2 sessions each)

### ~~1. Agentic RAG via Tool Use~~ DONE

**The architectural unlock.** Converted pre-fetch RAG into a `search_knowledge_base` Pydantic AI tool the agent invokes on demand. The agent decides WHEN to search, can refine queries, and can search multiple times per turn. Shared `AgentDeps` dataclass accumulates RAG source metadata across tool calls for storage/frontend display.

- **Files changed**: `agents/deps.py` (new), `agents/tools/knowledge_base_tools.py` (new), `agents/chat_agent.py`, `routers/chat_agent.py`, `utils/message_serialization.py`
- **Learned**: Pydantic AI tool registration, function-calling, agent autonomy, `RunContext` deps pattern
- **Prerequisite for**: web search, write-back, MCP tools, cross-reference discovery

### ~~2. Web Search Tool~~ DONE

Added Pydantic AI's built-in `WebSearchTool` via `OpenAIResponsesModel`. The agent blends personal notes with live web results in the same turn. Web sources are extracted, persisted, and displayed in a frontend dialog.

- **Files changed**: `agents/chat_agent.py`, `routers/chat_agent.py`, `utils/message_serialization.py`, `frontend/components/web-sources-dialog.tsx`
- **Learned**: Multi-tool agents, `OpenAIResponsesModel` vs `OpenAIChatModel`, builtin tool return parsing, Vercel AI SDK v6 transport

### 3. Obsidian Deep Links in Sources

Make the "View Sources" dialog link directly to notes via `obsidian://open?vault=...&file=...`. The vault name is already in config. Turns source attribution from decorative to actionable.

- **Files**: `frontend/components/rag-sources-dialog.tsx`
- **Learning**: Low (string formatting), but high UX payoff

---

## Medium Effort (3-5 sessions each)

### 4. Expose Neurocache as an MCP Server

**The flagship differentiator.** Mount a FastMCP server exposing `search_knowledge_base(query)`, `get_note(path)`, `list_recent_notes()`. Your second brain becomes queryable from Claude Code, Cursor, or any MCP client. You already have the retrieval logic -- this wraps it in MCP protocol.

- **Learning**: VERY HIGH -- MCP server protocol, tool interface design, the protocol shaping the AI ecosystem
- **Moat**: HIGHEST -- your knowledge base stops being locked in one chat UI

### 5. Hybrid Search (Keyword + Semantic)

Add PostgreSQL full-text search (`tsvector` + GIN index) alongside pgvector. Combine BM25-style keyword matching with embedding similarity. Embeddings miss exact names, titles, and technical terms -- keyword search catches them.

- **Files**: `services/knowledge_source/retrieval.py`, new migration for `tsvector` column
- **Learning**: HIGH -- information retrieval fundamentals, PostgreSQL full-text search
- **Moat**: HIGH -- better retrieval IS the core value proposition

### 6. Note Write-Back to Obsidian

Let the agent create/append notes in your vault. Capture conversation insights, create summaries, append to daily notes. Agent tools: `create_note(path, content)`, `append_to_note(path, content)`.

- **Requires**: Changing docker-compose vault mount from `:ro` to read-write, confirmation UX
- **Learning**: HIGH -- file system tools, agent autonomy, safety guardrails
- **Moat**: HIGH -- a brain that reads AND writes creates a growth loop

### 7. Cross-Reference Discovery

Parse Obsidian `[[wiki-links]]` during ingestion, store as edges in a relationship table. When the agent retrieves note A, also surface linked notes. Combine with embedding proximity for "related notes" that span explicit links AND semantic similarity.

- **Files**: `services/knowledge_source/ingestion.py`, new `NoteLink` model
- **Learning**: Graph relationships, link parsing, multi-hop retrieval
- **Moat**: HIGH -- this IS the "draw connections across concepts" vision from README
- **Bonus**: Naturally enhanced by agentic RAG -- an agent that can search iteratively discovers connections on its own

---

## Ambitious / Innovative

### 8. Conversation-to-Knowledge Pipeline

After each conversation, extract key facts, decisions, and insights. Propose them as new Obsidian notes or additions to existing notes. Your conversations feed back into your knowledge base -- a genuine growth loop where using the app makes it smarter.

- **Learning**: Extraction pipelines, structured output from LLMs, knowledge graph patterns
- **Moat**: VERY HIGH -- no commercial tool does this well

### 9. User-Configurable MCP Client (Plugin System)

Use Pydantic AI's `MCPServerHTTP`/`MCPServerStdio` + `load_mcp_servers()` to let users plug in external MCP servers from a settings UI. The agent automatically gains access to whatever tools are configured -- GitHub, Calendar, code execution, etc. This is effectively a plugin system for free.

- **Learning**: VERY HIGH -- MCP client protocol, dynamic tool loading, tool discovery
- **Moat**: HIGH -- turns Neurocache into an extensible platform, not just a chat app

### 10. Temporal Knowledge Tracking

Track how your thinking evolves over time. When did you first encounter an idea? How has your understanding of a topic changed across notes? Surface this in conversations: "You first wrote about X in March 2024, and your thinking shifted in this direction by November..."

- **Implementation**: Store ingestion timestamps per chunk, track note modification history, build timeline queries
- **Learning**: VERY HIGH -- temporal data modeling, versioning, novel retrieval patterns
- **Moat**: VERY HIGH -- no tool does this. This is genuinely unique.

### 11. Knowledge Gap Detection

Analyze your vault to find topics you reference frequently but haven't deeply explored. "You mention 'reinforcement learning' in 8 notes but have no dedicated study material on it." Proactively suggest areas to deepen.

- **Implementation**: Topic extraction from chunks, reference counting, gap analysis
- **Learning**: HIGH -- topic modeling, analytical pipelines
- **Moat**: HIGH -- turns passive retrieval into active learning guidance

### 12. "Think With Me" Mode

Instead of just answering, the agent walks through your existing notes step-by-step, showing its reasoning chain through your knowledge. "Based on your notes on X... and connecting to what you wrote about Y... here's a synthesis." Makes the retrieval chain visible and interactive.

- **Implementation**: Structured agent output with explicit source-reasoning steps, custom UI for chain-of-thought display
- **Learning**: HIGH -- structured output, agent reasoning transparency, novel UX
- **Moat**: HIGH -- commercial tools hide their reasoning; this makes your knowledge graph visible

### 13. Multi-Agent Architecture

Different agents for different tasks: research agent (deep multi-query search), daily review agent (surfaces notes you haven't revisited), writing assistant (helps draft from your notes). Uses Pydantic AI's multi-agent delegation.

- **Learning**: VERY HIGH -- agent orchestration, delegation patterns
- **Moat**: MEDIUM -- interesting architecture but the single agent covers most use cases today. Defer unless a specific use case demands it.

---

## Suggested Build Order

```
#1 Agentic RAG ✅ ──→ #2 Web Search ✅ ──→ #4 MCP Server
     (done)              (done)             (differentiator)
                                                 │
                                                 └──→ #5 Hybrid Search  OR  #6 Write-Back
                                                      (retrieval depth)     (growth loop)
                                                              │
                                                              └──→ #8 Conversation-to-Knowledge Pipeline
                                                                   (the full loop: read → chat → write → read)
```

**Priority 1**: ~~Agentic RAG (#1)~~ DONE
**Priority 2**: ~~Web Search (#2)~~ DONE
**Priority 3**: MCP Server (#4) -- biggest differentiator vs. Claude Desktop.
**Priority 4**: Hybrid Search (#5) or Write-Back (#6) -- pick based on curiosity (IR fundamentals vs. agent autonomy).
**Stretch**: Temporal tracking (#10) and knowledge gaps (#11) are the most unique ideas with no commercial equivalent.

## What NOT to Build (Yet)

- **Real auth** -- you're the only user
- **Document management UI** -- that's what Obsidian is for
- **Model selector** -- nice-to-have that doesn't widen the moat
- **Deployment/CI** -- premature until you decide to share it
- **Multi-agent** -- defer until a specific use case demands it
