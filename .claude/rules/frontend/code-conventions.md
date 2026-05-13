---
paths:
  - "frontend/components/**/*.{ts,tsx}"
  - "frontend/app/**/*.{ts,tsx}"
  - "frontend/hooks/**/*.{ts,tsx}"
  - "frontend/api/hooks/**/*.{ts,tsx}"
  - "frontend/lib/**/*.ts"
---

# Frontend Patterns

TypeScript/Next.js conventions for the neurocache frontend.

## Imports

- Use the `@/` path alias for imports that cross top-level directories
  (e.g., `import { cn } from "@/lib/utils"`,
  `import { useThreads } from "@/api/hooks/threads"`).
- Relative imports are fine for files in the same directory or in a direct
  subdirectory grouping within `components/` (e.g., `./ui/button`,
  `./elements/tool-call`, `./sidebar-history-item`). This matches the
  Vercel chatbot template pattern the codebase descends from.

## UI Components

- Use shadcn/ui components from `components/ui/` instead of raw HTML elements:
  - `<Button>` over `<button>` — provides consistent focus rings, disabled
    states, and cursor styles.
  - `<Input>` over `<input>` — except hidden file inputs
    (`type="file" className="hidden"`) and non-text inputs like sliders
    (`type="range"`), which are fine as raw elements.
  - `<Textarea>` over `<textarea>`.
  - `<Skeleton>` over `<div className="animate-pulse ...">` for loading
    placeholders.
  - `<Tooltip>` over `title=` attributes on interactive elements (buttons,
    icon buttons). Native `title=` is acceptable on text elements for
    truncation hints.
  - `<Separator>` for standalone visual dividers. Border classes (`border-b`,
    `border-t`) are fine when the border is part of a container's layout.
  - `<AlertDialog>` for confirmation dialogs, `<Dialog>` for modals,
    `<DropdownMenu>` for context menus, `<Collapsible>` for expandable
    sections, `<Sheet>` for slide-out panels.
  - `<Card>` for card-shaped surfaces (see `activation-guard.tsx`). Don't
    reach for raw `border-border bg-card` divs — the project standard is
    the `<Card>` family (`Card`, `CardHeader`, `CardContent`, etc.).
- When a shadcn component's default variant matches your needs, don't rewrite
  the styles — just use the variant. Override with `className` only for
  styles the variant doesn't cover.
- Do not manually edit files in `components/ui/` unless adding a new shadcn
  component or customizing an existing variant.

## Code Style

- Use kebab-case for filenames (e.g., `multimodal-input.tsx`,
  `rag-sources-dialog.tsx`, `sidebar-history-item.tsx`).
- Colocate types with their component unless shared across multiple files.
- Use `useCallback` and `memo` where the current codebase already does
  (`messages.tsx`, `message.tsx`, `multimodal-input.tsx`, `message-actions.tsx`,
  `sidebar-history-item.tsx`, `chat-header.tsx` all wrap their components in
  `memo`, several with a custom equality fn). Don't add new memoization
  speculatively — Next.js 16 ships with React 19, and once the React Compiler
  is enabled most manual `useCallback`/`useMemo` becomes redundant or
  counterproductive.
- Use `cn()` from `@/lib/utils` for conditional class merging.

## Generated API client

- The TypeScript client under `frontend/api/generated/` is regenerated from
  the backend OpenAPI schema by `pnpm -C frontend generate-client`. Never edit
  those files by hand — changes are wiped on the next regeneration.
- After modifying any backend route or schema, run `generate-client` and stage
  the regenerated files alongside the backend change.
- Wrap generated endpoints in custom TanStack Query hooks under `api/hooks/`
  rather than calling the SDK directly from components.
