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
-   Keep route handlers thin: push business logic to `services/`, DB logic to `models/`
-   Use modern Python syntax: `| None` over `Optional`, `list` over `List`
-   Use f-strings for logging: `logger.info(f"Created {item.id}")` not `logger.info("Created %s", item.id)`
-   When creating SQLAlchemy columns, prefer simple Python type inference and only use `mapped_column` when column-based attributes require more specific customization. Example: `name: Mapped[str | None]` instead of `name: Mapped[str | None] = mapped_column(String(255), nullable=True)`
-   After generating an alembic database migration, pause and ask if it looks okay before running `migrate-docker.sh`. Never run downgrade scripts without explicit user request.
-   Re-export convention for `__init__.py`:
    -   **Default:** Keep `__init__.py` empty; use deep imports (`from neurocache.models.thread import Thread`)
    -   **Exception — `models/`:** Re-export all models for Alembic autogenerate support
    -   **Exception — `routers/`:** Re-export routers for clean aggregation in `main.py`

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

1. Frontend `useChat` sends streaming messages to `/api/chat` route; non-streaming calls use TanStack Query hooks from `api/hooks/`
2. Route proxies to backend `/api/chat/stream`
3. Backend's chat agent processes with Pydantic AI
4. Response streams back as SSE, stored in PostgreSQL
5. Frontend renders streamed chunks in real-time

## Additional Instructions

-   This project uses Pydantic AI. LLM-friendly documentation for this library can be found at <https://ai.pydantic.dev/llms.txt>, which contains an overview and links to Markdown-formatted content.
-   Assume that Git operations for branches, commits, and pushes will mostly be done manually. If executing a multi-step, comprehensive plan that involves successive commits, ask before making a commit.
-   Do not make any changes until you have 95% confidence that you know what to build - ask me follow up questions using the AskUserQuestion tool until you have that confidence; but don't ask obvious questions, dig into the hard parts I might not have considered.
-   Do not worry about running the pytest commands yet. I have not implemented unit tests and likely will not for a while
-   After modifying backend API endpoints, regenerate the frontend client with `cd frontend && pnpm generate-client`. Do not manually edit files in `frontend/api/generated/`.
