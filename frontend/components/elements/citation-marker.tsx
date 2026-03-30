"use client";

import type { RAGSource } from "@/lib/types";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog";
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
    <Dialog>
      <TooltipProvider>
        <Tooltip>
          <DialogTrigger asChild>
            <TooltipTrigger asChild>
              <sup className="mx-0.5 inline-flex cursor-pointer rounded bg-primary/10 px-1 py-0.5 text-[10px] leading-none text-primary transition-colors hover:bg-primary/20">
                [{number}]
              </sup>
            </TooltipTrigger>
          </DialogTrigger>
          <TooltipContent side="top" className="max-w-xs">
            <p className="font-mono text-xs">{source.path}</p>
            <p className="text-muted-foreground text-xs">
              {typeLabel} &middot; {matchPct}% match
            </p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
      <DialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span className="shrink-0 rounded bg-primary/10 px-1.5 py-0.5 font-medium text-primary text-xs">
              [{number}]
            </span>
            <span className="break-all font-mono text-sm">{source.path}</span>
          </DialogTitle>
          <DialogDescription>
            {typeLabel} &middot; {matchPct}% match
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          {source.section_header && (
            <p className="text-muted-foreground text-xs italic">
              Section: {source.section_header}
            </p>
          )}
          {source.chapter && (
            <p className="text-muted-foreground text-xs italic">
              {source.chapter}
              {source.page_number ? ` (page: ${source.page_number})` : ""}
            </p>
          )}
          {source.content && (
            <p className="max-h-64 overflow-y-auto break-words text-muted-foreground text-sm">
              {source.content}
            </p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
