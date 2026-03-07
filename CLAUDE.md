# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

See @README.md for a project overview and @DEVELOPMENT.md for a development guide.

When working with this codebase, prioritize readability over cleverness. Ask clarifying questions before making architectural changes.

## Common Commands

### Backend (Python)

```bash
# Install dependencies
cd backend && uv sync

# Run backend with Docker (includes PostgreSQL)
docker compose up -d

# Pre-commit hooks (covers type checking, linting, and formatting for backend)
uv run pre-commit run --all-files

# Create local database migration
cd backend && ./scripts/create-db-revision-docker.sh "<migration_message>"

# Apply pending migrations (ask user first)
cd backend && ./scripts/migrate-docker.sh
```

### Frontend (TypeScript/Next.js)

```bash
cd frontend && pnpm install
cd frontend && pnpm lint            # lint with ultracite
cd frontend && pnpm format          # format with ultracite
cd frontend && pnpm generate-client # regenerate API client from backend OpenAPI
```

After making frontend code changes, run `pnpm format` to fix formatting. Use `pnpm lint` to check for errors. Do not run `pnpm build` for validation—it's slow and rarely catches issues that linting misses. The dev server (`pnpm dev`) is typically already running during development.

## Architecture

### Backend (`backend/`)

FastAPI Python backend using async patterns throughout.

-   **`src/neurocache/app.py`**: FastAPI application entry point with CORS and logging middleware
-   **`src/neurocache/routers/`**: API routes by domain (chat, threads, users, knowledge sources, health)
-   **`src/neurocache/agents/`**: Pydantic AI agents — `chat_agent.py` defines the chat agent and system prompt (uses `OpenAIResponsesModel` with `WebSearchTool` for web search and `search_knowledge_base` for RAG); `book_analysis_agent.py` generates structured book analysis (tags, summary, key concepts) on PDF upload; `deps.py` defines shared `AgentDeps`; `tools/` contains agent tools (e.g., `knowledge_base_tools.py` for RAG search)
-   **`src/neurocache/models/`**: SQLAlchemy async models with CRUD classmethods (User, Thread, Message, KnowledgeSource, Document)
-   **`src/neurocache/schemas/`**: Pydantic schemas for API contracts, enums, and domain types
-   **`src/neurocache/services/`**: Business logic (embeddings, RAG retrieval, document ingestion, title generation)
-   **`src/neurocache/utils/message_serialization.py`**: Message format round-trip: storage serialization, frontend conversion via `VercelAIAdapter.dump_messages()`, RAG/web source metadata extraction and attachment
-   **`src/neurocache/core/config.py`**: Settings via pydantic-settings (reads from `.env`)
-   **`src/neurocache/migrations/`**: Alembic migrations for PostgreSQL
-   **`src/neurocache/dependencies/`**: FastAPI dependency injection (db sessions, OpenAI client, auth)

See `.claude/rules/backend/code-conventions.md` for code style and conventions.

### Frontend (`frontend/`)

Next.js 16 with App Router and React 19.

-   **`app/(chat)/`**: Chat route group with main chat pages
-   **`app/(chat)/api/chat/route.ts`**: Proxy route that forwards chat requests to backend
-   **`components/chat.tsx`**: Main chat component using `@ai-sdk/react` useChat hook
-   **`api/client.ts`**: Axios client configuration (baseURL, credentials)
-   **`api/hooks/`**: Custom TanStack Query hooks wrapping generated client
-   **`api/generated/`**: Auto-generated TypeScript client from OpenAPI (do not edit manually)
-   **`components/ui/`**: Reusable UI components (shadcn/ui style)

Key patterns:

-   Uses Vercel AI SDK's `useChat` for streaming chat
-   Backend URL configured via `NEXT_PUBLIC_BACKEND_URL` env var
-   TanStack Query for data fetching with automatic caching/invalidation
-   Generated API client from backend OpenAPI schema - run `pnpm generate-client` after backend API changes

### Data Flow

1. Frontend `useChat` sends full message array to `/api/chat` route; non-streaming calls use TanStack Query hooks from `api/hooks/`
2. Route proxies raw request body to backend `/api/chat/stream`
3. Backend uses `VercelAIAdapter.dispatch_request()` to parse the request and execute the chat agent, which decides whether to call `search_knowledge_base` for RAG retrieval or `web_search` for real-time web results, then streams the response
4. `on_complete` callback extracts web search sources, persists conversation (with RAG/web source metadata) to PostgreSQL, and triggers title generation for new threads
5. Frontend renders streamed chunks in real-time; on finish, refetches messages from DB for RAG/web source metadata (displayed via "View Sources" / "View Web Sources" buttons on user messages)

## Additional Instructions

-   This project uses Pydantic AI. Documentation is available at `docs/pydantic-ai-llms-full.txt`. Read this file when working on agent code or when you need Pydantic AI API reference. Re-download periodically with `curl -o docs/pydantic-ai-llms-full.txt https://ai.pydantic.dev/llms-full.txt`.
-   Vercel AI SDK UI documentation is available at `docs/vercel-ai-sdk-ui.txt`. This project only uses **AI SDK UI** (hooks like `useChat` for chat UI) — it does NOT use AI SDK Core (LLM orchestration is handled by Pydantic AI on the backend). Read this file when working on frontend chat UI, message rendering, `useChat` hook, or streaming integration. Re-download with: `curl -s https://ai-sdk.dev/llms.txt | sed -n -e '/^# AI SDK UI$/,/^# AI_APICallError$/{' -e '/^# AI_APICallError$/d' -e p -e '}' > docs/vercel-ai-sdk-ui.txt`.
-   Assume that Git operations for branches, commits, and pushes will mostly be done manually. If executing a multi-step, comprehensive plan that involves successive commits, ask before making a commit.
-   Do not run `cd ... && git ...` for git commands in this repo. Assume you are already in the codebase.
-   Do not make any changes until you have 95% confidence that you know what to build - ask me follow up questions using the AskUserQuestion tool until you have that confidence; but don't ask obvious questions, dig into the hard parts I might not have considered.
-   Do not worry about running the pytest commands yet. I have not implemented unit tests and likely will not for a while
-   After modifying backend API endpoints, regenerate the frontend client with `cd frontend && pnpm generate-client`. Do not manually edit files in `frontend/api/generated/`.
