"use client";

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
              className="rounded-lg border bg-muted/50 p-4"
              key={`${source.path}-${index}`}
            >
              <div className="mb-2 flex items-start justify-between gap-2">
                <span className="line-clamp-2 break-all font-mono text-foreground text-sm">
                  {source.path}
                </span>
                <span className="shrink-0 rounded bg-muted px-2 py-0.5 text-muted-foreground text-xs">
                  {Math.round(source.similarity * 100)}% match
                </span>
              </div>
              {source.content && (
                <p className="max-h-48 overflow-y-auto text-muted-foreground text-sm">
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
