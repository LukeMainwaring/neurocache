---
paths:
  - "frontend/components/**/*.tsx"
  - "frontend/app/(chat)/**/*.{ts,tsx}"
  - "frontend/hooks/**/*.{ts,tsx}"
  - "frontend/api/hooks/**/*.{ts,tsx}"
  - "frontend/lib/**/*.ts"
---

# Vercel AI SDK Rules

## Docs are split between two places

The Vercel AI SDK's documentation lives in two places with **different content**:

1. **`docs/vercel-ai-sdk-ui.txt`** — local pinned reference, **UI surface only**
   (`useChat`, message parts, chat transports, the SSE stream protocol,
   tool-call rendering). Refresh via the `updating-deps` skill — its docs-fetch
   step is the source of truth for which upstream pages we mirror.

2. **`https://ai-sdk.dev/`** — everything else. AI SDK Core (`generateText`,
   server-side `streamText`, model providers), guides, framework examples,
   cookbook. Not cached locally; fetch ad-hoc with WebFetch.

**Rule of thumb:** if you're grepping `vercel-ai-sdk-ui.txt` for anything
outside the UI slice and finding nothing, it hasn't been deleted — it's on
the web docs. Use WebFetch on `https://ai-sdk.dev/docs/...` before giving up.

## The chat surface in this project

- **AI SDK UI only — no Core server-side.** `app/(chat)/api/chat/route.ts` is
  a thin proxy to the FastAPI backend's `POST /api/chat/stream`; Pydantic AI
  emits the SSE stream via `VercelAIAdapter.dispatch_request()`. When the docs
  show `streamText` / `toUIMessageStreamResponse`, that's a **spec for what the
  backend must emit**, not code to write here.
- **Keep `ChatMessage` threaded.** `useChat` is parameterized by the custom
  `ChatMessage` type in `frontend/lib/types.ts`. Carry that generic through
  every `UseChatHelpers` site — falling back to plain `UIMessage` loses the
  project's custom metadata (RAG sources, web sources) and tool-part typing.
- **Tool-call panels switch on `part.type === "tool-<name>"`** in the message
  renderer. Use the `isToolPart()` helper in `components/message.tsx` to detect
  tool parts — both `tool-<name>` and `dynamic-tool` are valid tool-part shapes
  and the helper handles both. A new backend tool that needs a custom UI panel
  adds a branch there.
- **Tool-call streaming caveat.** `experimental_throttle: 100` on `useChat`
  coalesces intermediate states, so tool parts often arrive as
  `output-available` directly without an in-between `input-streaming` /
  `output-streaming` tick. The `isStreaming` prop on `ToolCall` compensates;
  don't assume incremental tool-state transitions will be observable.

## On finish: refetch from DB

After a stream completes, the frontend refetches messages from the DB. RAG
and web-source metadata are attached on the backend in
`utils/message_serialization.py` and surface as inline citations on assistant
messages plus "View Sources" / "View Web Sources" buttons on user messages.
The streamed message is a placeholder for that — don't try to fish source
metadata out of the SSE stream itself.
