# Neurocache Roadmap

A personal "second brain" AI chat application. This roadmap focuses on what matters for a local, experimental app.

## Current State

- **Working**: Chat with streaming, message persistence, thread management, auto-generated thread titles, user personalization settings
- **Missing**: RAG/knowledge base (the core feature)

---

## Completed

### Phase 1: User Personalization (Done)

Made the chat agent more helpful by incorporating user-specific context into every conversation.

- Improved system prompt in `chat_agent.py` structured to incorporate personalization data
- User model extended with personalization fields (custom_instructions, nickname, occupation, about_you)
- Backend API endpoints for get/update personalization settings
- Frontend settings page with form to edit personalization fields
- Personalization data injected into system prompt at chat time

### Phase 2: Obsidian Integration (RAG)

- Add pgvector extension to PostgreSQL

---

## Next Up

### Phase 2: Obsidian Integration (RAG)

**This is the core differentiating feature.** Connect to a local Obsidian vault as the knowledge base. This phase transforms Neurocache from a personalized chatbot into a true "second brain" that can reference your accumulated knowledge.

**Why this is the priority:**

- Directly enables the core vision: "Reference a knowledge base tailored to me"
- High learning value: teaches RAG patterns, vector embeddings, semantic search
- High user value: makes the app fundamentally more useful than ChatGPT/Claude

### 2.1 PostgreSQL + pgvector Setup

Foundation for storing and searching embeddings.

- Create SQLAlchemy model for document chunks with vector column
- Test basic similarity search queries

### 2.2 Obsidian Vault Ingestion

Read and process markdown files from a local vault.

- Configure vault path via environment variable
- Parse markdown files, extract content and metadata (title, tags, links)
- Chunk documents intelligently (respect headers, paragraphs)
- Generate embeddings using OpenAI's embedding API
- Store chunks with embeddings and source metadata

### 2.3 RAG in Chat

Integrate retrieval into the chat flow.

- Semantic search over note chunks before LLM call
- Include relevant context in system prompt (with token budget)
- Show source attribution in responses (which notes were used)
- Add "Sources" display in frontend chat UI

### 2.4 Sync and Refresh

Keep the knowledge base current.

- Manual re-sync endpoint/button
- Track file modification times to detect changes
- Incremental updates (only re-embed changed files)

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

### Retrieval Tuning

- Experiment with chunk sizes and overlap
- Hybrid search (keyword + semantic)
- Re-ranking retrieved results

---

## Deferred Features

Features documented here to avoid re-adding them prematurely. These make sense for a production app but are unnecessary overhead for local experimentation.

### Authentication

Currently uses a hardcoded demo user. Real auth (OAuth, email/password) only matters if the app becomes multi-user or deployed.

### Error Handling and Resilience

Basic error handling exists. Retry logic, rate limiting, and graceful degradation are production concerns.

### Document Management UI

A frontend for browsing/managing the knowledge base. For now, just use Obsidian directly.

### Book Import

EPUB/PDF ingestion with chapter-aware chunking. Future enhancement once Obsidian integration is solid.

### Web Content Ingestion

URL scraping and web content capture. Can add later if needed.

### Multi-User Support

User isolation, usage tracking, admin dashboard. Only relevant for productionization.

### Deployment Infrastructure

CI/CD, monitoring, production deployment. Handle when/if the app goes public.

### Data Export

Conversation and knowledge base export. Low priority for personal use.

---

## Notes

- Obsidian is the primary knowledge source. Keep the ingestion pipeline simple.
- This is a learning project. Optimize for understanding patterns, not production robustness.
- Incremental progress: each item should be completable in a reasonable work session.
- Phase 2 is broken into sub-milestones (2.1, 2.2, 2.3, 2.4) to allow incremental progress.
