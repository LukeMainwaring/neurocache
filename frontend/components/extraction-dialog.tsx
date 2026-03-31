"use client";

import { ExternalLink, Loader2, Pencil, Sparkles } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import {
  useExtractionConfirm,
  useExtractionPreview,
  useExtractionStatus,
} from "@/api/hooks/extractions";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Response } from "./elements/response";

type ExtractionDialogProps = {
  threadId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

type DialogState = "loading" | "preview" | "saving" | "success" | "empty";

export function ExtractionDialog({
  threadId,
  open,
  onOpenChange,
}: ExtractionDialogProps) {
  const [state, setState] = useState<DialogState>("loading");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [savedPath, setSavedPath] = useState("");
  const [obsidianUrl, setObsidianUrl] = useState("");
  const hasTriggered = useRef(false);

  const { previewExtraction } = useExtractionPreview();
  const { confirmExtraction } = useExtractionConfirm();
  const { data: statusData } = useExtractionStatus(open ? threadId : null);

  // Stable refs for callbacks used in the effect
  const previewRef = useRef(previewExtraction);
  previewRef.current = previewExtraction;
  const onOpenChangeRef = useRef(onOpenChange);
  onOpenChangeRef.current = onOpenChange;

  const hasExistingExtractions =
    statusData && statusData.extractions.length > 0;

  const runPreview = useCallback((tid: string) => {
    setState("loading");
    previewRef
      .current(tid)
      .then((result) => {
        if (!result.content.trim() || !result.title.trim()) {
          setState("empty");
          return;
        }
        setTitle(result.title);
        setContent(result.content);
        setState("preview");
      })
      .catch(() => {
        toast.error("Failed to analyze conversation");
        onOpenChangeRef.current(false);
      });
  }, []);

  useEffect(() => {
    if (open && !hasTriggered.current) {
      hasTriggered.current = true;
      runPreview(threadId);
    }
    if (!open) {
      hasTriggered.current = false;
      setState("loading");
      setTitle("");
      setContent("");
      setIsEditing(false);
      setSavedPath("");
      setObsidianUrl("");
    }
  }, [open, threadId, runPreview]);

  const handleSave = async () => {
    setState("saving");
    try {
      const result = await confirmExtraction(threadId, title, content);
      setSavedPath(result.relative_path);
      setObsidianUrl(result.obsidian_url);
      setState("success");
      toast.success("Note saved to your vault");
    } catch {
      toast.error("Failed to save note");
      setState("preview");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-hidden sm:max-w-2xl flex flex-col">
        {/* Loading state */}
        {state === "loading" && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Sparkles className="size-4" />
                Extract Insights
              </DialogTitle>
              <DialogDescription>
                Analyzing conversation for reusable knowledge...
              </DialogDescription>
            </DialogHeader>
            <div className="flex items-center justify-center py-12">
              <Loader2 className="size-6 animate-spin text-muted-foreground" />
            </div>
          </>
        )}

        {/* Empty state */}
        {state === "empty" && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Sparkles className="size-4" />
                Extract Insights
              </DialogTitle>
            </DialogHeader>
            <div className="py-8 text-center text-muted-foreground text-sm">
              No extractable insights found in this conversation.
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Close
              </Button>
            </DialogFooter>
          </>
        )}

        {/* Preview state */}
        {state === "preview" && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Sparkles className="size-4" />
                Extract Insights
              </DialogTitle>
              <DialogDescription>
                Review the extracted note before saving to your vault.
                {hasExistingExtractions && (
                  <span className="mt-1 block text-amber-600 dark:text-amber-400">
                    You've already extracted from this conversation. This will
                    create an additional note.
                  </span>
                )}
              </DialogDescription>
            </DialogHeader>

            {/* Title */}
            <div className="space-y-1">
              <label htmlFor="extraction-title" className="font-medium text-sm">
                Title
              </label>
              <input
                id="extraction-title"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>

            {/* Content */}
            <div className="min-h-0 flex-1 space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-medium text-sm">Content</span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 gap-1 text-xs"
                  onClick={() => setIsEditing(!isEditing)}
                >
                  <Pencil className="size-3" />
                  {isEditing ? "Preview" : "Edit"}
                </Button>
              </div>
              <div className="max-h-[40vh] overflow-y-auto rounded-md border p-4">
                {isEditing ? (
                  <textarea
                    className="min-h-[200px] w-full resize-none bg-transparent font-mono text-sm outline-none"
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                  />
                ) : (
                  <Response className="prose-sm">{content}</Response>
                )}
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={!title.trim()}>
                Save to Vault
              </Button>
            </DialogFooter>
          </>
        )}

        {/* Saving state */}
        {state === "saving" && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Sparkles className="size-4" />
                Saving to Vault
              </DialogTitle>
              <DialogDescription>
                Writing note and indexing for search...
              </DialogDescription>
            </DialogHeader>
            <div className="flex items-center justify-center py-12">
              <Loader2 className="size-6 animate-spin text-muted-foreground" />
            </div>
          </>
        )}

        {/* Success state */}
        {state === "success" && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Sparkles className="size-4" />
                Note Saved
              </DialogTitle>
              <DialogDescription>
                Your note has been saved and indexed for future retrieval.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3 py-4">
              <p className="font-mono text-muted-foreground text-sm">
                {savedPath}
              </p>
              {obsidianUrl && (
                <a
                  href={obsidianUrl}
                  className="inline-flex items-center gap-1.5 text-primary text-sm underline-offset-2 hover:underline"
                >
                  Open in Obsidian
                  <ExternalLink className="size-3.5" />
                </a>
              )}
            </div>
            <DialogFooter>
              <Button onClick={() => onOpenChange(false)}>Done</Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
