"use client";

import { ExternalLink } from "lucide-react";
import type { ReactNode } from "react";
import type { WebSource } from "@/lib/types";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog";

type WebSourcesDialogProps = {
  sources: WebSource[];
  trigger: ReactNode;
};

export function WebSourcesDialog({ sources, trigger }: WebSourcesDialogProps) {
  return (
    <Dialog>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Web Sources</DialogTitle>
          <DialogDescription>
            Web pages referenced when answering this question.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          {sources.map((source, index) => (
            <a
              className="flex items-center gap-3 rounded-lg border bg-muted/50 p-3 transition-colors hover:bg-muted"
              href={source.url}
              key={`${source.url}-${index}`}
              rel="noopener noreferrer"
              target="_blank"
            >
              <div className="min-w-0 flex-1">
                <p className="break-all font-medium text-foreground text-sm">
                  {source.title || source.url}
                </p>
                {source.title && (
                  <p className="break-all text-muted-foreground text-xs">
                    {source.url}
                  </p>
                )}
              </div>
              <ExternalLink className="size-4 shrink-0 text-muted-foreground" />
            </a>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
