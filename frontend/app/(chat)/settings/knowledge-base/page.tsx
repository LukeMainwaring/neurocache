"use client";

import {
  BookOpen,
  ChevronDown,
  ChevronUp,
  FileUp,
  FolderOpen,
  Loader2,
  Play,
  Plus,
  RefreshCw,
  Trash2,
  Upload,
} from "lucide-react";
import { useState } from "react";
import { useDropzone } from "react-dropzone";
import { toast } from "sonner";
import type {
  BookPdfPreview,
  BookSchema,
  KnowledgeSourceSchema,
} from "@/api/generated/types.gen";
import {
  useCreateKnowledgeSource,
  useDeleteKnowledgeSource,
  useKnowledgeSourceBooks,
  useKnowledgeSourceDefaults,
  useKnowledgeSources,
  usePreviewBook,
  useRetryKnowledgeSource,
  useSyncKnowledgeSource,
  useUploadBook,
} from "@/api/hooks/knowledge-sources";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

function formatRelativeTime(dateString: string): string {
  const now = Date.now();
  const then = new Date(dateString).getTime();
  const seconds = Math.floor((now - then) / 1000);

  if (seconds < 60) {
    return "just now";
  }
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  }
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

const STATUS_LABELS: Record<KnowledgeSourceSchema["status"], string> = {
  pending: "Pending",
  connected: "Connected",
  syncing: "Syncing",
  error: "Error",
};

const STATUS_COLORS: Record<KnowledgeSourceSchema["status"], string> = {
  pending: "bg-yellow-500",
  connected: "bg-green-500",
  syncing: "bg-blue-500",
  error: "bg-red-500",
};

const DOC_STATUS_COLORS: Record<string, string> = {
  indexed: "bg-green-500",
  processing: "bg-blue-500",
  pending: "bg-yellow-500",
  error: "bg-red-500",
  deleted: "bg-gray-400",
};

function formatAuthors(raw: string): string {
  return raw
    .split(";")
    .map((s) => s.trim())
    .filter(Boolean)
    .join(", ");
}

function BookRow({ book }: { book: BookSchema }) {
  const noteDoc = book.documents.find((d) => d.content_type === "book_note");
  const pdfDoc = book.documents.find((d) => d.content_type === "book_source");

  return (
    <div className="flex items-start justify-between rounded-md px-2 py-1.5 transition-colors hover:bg-muted/50">
      <div className="min-w-0 flex-1 space-y-0.5">
        <p className="truncate font-medium text-sm leading-none">
          {book.title}
        </p>
        {book.author && (
          <p className="truncate text-muted-foreground text-xs">
            {formatAuthors(book.author)}
          </p>
        )}
      </div>
      <div className="ml-3 flex shrink-0 items-center gap-1.5">
        {noteDoc && (
          <span className="inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-xs">
            <span
              className={`size-1.5 rounded-full ${DOC_STATUS_COLORS[noteDoc.status] ?? "bg-gray-400"}`}
            />
            Notes
          </span>
        )}
        {pdfDoc && (
          <span className="inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-xs">
            <span
              className={`size-1.5 rounded-full ${DOC_STATUS_COLORS[pdfDoc.status] ?? "bg-gray-400"}`}
            />
            PDF
          </span>
        )}
      </div>
    </div>
  );
}

const MAX_PDF_SIZE = 50 * 1024 * 1024; // 50MB, matches backend

function UploadBookDialog({
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

function VaultSourceCard({
  source,
  onRetry,
  onDelete,
  onSync,
  isRetrying,
  isDeleting,
  isSyncing,
}: {
  source: KnowledgeSourceSchema;
  onRetry: (id: string) => void;
  onDelete: (id: string) => void;
  onSync: (id: string) => void;
  isRetrying: boolean;
  isDeleting: boolean;
  isSyncing: boolean;
}) {
  const [booksExpanded, setBooksExpanded] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const isConnected =
    source.status === "connected" || source.status === "syncing";

  const hasSynced = !!source.last_synced_at;
  const { data: booksData, isLoading: isLoadingBooks } =
    useKnowledgeSourceBooks(source.id, isConnected && hasSynced);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-base">{source.name}</CardTitle>
            <CardDescription className="font-mono text-xs">
              {source.file_path}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5">
              <div
                className={`size-2 rounded-full ${STATUS_COLORS[source.status]}`}
              />
              <span className="text-muted-foreground text-xs">
                {STATUS_LABELS[source.status]}
              </span>
            </div>
            {source.status === "error" && (
              <Button
                disabled={isRetrying}
                onClick={() => onRetry(source.id)}
                size="icon-sm"
                variant="ghost"
              >
                {isRetrying ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <RefreshCw className="size-4" />
                )}
              </Button>
            )}
            <Button
              disabled={isDeleting}
              onClick={() => onDelete(source.id)}
              size="icon-sm"
              variant="ghost"
            >
              {isDeleting ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Trash2 className="size-4" />
              )}
            </Button>
          </div>
        </div>
      </CardHeader>

      {source.status === "error" && source.error_message && (
        <CardContent className="pt-0">
          <p className="text-destructive text-sm">{source.error_message}</p>
        </CardContent>
      )}

      {isConnected && (
        <CardContent className="space-y-3 pt-0">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              {source.config?.documents_indexed != null ? (
                <p className="text-muted-foreground text-sm">
                  {Number(source.config.documents_indexed)} documents indexed
                </p>
              ) : (
                !!source.config?.file_count && (
                  <p className="text-muted-foreground text-sm">
                    {Number(source.config.file_count)} files found
                  </p>
                )
              )}
              <p className="text-muted-foreground text-xs">
                {source.last_synced_at
                  ? `Last synced ${formatRelativeTime(source.last_synced_at)}`
                  : "Never synced"}
              </p>
            </div>
            <Button
              disabled={source.status === "syncing" || isSyncing}
              onClick={() => onSync(source.id)}
              size="sm"
              variant="outline"
            >
              {source.status === "syncing" || isSyncing ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Play className="size-4" />
              )}
              {source.status === "syncing" || isSyncing
                ? "Syncing..."
                : "Sync Now"}
            </Button>
          </div>

          {hasSynced && (
            <>
              <div className="flex items-center gap-1">
                <Button
                  onClick={() => setBooksExpanded((prev) => !prev)}
                  size="sm"
                  variant="ghost"
                >
                  <BookOpen className="size-3.5" />
                  Books
                  {booksData && (
                    <span className="text-xs">({booksData.books.length})</span>
                  )}
                  {booksExpanded ? (
                    <ChevronUp className="size-3.5" />
                  ) : (
                    <ChevronDown className="size-3.5" />
                  )}
                </Button>
                <Button
                  onClick={() => setUploadDialogOpen(true)}
                  size="sm"
                  variant="ghost"
                >
                  <Upload className="size-3.5" />
                  Upload PDF
                </Button>
              </div>

              {booksExpanded && (
                <div className="max-h-64 space-y-0.5 overflow-y-auto">
                  {isLoadingBooks ? (
                    <div className="flex items-center justify-center py-4">
                      <Loader2 className="size-4 animate-spin text-muted-foreground" />
                    </div>
                  ) : booksData?.books.length === 0 ? (
                    <p className="py-2 text-center text-muted-foreground text-xs">
                      No books found. Add PDFs or notes to Books/ in your vault.
                    </p>
                  ) : (
                    booksData?.books.map((book) => (
                      <BookRow book={book} key={book.folder_path} />
                    ))
                  )}
                </div>
              )}

              <UploadBookDialog
                onOpenChange={setUploadDialogOpen}
                open={uploadDialogOpen}
                sourceId={source.id}
              />
            </>
          )}
        </CardContent>
      )}
    </Card>
  );
}

export default function KnowledgeBasePage() {
  const { data: sourcesData, isLoading: isLoadingSources } =
    useKnowledgeSources();
  const { data: defaultsData } = useKnowledgeSourceDefaults();
  const { createSource, isPending: isCreating } = useCreateKnowledgeSource();
  const { deleteSource } = useDeleteKnowledgeSource();
  const { retrySource } = useRetryKnowledgeSource();
  const { syncSource } = useSyncKnowledgeSource();

  const sources = sourcesData?.sources ?? [];
  const defaults = defaultsData?.obsidian;

  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [syncingId, setSyncingId] = useState<string | null>(null);

  // Form state
  const [name, setName] = useState("");
  const [filePath, setFilePath] = useState("");

  function resetForm() {
    setName("");
    setFilePath("");
  }

  function handleOpenDialog() {
    if (defaults) {
      setName(defaults.name ?? "");
      setFilePath(defaults.file_path ?? "");
    }
    setIsDialogOpen(true);
  }

  async function handleCreate() {
    if (!name.trim() || !filePath.trim()) {
      toast.error("Please fill in all fields");
      return;
    }

    try {
      const result = await createSource({
        name: name.trim(),
        source_type: "obsidian",
        file_path: filePath.trim(),
      });
      setIsDialogOpen(false);
      resetForm();
      if (result.status === "error") {
        toast.error(result.error_message ?? "Failed to connect vault");
      } else {
        const fileCount = result.config?.file_count as number | undefined;
        const message = fileCount
          ? `Connected! ${fileCount} files found`
          : "Knowledge source connected";
        toast.success(message);
      }
    } catch (error) {
      console.error("Failed to create knowledge source:", error);
      toast.error("Failed to add knowledge source");
    }
  }

  async function handleRetry(id: string) {
    setRetryingId(id);
    try {
      const result = await retrySource(id);
      if (result.status === "error") {
        toast.error(result.error_message ?? "Validation failed");
      } else {
        const fileCount = result.config?.file_count as number | undefined;
        const message = fileCount
          ? `Connected! ${fileCount} files found`
          : "Knowledge source connected";
        toast.success(message);
      }
    } catch (error) {
      console.error("Failed to retry knowledge source:", error);
      toast.error("Failed to retry validation");
    } finally {
      setRetryingId(null);
    }
  }

  async function handleSync(id: string) {
    setSyncingId(id);
    try {
      const result = await syncSource(id);
      const {
        documents_created,
        documents_updated,
        documents_deleted,
        documents_skipped,
        documents_failed,
      } = result;

      if (
        documents_created === 0 &&
        documents_updated === 0 &&
        documents_deleted === 0 &&
        documents_failed === 0
      ) {
        toast.success(
          `Already up to date — ${documents_skipped} documents unchanged`
        );
      } else {
        const parts: string[] = [];
        if (documents_created > 0) {
          parts.push(`${documents_created} new`);
        }
        if (documents_updated > 0) {
          parts.push(`${documents_updated} updated`);
        }
        if (documents_deleted > 0) {
          parts.push(`${documents_deleted} removed`);
        }
        if (documents_skipped > 0) {
          parts.push(`${documents_skipped} unchanged`);
        }
        if (documents_failed > 0) {
          parts.push(`${documents_failed} failed`);
        }
        toast.success(`Synced! ${parts.join(", ")}`);
      }
    } catch (error) {
      console.error("Failed to sync knowledge source:", error);
      toast.error("Failed to sync knowledge source");
    } finally {
      setSyncingId(null);
    }
  }

  async function handleDelete(id: string) {
    setDeletingId(id);
    try {
      await deleteSource(id);
      toast.success("Knowledge source removed");
    } catch (error) {
      console.error("Failed to delete knowledge source:", error);
      toast.error("Failed to remove knowledge source");
    } finally {
      setDeletingId(null);
    }
  }

  if (isLoadingSources) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-semibold text-lg">Knowledge Base</h2>
          <p className="text-muted-foreground text-sm">
            Connect your knowledge sources to enhance AI responses with your
            personal context.
          </p>
        </div>

        <Dialog onOpenChange={setIsDialogOpen} open={isDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={handleOpenDialog}>
              <Plus className="mr-2 size-4" />
              Add Source
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Connect Obsidian Vault</DialogTitle>
              <DialogDescription>
                Enter the path to your Obsidian vault folder on your local
                filesystem.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label
                  className="font-medium text-sm leading-none"
                  htmlFor="name"
                >
                  Name
                </label>
                <Input
                  id="name"
                  onChange={(e) => setName(e.target.value)}
                  placeholder="My Obsidian Vault"
                  value={name}
                />
                <p className="text-muted-foreground text-xs">
                  A friendly name to identify this knowledge source
                </p>
              </div>

              <div className="space-y-2">
                <label
                  className="font-medium text-sm leading-none"
                  htmlFor="file-path"
                >
                  Vault Path
                </label>
                <Input
                  id="file-path"
                  onChange={(e) => setFilePath(e.target.value)}
                  placeholder="/Users/you/Documents/ObsidianVault"
                  value={filePath}
                />
                <p className="text-muted-foreground text-xs">
                  The absolute path to your Obsidian vault folder
                </p>
              </div>
            </div>

            <DialogFooter>
              <Button
                disabled={isCreating}
                onClick={() => setIsDialogOpen(false)}
                variant="outline"
              >
                Cancel
              </Button>
              <Button disabled={isCreating} onClick={handleCreate}>
                {isCreating && <Loader2 className="mr-2 size-4 animate-spin" />}
                Connect
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {sources.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <FolderOpen className="mb-4 size-12 text-muted-foreground" />
            <h3 className="mb-1 font-medium">No knowledge sources connected</h3>
            <p className="mb-4 text-muted-foreground text-sm">
              Connect your Obsidian vault to get started
            </p>
            <Button onClick={handleOpenDialog} variant="outline">
              <Plus className="mr-2 size-4" />
              Add Your First Source
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {sources.map((source) => (
            <VaultSourceCard
              isDeleting={deletingId === source.id}
              isRetrying={retryingId === source.id}
              isSyncing={syncingId === source.id}
              key={source.id}
              onDelete={handleDelete}
              onRetry={handleRetry}
              onSync={handleSync}
              source={source}
            />
          ))}
        </div>
      )}
    </div>
  );
}
