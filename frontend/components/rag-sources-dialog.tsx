"use client";

import { ExternalLink } from "lucide-react";
import type { ReactNode } from "react";
import type { RAGSource } from "@/lib/types";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog";

type RAGSourcesDialogProps = {
  sources: RAGSource[];
  trigger: ReactNode;
};

export function RAGSourcesDialog({ sources, trigger }: RAGSourcesDialogProps) {
  return (
    <Dialog>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Sources</DialogTitle>
          <DialogDescription>
            Information from your knowledge base that was used to answer this
            question.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          {sources.map((source, index) => (
            <div
              className="overflow-hidden rounded-lg border bg-muted/50 p-4"
              key={`${source.path}-${index}`}
            >
              <div className="mb-2 flex items-start justify-between gap-2">
                <div className="flex items-start gap-2">
                  <span className="shrink-0 rounded bg-primary/10 px-1.5 py-0.5 font-medium text-primary text-xs">
                    [{source.source_number ?? index + 1}]
                  </span>
                  {source.obsidian_url ? (
                    <a
                      href={source.obsidian_url}
                      className="line-clamp-2 inline-flex items-center gap-1.5 break-all font-mono text-sm text-primary underline-offset-2 hover:underline"
                    >
                      {source.path}
                      <ExternalLink className="size-3.5 shrink-0" />
                    </a>
                  ) : (
                    <span className="line-clamp-2 break-all font-mono text-foreground text-sm">
                      {source.path}
                    </span>
                  )}
                </div>
                <span className="shrink-0 rounded bg-muted px-2 py-0.5 text-muted-foreground text-xs">
                  {Math.round(source.similarity * 100)}% match
                </span>
              </div>
              {source.section_header && (
                <p className="mb-2 text-muted-foreground text-xs italic">
                  Section: {source.section_header}
                </p>
              )}
              {source.chapter && (
                <p className="mb-2 text-muted-foreground text-xs italic">
                  {source.chapter}, (page: {source.page_number || "N/A"})
                </p>
              )}
              {source.content && (
                <p className="max-h-48 overflow-y-auto break-words text-muted-foreground text-sm">
                  {source.content}
                </p>
              )}
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
