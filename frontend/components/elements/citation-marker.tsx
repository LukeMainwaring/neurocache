"use client";

import type { RAGSource } from "@/lib/types";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../ui/tooltip";

const CONTENT_TYPE_LABELS: Record<string, string> = {
  personal_note: "Personal Note",
  book_note: "Book Note",
  book_source: "Book Source",
  article: "Article",
};

type CitationMarkerProps = {
  number: number;
  source?: RAGSource;
};

export function CitationMarker({ number, source }: CitationMarkerProps) {
  if (!source) {
    return (
      <sup className="mx-0.5 inline-flex cursor-default rounded px-1 py-0.5 text-[10px] leading-none text-muted-foreground">
        [{number}]
      </sup>
    );
  }

  const typeLabel = source.content_type
    ? (CONTENT_TYPE_LABELS[source.content_type] ?? "Note")
    : "Note";
  const matchPct = Math.round(source.similarity * 100);

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <sup className="mx-0.5 inline-flex cursor-pointer rounded bg-primary/10 px-1 py-0.5 text-[10px] leading-none text-primary transition-colors hover:bg-primary/20">
            [{number}]
          </sup>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs">
          <p className="font-mono text-xs">{source.path}</p>
          <p className="text-muted-foreground text-xs">
            {typeLabel} &middot; {matchPct}% match
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
