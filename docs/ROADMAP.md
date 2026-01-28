# Neurocache Roadmap

A personal "second brain" AI chat application. This roadmap focuses on what matters for a local, experimental app.

## Current State

- **Working**: Chat with streaming, message persistence, thread management, auto-generated thread titles, user personalization settings, RAG vertical slice (single document ingestion, semantic search, context injection), markdown-aware chunking strategy, batch ingestion of all documents from a knowledge source, sync lifecycle with manual re-sync UI and status tracking, change detection during sync (re-index modified files, clean up deleted files)
- **Next Up**: Enhanced retrieval (cross-reference discovery, citations, hybrid search)

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
- API endpoint for document ingestion (`POST /api/documents/ingest`)

#### 2.3 Retrieval and RAG Integration

- Retrieval service with semantic search (cosine similarity)
- RAG integration in chat agent (RAG_TOP_K=3, RAG_SIMILARITY_THRESHOLD=0.25)
- Context injection into system prompt
- API endpoint for semantic search (`POST /api/documents/search`)

#### 2.4 Chunking Strategy (Done)

Implemented markdown-aware chunking for better retrieval quality.

- Section detection based on markdown headers (h1-h6) and date patterns
- Context injection into each chunk with `[Source: filename]` and `[Section: header]` prefixes
- Tuned chunk parameters: target 1500 chars, max 2000, overlap 200, min 300
- Improved over naive character-based chunking by respecting document structure

#### 2.5 Batch Ingestion (Done)

Scaled the ingestion pipeline to process all documents from a knowledge source at once.

- `POST /knowledge-sources/{source_id}/ingest-all` endpoint
- Automatic discovery of all .md files in the vault via `discover_markdown_files()`
- Exclusion of system directories (.obsidian, .git, .smart-env, copilot, .trash)
- Skip logic for already indexed documents (avoids re-processing)
- `force_reindex` parameter to re-ingest even if already indexed
- Error handling: continues on single file failure, reports all failures at end
- `BatchIngestResult` response with statistics (total_files_found, documents_created, documents_skipped, documents_failed, failed_files, duration_seconds)

#### 2.6 Sync Lifecycle (Done)

Added manual sync with status tracking and service layer reorganization.

- `sync_documents()` service wrapping ingestion with lifecycle management (SYNCING -> CONNECTED/ERROR)
- `last_synced_at` timestamp on KnowledgeSource model, set on successful sync
- Document stats tracked in source config (documents_indexed, documents_failed)
- Service layer reorganization: `services/knowledge_source/` package with ingestion, knowledge_source, vault_validator, and retrieval modules
- Simplified router delegating to service layer
- Frontend: Sync Now button with syncing state, document count display, last synced relative time, toast messages with sync results
- Improved markdown parsing (cleaner frontmatter stripping, better title extraction)

#### 2.7 Change Detection (Done)

Made sync detect modified and deleted files instead of blindly skipping existing documents.

- Two-stage change detection: fast `file_modified_at` mtime comparison, then `content_hash` (SHA-256) if mtime differs
- Modified files are deleted and re-ingested with fresh chunks and embeddings
- After processing discovered files, DB records for files no longer on disk are cleaned up (cascade deletes chunks)
- Renamed files handled implicitly as delete + create (no special rename logic)
- `BatchIngestResult` extended with `documents_updated` and `documents_deleted` counters
- `Document.get_all_by_source()` classmethod for comparing DB records against discovered files
- Frontend toast messages show granular sync results (new, updated, removed, unchanged, failed)

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
