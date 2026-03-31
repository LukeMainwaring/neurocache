<div align="center">
  <img src="frontend/public/images/neurocache-logo.png" alt="Neurocache" width="120" />
  <h1>Neurocache</h1>
  <p>Build an institution of your mind. An AI agent that turns your notes, books, and articles into a searchable second brain — grounding every answer in what you actually know.</p>

  [![CI](https://github.com/LukeMainwaring/neurocache/actions/workflows/ci.yml/badge.svg)](https://github.com/LukeMainwaring/neurocache/actions/workflows/ci.yml)
  [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
</div>

<div align="center">
  <img src="docs/assets/search-knowledge-base.gif" alt="Neurocache demo — hybrid search with inline citations" width="700" />
</div>

## Why Neurocache?

General-purpose chatbots (ChatGPT, Claude) start every conversation from scratch. Neurocache connects to your Obsidian vault and makes your entire knowledge base searchable by an AI agent that can:

- **Retrieve from your notes** — semantic + keyword hybrid search finds relevant content even when you didn't use the exact words
- **Search the web** — supplements your knowledge with real-time information when needed
- **Cite its sources** — inline citations link back to the exact note, with Obsidian deep links
- **Extract insights back** — save conversation highlights as new notes, creating a knowledge growth loop

## Features

- **Hybrid RAG** — Semantic (pgvector cosine) + keyword (PostgreSQL full-text) search fused with Reciprocal Rank Fusion, with content-type boosting (your notes rank above raw book content)
- **Streaming chat** — Real-time responses via Vercel AI SDK with Pydantic AI agent orchestration
- **Inline citations** — Clickable `[1]` markers showing source path, content type, and similarity score; hover for preview, click for full content
- **Obsidian deep links** — Every citation path is an `obsidian://` link that opens the source note directly
- **PDF book pipeline** — Upload a book PDF → AI generates tags, summary, and key concepts → content is chunked, embedded, and searchable
- **Web search** — Agent decides when to search the web for current information
- **MCP server** — Exposes the knowledge base as MCP tools for Claude Desktop, Claude Code, and Cursor
- **Conversation-to-knowledge** — "Extract Insights" analyzes a conversation and generates a structured Obsidian note, which gets ingested back into the knowledge base
- **User personalization** — Profile context (background, interests, custom instructions) shapes how the agent responds
- **Auth0 authentication** — JWT-based auth with JWKS verification

## Demo Workflows

These prompts showcase what Neurocache can do that generic chatbots can't. See [docs/DEMO_WORKFLOWS.md](docs/DEMO_WORKFLOWS.md) for the full list.

**Hybrid personal + web search:**
> "I've been thinking about how the Stoic concept of 'memento mori' connects to the Buddhist idea of impermanence. What have I written about either of these ideas, and how do modern psychologists frame this overlap?"

Triggers both `search_knowledge_base` (your notes on Stoicism, Buddhism) and `web_search` (current psychology research). The response synthesizes your thinking with external knowledge, citing both.

**Deep knowledge base retrieval:**
> "What have I written about [topic] and where do my ideas contradict each other?"

Retrieves relevant chunks across notes written months apart, then reasons about tensions and evolution in your thinking.

**Cross-domain connections:**
> "What connections can you find between my notes on [Topic A] and [Topic B]?"

Surfaces non-obvious links across your knowledge base using semantic search and LLM reasoning.


## MCP Integration

Search your knowledge base from Claude Desktop, Claude Code, or Cursor via the built-in MCP server.

<div align="center">
  <img src="docs/assets/mcp-claude-search.png" alt="Searching the knowledge base from Claude" width="30%" />
  &nbsp;&nbsp;
  <img src="docs/assets/mcp-claude-save.png" alt="Save to knowledge base in Claude" width="30%" />
    &nbsp;&nbsp;
  <img src="docs/assets/mcp-obsidian-save.png" alt="Obsidian note output from thread" width="30%" />
</div>

## PDF Book Pipeline

Upload a book PDF and the AI generates tags, a summary, and key concepts — then the content is chunked, embedded, and searchable.

<div align="center">
  <img src="docs/assets/book-upload-pdf.png" alt="PDF book upload and AI analysis" width="45%" />
  &nbsp;&nbsp;
  <img src="docs/assets/book-obsidian-note.png" alt="Obsidian note with output from book agent" width="45%" />
</div>


## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (for PostgreSQL + backend)
- [pnpm](https://pnpm.io/installation) (for frontend)
- [uv](https://docs.astral.sh/uv/) (for Python dependency management)
- An [OpenAI API key](https://platform.openai.com/api-keys)
- An [Auth0](https://auth0.com/) tenant (free tier works)
- An Obsidian vault with markdown notes (this is what Neurocache searches)

### Setup

1. **Configure environment:**

    ```bash
    cp .env.sample .env
    cp frontend/.env.example frontend/.env.local
    ```

    Fill in your OpenAI API key, Auth0 credentials, and Obsidian vault path in `.env`. Add your Auth0 domain and client ID to `frontend/.env.local`.

2. **Start the backend:**

    ```bash
    docker compose up -d
    ```

    This starts PostgreSQL (with pgvector) and the FastAPI backend. On first run, Alembic migrations apply automatically.

3. **Start the frontend:**

    ```bash
    pnpm -C frontend install
    pnpm -C frontend dev
    ```

4. **Open [localhost:3000](http://localhost:3000)** — sign in, connect your vault in Settings > Knowledge Base, and start chatting.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.13, FastAPI, Pydantic AI, SQLAlchemy (async), Alembic |
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS 4, Vercel AI SDK |
| **Database** | PostgreSQL 17, pgvector, tsvector full-text search |
| **AI** | OpenAI (GPT-4o, text-embedding-3-large), Pydantic AI agents |
| **Auth** | Auth0 (JWT + JWKS verification) |
| **Infrastructure** | Docker Compose, GitHub Actions CI, pre-commit hooks |
| **Integrations** | MCP server (FastMCP), Obsidian deep links |

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for setup, testing, linting, migrations, and API client generation.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for planned features including temporal knowledge tracking, cross-reference discovery, and knowledge gap detection.

## License

[MIT](LICENSE)
