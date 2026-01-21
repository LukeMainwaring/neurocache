# Neurocache Roadmap

A personal "second brain" AI chat application. This roadmap focuses on what matters for a local, experimental app.

## Current State

-   **Working**: Chat with streaming, message persistence, thread management, auto-generated thread titles
-   **Missing**: RAG/knowledge base (the core feature)

---

## Phase 1: User Personalization

Make the chat agent more helpful by incorporating user-specific context into every conversation.

### 1.1 Improved System Prompt

-   Revamp the default system prompt in `chat_agent.py` to be more thorough and helpful
-   Structure the prompt to cleanly incorporate user personalization data

### 1.2 User Personalization Settings

Add editable fields for users to customize their AI experience (inspired by ChatGPT):

-   **Custom instructions**: Free-form guidance for how the AI should respond
-   **Nickname**: What the user prefers to be called
-   **Occupation**: User's profession or role for relevant context
-   **About you**: Additional personal context the AI should know

### 1.3 Full-Stack Implementation

-   **Backend**: Add personalization fields to User model, create API endpoints for get/update
-   **Frontend**: Settings page with form to edit personalization fields
-   **Integration**: Inject personalization data into system prompt at chat time


## Phase 2: Obsidian Integration (RAG)

The core differentiating feature. Connect to a local Obsidian vault as the knowledge base.

### 2.1 Obsidian Vault Connection

-   Configure local vault path
-   Read and index markdown files
-   Watch for file changes (or manual re-sync)

### 2.2 Vector Embeddings

-   Add pgvector extension to PostgreSQL
-   Generate embeddings for note chunks
-   Store with source file metadata

### 2.3 RAG in Chat

-   Semantic search over notes before LLM call
-   Include relevant context in system prompt
-   Show source attribution (which notes were used)

---

## Phase 3: Enhanced Retrieval

### Cross-Reference Discovery

Surface connections across notes during conversation.

-   "Related notes" suggestions
-   Concept linking across different sources

### Citation Display

-   Inline citations linking to source notes
-   Expandable previews

---

## Deferred Features

Features documented here to avoid re-adding them prematurely. These make sense for a production app but are unnecessary overhead for local experimentation.

### Authentication

Currently uses a hardcoded demo user. Real auth (OAuth, email/password) only matters if the app becomes multi-user or deployed.

### Error Handling & Resilience

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

-   Obsidian is the primary knowledge source. Keep the ingestion pipeline simple.
-   This is a learning project. Optimize for understanding patterns, not production robustness.
-   Incremental progress: each item should be completable in a reasonable work session.
