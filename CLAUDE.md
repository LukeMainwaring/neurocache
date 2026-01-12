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

# Run tests
cd backend && uv run pytest
cd backend && uv run pytest -m main      # only main tests
cd backend && uv run pytest tests/test_file.py::test_name  # single test


```

### Frontend (TypeScript/Next.js)

```bash
cd frontend && pnpm install
cd frontend && pnpm dev        # start dev server with turbo
cd frontend && pnpm build      # production build
cd frontend && pnpm lint       # lint with ultracite
cd frontend && pnpm format     # format with ultracite
```

## Architecture

### Backend (`backend/`)

FastAPI Python backend using async patterns throughout.

-   **`src/neurocache/app.py`**: FastAPI application entry point with CORS and logging middleware
-   **`src/neurocache/routers/`**: API routes organized by domain (chat, thread, user, health)
-   **`src/neurocache/agents/`**: Pydantic AI agents - `chat_agent.py` contains the main conversational agent
-   **`src/neurocache/models/`**: SQLAlchemy async models (Thread, Message, User)
-   **`src/neurocache/schemas/`**: Pydantic models for request/response validation
-   **`src/neurocache/core/config.py`**: Settings via pydantic-settings (reads from `.env`)
-   **`src/neurocache/migrations/`**: Alembic migrations for PostgreSQL

Key patterns:

-   All database operations are async using `AsyncSession`
-   Agents stream responses as SSE in Vercel AI SDK v1 format
-   Messages stored as JSONB, threads have composite primary key (thread_id, agent_type)
-   Type hints required on all functions

### Frontend (`frontend/`)

Next.js 16 with App Router and React 19.

-   **`app/(chat)/`**: Chat route group with main chat pages
-   **`app/(chat)/api/chat/route.ts`**: Proxy route that forwards chat requests to backend
-   **`components/chat.tsx`**: Main chat component using `@ai-sdk/react` useChat hook
-   **`lib/api/backend-client.ts`**: API client for backend communication
-   **`components/ui/`**: Reusable UI components (shadcn/ui style)

Key patterns:

-   Uses Vercel AI SDK's `useChat` for streaming chat
-   Backend URL configured via `NEXT_PUBLIC_BACKEND_URL` env var
-   SWR for data fetching with automatic revalidation

### Data Flow

1. Frontend `useChat` sends messages to `/api/chat` route
2. Route proxies to backend `/api/chat/stream`
3. Backend's chat agent processes with Pydantic AI
4. Response streams back as SSE, stored in PostgreSQL
5. Frontend renders streamed chunks in real-time

## Additional Instructions

-   This project uses Pydantic AI. LLM-friendly documentation for this library can be found at <https://ai.pydantic.dev/llms.txt>, which contains an overview and links to Markdown-formatted content.
-   Assume that Git operations for branches, commits, and pushes will be done manually. If executing a multi-step, comprehensive plan that involves successive commits, ask before making a commit.
