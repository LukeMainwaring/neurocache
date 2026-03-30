# Neurocache

A personal "second brain" AI chat application. Talk to an AI agent that can help you organize and retrieve information from your knowledge base.

## Context and Motivation

I'd like the AI/LLM tools I use to have better context into my foundational knowledge, priorities, and active ideas. Over the years, I have read tons of books, articles, and other resources. I have recorded notes and ideas about personal projects and life. I'd like to leverage these to create an "institution of my brain" - a model based on the text that has gone in and out of my mind.

ChatGPT and Claude have powerful memory features, but they're limited to interactions from within the app. I'd like to set up a framework that combines as many meaningful sources as possible. This will most likely be some form of RAG system, maybe with a special document structure.

When I chat with this AI system, it should:
- Reference a knowledge base tailored to me
- Focus on the books I've read and my current research thoughts
- Draw connections across concepts
- Search the web for real-time information when needed

**Important notes:**
- This is a personal project, developed by me, mostly locally for now
- I am the end user and will supply my own notes, ideas, and sources
- Goals: (1) learn full-stack AI agent chatbot development, and (2) build something more useful than general-purpose chatbots by referencing my own knowledge base
- If successful, I may eventually productionize and open this app to other users

## Architecture

```
neurocache/
├── backend/        # FastAPI Python backend
├── frontend/       # Next.js frontend
└── docker-compose.yml
```

### Backend

-   **FastAPI** with async support
-   **PostgreSQL** database with SQLAlchemy
-   **Pydantic AI** for LLM agent orchestration (hybrid RAG + web search)

### Frontend

-   **Next.js 16** with App Router
-   **React 19** with Tailwind CSS
-   **Vercel AI SDK** for streaming chat

## Quick Start

1. Copy environment files:

    ```bash
    cp .env.sample .env
    cp frontend/.env.example frontend/.env.local
    ```

2. Add your OpenAI API key and Auth0 credentials to `.env`

3. Start the backend with Docker:

    ```bash
    docker compose up -d
    ```

4. Start the frontend:

    ```bash
    pnpm -C frontend install
    pnpm -C frontend dev
    ```

5. Open [localhost:3000](http://localhost:3000)

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development instructions.
