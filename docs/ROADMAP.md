# Neurocache Roadmap

A personal "second brain" AI chat application. This roadmap focuses on what matters for a local, experimental app.

## Current State

**Working:**

- **Chat**: Streaming responses, message persistence, thread management, auto-generated titles
- **Personalization**: User-specific context (custom instructions, occupation, about) injected into system prompt
- **RAG / Knowledge Base**: Document ingestion from Obsidian vaults, markdown-aware chunking, semantic search via pgvector, agentic retrieval via tool use

  - Batch ingestion of all markdown files from a knowledge source
  - Sync lifecycle with manual re-sync UI and status tracking
  - Change detection during sync (re-index modified files, clean up deleted files)
  - Agent-driven `search_knowledge_base` tool — agent decides when to search, can refine queries, and search multiple times per turn

- **Book Import**: PDF upload with drag-and-drop UI, chapter-aware chunking, and AI-powered analysis

  - Two-phase upload flow: preview PDF metadata, then confirm with editable title/author
  - Background ingestion: PDF text extraction, chunking by chapter boundaries, embedding generation
  - Book analysis agent: generates tags, summary, and key concepts breakdown into Notes.md using structured LLM output
  - Book list UI with document status badges and polling during ingestion

**Next Up:** MCP server, enhanced retrieval (hybrid search, cross-reference discovery, citations)

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

---

## Phase 3: Enhanced Retrieval

Build on RAG foundation for richer knowledge interactions.

### Cross-Reference Discovery

Surface connections across notes during conversation.

- "Related notes" suggestions based on conversation context
- Concept linking across different sources
- Leverage Obsidian's `[[wiki-links]]` for explicit connections

### Citation Display

- Inline citations linking to source notes
- Expandable previews of source content
- Click-to-open in Obsidian (obsidian:// URI scheme)

### Advanced Retrieval

- Hybrid search (keyword + semantic)
- Re-ranking retrieved results
- Query expansion/reformulation

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

### Data Export

Conversation and knowledge base export. Low priority for personal use.

---

## Notes

- Obsidian is the primary knowledge source. Keep the ingestion pipeline simple.
- This is a learning project. Optimize for understanding patterns, not production robustness.
- Incremental progress: each item should be completable in a reasonable work session.
