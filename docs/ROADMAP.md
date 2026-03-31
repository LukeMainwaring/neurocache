# Neurocache Roadmap

A personal "second brain" AI chat application. This roadmap focuses on what matters for a local, experimental app.

**Strategic moat:** Neurocache's value over commercial tools (Claude Desktop, ChatGPT) is depth of integration with YOUR knowledge — your entire vault as always-on context, structured retrieval with provenance, agent tool use against your data, and a portable knowledge API via MCP. Every feature is evaluated against this.

## Current State

**Working:**

- **Chat**: Streaming responses, message persistence, thread management, auto-generated titles
- **Personalization**: User-specific context (custom instructions, occupation, about) injected into system prompt
- **RAG / Knowledge Base**: Document ingestion from Obsidian vaults, markdown-aware chunking, hybrid search (semantic + keyword) via pgvector and PostgreSQL full-text search with Reciprocal Rank Fusion, agentic retrieval via tool use

  - Batch ingestion of all markdown files from a knowledge source
  - Sync lifecycle with manual re-sync UI and status tracking
  - Change detection during sync (re-index modified files, clean up deleted files)
  - Agent-driven `search_knowledge_base` tool — agent decides when to search, can refine queries, and search multiple times per turn

- **Book Import**: PDF upload with drag-and-drop UI, chapter-aware chunking, and AI-powered analysis

  - Two-phase upload flow: preview PDF metadata, then confirm with editable title/author
  - Background ingestion: PDF text extraction, chunking by chapter boundaries, embedding generation
  - Book analysis agent: generates tags, summary, and key concepts breakdown into Notes.md using structured LLM output
  - Book list UI with document status badges and polling during ingestion

**Next Up:** Enhanced retrieval (cross-reference discovery), note write-back to Obsidian

### Phase 2.9: Authentication (Auth0)

Replaced hardcoded demo user with Auth0 JWT authentication. Backend verifies JWTs via JWKS, extracts user identity from the `sub` claim, and guards all routes. Frontend uses Auth0 SPA SDK with an activation flow for new users (first/last name entry). Axios interceptor attaches access tokens to all API requests.

---

## Completed

### Phase 1: User Personalization

User-specific context (custom instructions, nickname, occupation, about) stored in the User model and injected into the chat agent's system prompt. Settings page on the frontend for editing.

### Phase 2: RAG Vertical Slice

End-to-end RAG pipeline: pgvector storage with HNSW indexing, OpenAI embeddings, markdown-aware chunking that respects document structure, semantic retrieval integrated into the chat agent. Batch ingestion discovers all markdown files in an Obsidian vault, with sync lifecycle management and change detection (mtime + content hash) to keep the index up to date.

### Phase 2.5: Agentic RAG via Tool Use

Converted RAG from a pre-fetch step into a Pydantic AI tool (`search_knowledge_base`) the agent invokes on demand. Introduced shared `AgentDeps` dataclass and `agents/tools/` module pattern. The agent now decides whether retrieval is needed, can reformulate queries, and can search multiple times per turn. This is the architectural prerequisite for web search, write-back, MCP tools, and other future agent capabilities.

### Phase 2.75: Book Import & Analysis

PDF book upload with drag-and-drop UI, two-phase preview/confirm flow, and background ingestion with chapter-aware chunking. A dedicated book analysis agent (`book_analysis_agent`) uses Pydantic AI structured output to generate tags, a high-level summary, and per-chapter key concepts from the full PDF text, writing the results into the book's Notes.md before ingestion so the analysis is embedded and searchable via RAG. Knowledge base settings page refactored into modular components.

### Phase 2.8: Web Search

Added Pydantic AI's built-in `WebSearchTool` to the chat agent via `OpenAIResponsesModel`. The agent can now blend personal knowledge base results with live web search in the same turn. Web search sources are extracted from tool return parts, persisted alongside RAG sources, and displayed in a "View Web Sources" dialog on the frontend.

### Phase 3.1: Hybrid Search

Added keyword search alongside existing semantic search using PostgreSQL full-text search (`tsvector`/`tsquery`) with a GIN index. Results from both methods are fused via Reciprocal Rank Fusion (RRF) with k=60. Each chunk's tsvector is a weighted composition of document metadata (title and author at weight A, tags/section headers/chapters at weight B) and chunk content (weight C), using `english` config for stemmed fields and `simple` for tags. Dual tsquery matching (english + simple) ensures both stemmed content and exact metadata terms are found. Search vectors are computed per-document during ingestion via a single SQL UPDATE join.

### Phase 3.2: MCP Server

Exposed the knowledge base as an MCP server using FastMCP (included via pydantic-ai). Three tools: `search_knowledge_base` (hybrid search with RRF), `get_document` (full document content by path), and `list_documents` (browse indexed documents). Dual transport: mounted on the FastAPI app at `/mcp` via streamable-http (runs automatically with Docker), and runnable standalone via `python -m neurocache.mcp` for stdio transport (Claude Desktop, Claude Code, Cursor). Lifespan pattern validates the configured user and shares the OpenAI client across tool calls. Graceful degradation if `NEUROCACHE_USER_ID` is not set.

### Phase 3.3: Inline Citations

Added numbered inline citations (`[1]`, `[2]`) to assistant responses when the agent references the knowledge base. Sources are numbered in the RAG context so the agent can cite them, with consecutive numbering across multiple searches in one turn. Frontend renders citations as interactive superscript badges via Streamdown's `allowedTags`/`components` overrides — hover shows a compact tooltip (source path, content type, match %), click opens a dialog with the full source content and metadata. RAG sources are now attached to both user messages (for the existing "View Sources" dialog) and assistant messages (for inline citation rendering). Citations degrade gracefully: plain superscripts during streaming, interactive after refetch; invalid citation numbers render as non-interactive text.

---

## Phase 3: Enhanced Retrieval

Build on RAG foundation for richer knowledge interactions.

### Cross-Reference Discovery

Surface connections across notes during conversation.

- "Related notes" suggestions based on conversation context
- Concept linking across different sources
- Leverage Obsidian's `[[wiki-links]]` for explicit connections

### Advanced Retrieval

- Re-ranking retrieved results
- Query expansion/reformulation

---

## Future Ideas

Ambitious features worth exploring once the core is mature. Ordered roughly by uniqueness and impact.

### Conversation-to-Knowledge Pipeline

After each conversation, extract key facts, decisions, and insights. Propose them as new Obsidian notes or additions to existing notes. The full loop: read → chat → write → read. This creates a genuine growth loop where using the app makes it smarter.

### Temporal Knowledge Tracking

Track how thinking evolves over time. Surface when you first encountered an idea and how your understanding shifted across notes. No commercial tool does this — genuinely unique.

### Knowledge Gap Detection

Analyze the vault for topics referenced frequently but never deeply explored. "You mention 'reinforcement learning' in 8 notes but have no dedicated material on it." Turns passive retrieval into active learning guidance.

### "Think With Me" Mode

Instead of just answering, the agent walks through existing notes step-by-step, showing its reasoning chain through your knowledge. Makes the retrieval chain visible and interactive — commercial tools hide this.

### User-Configurable MCP Client (Plugin System)

Let users plug in external MCP servers (GitHub, Calendar, code execution) from a settings UI. Uses Pydantic AI's `MCPServerHTTP`/`MCPServerStdio` + `load_mcp_servers()`. Turns Neurocache into an extensible platform.

### Obsidian Deep Links in Citations

Make inline citations link directly to notes via `obsidian://open?vault=...&file=...`. The vault name is already in config. Small effort, high UX payoff.

---

## Deferred Features

Features documented here to avoid re-adding them prematurely. These make sense for a production app but are unnecessary overhead for local experimentation.

### Error Handling and Resilience

Basic error handling exists. Retry logic, rate limiting, and graceful degradation are production concerns.

### Document Management UI

A frontend for browsing/managing the knowledge base. For now, just use Obsidian directly.

### Web Content Ingestion

URL scraping and web content capture. Can add later if needed.

### Multi-User Support

User isolation, usage tracking, admin dashboard. Only relevant for productionization.

### Deployment Infrastructure

CI/CD, monitoring, production deployment. Handle when/if the app goes public.


### Model Upgrades & Reasoning

Experiment with reasoning models and tune `ModelSettings` (e.g., `openai_reasoning_effort`) once the core chat and RAG flow is working well. Just a config change — no architectural work needed.

### Multi-Agent Architecture

Specialized agents for different tasks: research agent (deep multi-query search), daily review agent (surfaces unvisited notes), writing assistant (drafts from your notes). Defer unless a specific use case demands it — the single agent covers most cases today.

### Data Export

Conversation and knowledge base export. Low priority for personal use.

---

## Notes

- Obsidian is the primary knowledge source. Keep the ingestion pipeline simple.
- This is a learning project. Optimize for understanding patterns, not production robustness.
- Incremental progress: each item should be completable in a reasonable work session.
