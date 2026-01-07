# Neurocache

A personal "second brain" AI chat application. Talk to an AI agent that can help you organize and retrieve information from your knowledge base.

## Architecture

```
neurocache/
├── backend/        # FastAPI Python backend
├── ai-chatbot/     # Next.js frontend
└── docker-compose.yml
```

### Backend
- **FastAPI** with async support
- **PostgreSQL** database with SQLAlchemy
- **Pydantic AI** for LLM agent orchestration

### Frontend
- **Next.js 16** with App Router
- **React 19** with Tailwind CSS
- **Vercel AI SDK** for streaming chat

## Quick Start

1. Copy environment files:
   ```bash
   cp .env.sample .env
   cp ai-chatbot/.env.example ai-chatbot/.env.local
   ```

2. Add your OpenAI API key to `.env`

3. Start the backend with Docker:
   ```bash
   docker compose up -d
   ```

4. Start the frontend:
   ```bash
   cd ai-chatbot
   pnpm install
   pnpm dev
   ```

5. Open [localhost:3000](http://localhost:3000)

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development instructions.
