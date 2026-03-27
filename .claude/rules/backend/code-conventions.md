# Backend Patterns

Python/FastAPI conventions for the neurocache backend.

## Code Style

- Use lowercase with underscores for filenames (e.g., `chat_agent.py`, `title_generator.py`)
- Use modern Python syntax: `| None` over `Optional`, `list` over `List`
- Use f-strings for logging: `logger.info(f"Created {item.id}")`
- Use descriptive variable names with auxiliary verbs (e.g., `is_active`, `has_permission`)
- Type hints required on all functions

## Architecture

- Use `def` for pure functions, `async def` for I/O operations
- Use FastAPI's dependency injection for shared resources (db sessions, auth, config)
- All database operations are async using `AsyncSession`
- Keep route handlers thin: push business logic to `services/`, DB logic to `models/`
- Import service modules with a named alias in routers: `from neurocache.services import thread as thread_service`, then call `thread_service.rename_thread(...)`. This avoids name collisions with router functions and makes the delegation explicit.
- Use `BackgroundTasks` for blocking, secondary work in routes
- Prefer Pydantic models over raw dicts for request/response schemas

## Data Patterns

- Messages stored as JSONB, threads have composite primary key (thread_id, agent_type)
- RAG source metadata stored as extra field on request messages for frontend display
- Agents stream responses via `VercelAIAdapter.dispatch_request()` (Vercel AI SDK format)
- Message persistence handled via `on_complete` callback using append-only `Message.save_history()`
- RAG retrieval is agentic: the agent calls `search_knowledge_base` tool on demand (not pre-fetched). Tool functions live in `agents/tools/` and are bundled into capabilities in `agents/capabilities/`

## Pydantic

- Prefer Pydantic schemas over dataclasses and raw dicts for data structures
- Use Pydantic v2 conventions: `model_dump()` not `dict()`, `model_validate()` not `parse_obj()`
- Leverage Pydantic features: `@field_validator`, `@model_validator`, `@computed_field`, `Field()` constraints
- Use `model_dump(exclude_unset=True)` for partial updates
- Serialization: `model_dump()`, `model_dump_json()`, use `@field_serializer` for custom formats
- Deserialization: `model_validate()`, `model_validate_json()` for parsing raw data

## SQLAlchemy

- Prefer simple Python type inference; only use `mapped_column` when column attributes need customization. Example: `name: Mapped[str | None]` instead of `name: Mapped[str | None] = mapped_column(String(255), nullable=True)`
- Encapsulate DB logic in model `@classmethod` functions: `create`, `update`, `delete` for mutations; `get_by_*` for queries. See `models/document.py`.

## Migrations

- After generating an alembic migration, pause and ask if it looks okay before running `migrate-docker.sh`
- Never run downgrade scripts without explicit user request

## Module Conventions

Re-export convention for `__init__.py`:

- **Default:** Keep `__init__.py` empty; use deep imports (`from neurocache.models.thread import Thread`)
- **Exception — `models/`:** Re-export all models for Alembic autogenerate support
- **Exception — `routers/`:** Re-export routers for clean aggregation in `main.py`
