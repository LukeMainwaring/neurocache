# Neurocache Roadmap

A personal "second brain" AI chat application. This roadmap focuses on what matters for a local, experimental app.

## Current State

- **Working**: Chat with streaming, message persistence, thread management, auto-generated thread titles, user personalization settings, RAG vertical slice (single document ingestion, semantic search, context injection)
- **In Progress**: Experimenting with chunking strategies and similarity thresholds before full vault ingestion

---

## Completed

### Phase 1: User Personalization (Done)

Made the chat agent more helpful by incorporating user-specific context into every conversation.

- Improved system prompt in `chat_agent.py` structured to incorporate personalization data
- User model extended with personalization fields (custom_instructions, nickname, occupation, about_you)
- Backend API endpoints for get/update personalization settings
- Frontend settings page with form to edit personalization fields
- Personalization data injected into system prompt at chat time

### Phase 2: RAG Vertical Slice (Done)

Built the core RAG pipeline from ingestion to retrieval to chat integration.

#### 2.1 PostgreSQL + pgvector Setup

- Added pgvector extension to PostgreSQL
- Created Document and DocumentChunk models with vector column (1536 dimensions)
- HNSW index for efficient similarity search

#### 2.2 Embedding and Ingestion Services

- Embedding service using OpenAI text-embedding-3-large
- Ingestion service for single document processing
- Naive chunking strategy (MAX_CHUNK_SIZE=1000, CHUNK_OVERLAP=100)
- API endpoint for document ingestion (`POST /api/documents/ingest`)

#### 2.3 Retrieval and RAG Integration

- Retrieval service with semantic search (cosine similarity)
- RAG integration in chat agent (RAG_TOP_K=3, RAG_SIMILARITY_THRESHOLD=0.25)
- Context injection into system prompt
- API endpoint for semantic search (`POST /api/documents/search`)

---

## Next Up

### Phase 2.5: RAG Experimentation

Before scaling to full vault ingestion, experiment with the RAG pipeline to find optimal settings.

**Why this matters:**

- Chunking strategy significantly impacts retrieval quality
- Similarity thresholds affect precision/recall tradeoff
- Better to tune on small scale before processing entire vault
- Learning opportunity: understand how these parameters affect results

#### Chunking Strategy Experiments

- Try different chunk sizes (500, 1000, 2000 chars)
- Experiment with overlap ratios
- Consider semantic chunking (respect markdown headers, paragraphs)
- Evaluate recursive chunking approaches

#### Similarity Threshold Tuning

- Test different RAG_SIMILARITY_THRESHOLD values
- Analyze precision vs recall at various thresholds
- Consider dynamic thresholds based on query type
- Add logging/metrics to evaluate retrieval quality

### Phase 2.6: Full Vault Ingestion

Scale the ingestion pipeline to process an entire Obsidian vault.

- Configure vault path via environment variable
- Batch processing for multiple markdown files
- Parse frontmatter metadata (tags, dates, links)
- Progress tracking for large vaults

### Phase 2.7: Sync and Refresh

Keep the knowledge base current.

- Manual re-sync endpoint/button
- Track file modification times to detect changes
- Incremental updates (only re-embed changed files)
- Handle deleted/renamed files

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
- Phase 2 is broken into sub-milestones to allow incremental progress.
- RAG experimentation (2.5) is intentionally before full vault ingestion to tune parameters at small scale.
