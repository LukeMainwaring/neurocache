"use client";

import { FileUp, Loader2 } from "lucide-react";
import { useState } from "react";
import { useDropzone } from "react-dropzone";
import { toast } from "sonner";
import type { BookPdfPreview } from "@/api/generated/types.gen";
import { usePreviewBook, useUploadBook } from "@/api/hooks/knowledge-sources";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { formatAuthors } from "./utils";

const MAX_PDF_SIZE = 50 * 1024 * 1024; // 50MB, matches backend

export function UploadBookDialog({
  sourceId,
  open,
  onOpenChange,
}: {
  sourceId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<BookPdfPreview | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editAuthor, setEditAuthor] = useState("");

  const previewMutation = usePreviewBook(sourceId);
  const uploadMutation = useUploadBook(sourceId);

  async function onDrop(acceptedFiles: File[]) {
    const file = acceptedFiles[0];
    if (!file) {
      return;
    }
    setSelectedFile(file);
    setPreview(null);
    previewMutation.reset();

    try {
      const result = await previewMutation.previewBook(file);
      setPreview(result);
      setEditTitle(result.title);
      setEditAuthor(result.author ? formatAuthors(result.author) : "");
    } catch {
      toast.error("Failed to parse PDF");
    }
  }

  const { getRootProps, getInputProps, isDragActive, fileRejections } =
    useDropzone({
      onDrop,
      accept: { "application/pdf": [".pdf"] },
      maxSize: MAX_PDF_SIZE,
      maxFiles: 1,
      disabled: previewMutation.isPending,
    });

  function reset() {
    setSelectedFile(null);
    setPreview(null);
    setEditTitle("");
    setEditAuthor("");
    previewMutation.reset();
    uploadMutation.reset();
  }

  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen) {
      reset();
    }
    onOpenChange(nextOpen);
  }

  async function handleUpload() {
    if (!selectedFile || !editTitle.trim()) {
      return;
    }

    try {
      await uploadMutation.uploadBook(
        selectedFile,
        editTitle.trim(),
        editAuthor.trim() || undefined
      );
      toast.success("Book uploaded! Ingestion started in the background.");
      handleOpenChange(false);
    } catch {
      toast.error("Failed to upload book");
    }
  }

  const rejectionMessage = fileRejections[0]?.errors[0]?.message;

  return (
    <Dialog onOpenChange={handleOpenChange} open={open}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Upload Book PDF</DialogTitle>
          <DialogDescription>
            Upload a PDF to add it to your Books collection.
          </DialogDescription>
        </DialogHeader>

        <div className="min-w-0 space-y-4 py-4">
          {!preview && (
            <div
              {...getRootProps()}
              className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
                isDragActive
                  ? "border-primary bg-primary/5"
                  : "border-muted-foreground/25 hover:border-muted-foreground/50"
              } ${previewMutation.isPending ? "pointer-events-none opacity-50" : ""}`}
            >
              <input {...getInputProps()} />
              {previewMutation.isPending ? (
                <>
                  <Loader2 className="mb-2 size-8 animate-spin text-muted-foreground" />
                  <p className="text-muted-foreground text-sm">
                    Parsing PDF metadata...
                  </p>
                </>
              ) : (
                <>
                  <FileUp className="mb-2 size-8 text-muted-foreground" />
                  <p className="text-sm">
                    {isDragActive
                      ? "Drop your PDF here"
                      : "Drag & drop a PDF, or click to browse"}
                  </p>
                  <p className="mt-1 text-muted-foreground text-xs">
                    PDF up to 50MB
                  </p>
                </>
              )}
            </div>
          )}

          {rejectionMessage && (
            <p className="text-destructive text-sm">{rejectionMessage}</p>
          )}

          {previewMutation.isError && (
            <p className="text-destructive text-sm">
              Could not parse this PDF. It may be encrypted or contain no
              extractable text.
            </p>
          )}

          {preview && selectedFile && (
            <>
              <div className="flex items-center gap-2 overflow-hidden rounded-md border bg-muted/50 px-3 py-2">
                <FileUp className="size-4 shrink-0 text-muted-foreground" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm">{selectedFile.name}</p>
                  <p className="text-muted-foreground text-xs">
                    {preview.page_count} pages
                  </p>
                </div>
                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    reset();
                  }}
                  size="sm"
                  variant="ghost"
                >
                  Change
                </Button>
              </div>

              <div className="space-y-2">
                <label
                  className="font-medium text-sm leading-none"
                  htmlFor="book-title"
                >
                  Title
                </label>
                <Input
                  id="book-title"
                  onChange={(e) => setEditTitle(e.target.value)}
                  placeholder="Book title"
                  value={editTitle}
                />
              </div>

              <div className="space-y-2">
                <label
                  className="font-medium text-sm leading-none"
                  htmlFor="book-author"
                >
                  Author
                </label>
                <Input
                  id="book-author"
                  onChange={(e) => setEditAuthor(e.target.value)}
                  placeholder="Author (optional)"
                  value={editAuthor}
                />
              </div>
            </>
          )}
        </div>

        <DialogFooter>
          <Button onClick={() => handleOpenChange(false)} variant="outline">
            Cancel
          </Button>
          <Button
            disabled={!preview || !editTitle.trim() || uploadMutation.isPending}
            onClick={handleUpload}
          >
            {uploadMutation.isPending && (
              <Loader2 className="mr-2 size-4 animate-spin" />
            )}
            Upload
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
