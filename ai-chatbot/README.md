# Neurocache Frontend

Next.js frontend for Neurocache - a personal "second brain" AI chat application.

## Tech Stack

- [Next.js 16](https://nextjs.org) with App Router
- [React 19](https://react.dev)
- [Tailwind CSS 4](https://tailwindcss.com)
- [shadcn/ui](https://ui.shadcn.com) components
- [Vercel AI SDK](https://sdk.vercel.ai) for chat streaming

## Prerequisites

- Node.js 18+
- pnpm
- Backend service running (see `../backend/`)

## Running Locally

1. Copy environment variables:
   ```bash
   cp .env.example .env.local
   ```

2. Update `.env.local` with your backend URL (default: `http://localhost:8000`)

3. Install dependencies and run:
   ```bash
   pnpm install
   pnpm dev
   ```

The app will be running at [localhost:3000](http://localhost:3000).

## Project Structure

```
app/           # Next.js app router pages
components/    # React components
  ui/          # shadcn/ui components
  elements/    # Custom UI elements
hooks/         # Custom React hooks
lib/           # Utilities and types
```
