"use client";

import {
  FolderOpen,
  Loader2,
  Play,
  Plus,
  RefreshCw,
  Trash2,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import type { KnowledgeSourceSchema } from "@/api/generated/types.gen";
import {
  useCreateKnowledgeSource,
  useDeleteKnowledgeSource,
  useKnowledgeSourceDefaults,
  useKnowledgeSources,
  useRetryKnowledgeSource,
  useSyncKnowledgeSource,
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
    // Pre-populate form with defaults from backend config
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
          ? `Connected! ${fileCount} markdown files found`
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
          ? `Connected! ${fileCount} markdown files found`
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
      if (result.documents_created === 0 && result.documents_failed === 0) {
        toast.success(
          `Already up to date — ${result.documents_skipped} documents unchanged`,
        );
      } else {
        toast.success(
          `Synced! ${result.documents_created} new, ${result.documents_skipped} unchanged, ${result.documents_failed} failed`,
        );
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
            <Card key={source.id}>
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
                        disabled={retryingId === source.id}
                        onClick={() => handleRetry(source.id)}
                        size="icon-sm"
                        variant="ghost"
                      >
                        {retryingId === source.id ? (
                          <Loader2 className="size-4 animate-spin" />
                        ) : (
                          <RefreshCw className="size-4" />
                        )}
                      </Button>
                    )}
                    <Button
                      disabled={deletingId === source.id}
                      onClick={() => handleDelete(source.id)}
                      size="icon-sm"
                      variant="ghost"
                    >
                      {deletingId === source.id ? (
                        <Loader2 className="size-4 animate-spin" />
                      ) : (
                        <Trash2 className="size-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </CardHeader>
              {(source.status === "error" ||
                source.status === "connected" ||
                source.status === "syncing") && (
                <CardContent className="pt-0">
                  {source.status === "error" && source.error_message && (
                    <p className="text-destructive text-sm">
                      {source.error_message}
                    </p>
                  )}
                  {(source.status === "connected" ||
                    source.status === "syncing") && (
                    <div className="flex items-center justify-between">
                      <div className="space-y-1">
                        {source.config?.documents_indexed != null ? (
                          <p className="text-muted-foreground text-sm">
                            {Number(source.config.documents_indexed)} documents
                            indexed
                          </p>
                        ) : (
                          !!source.config?.file_count && (
                            <p className="text-muted-foreground text-sm">
                              {Number(source.config.file_count)} markdown files
                              found
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
                        disabled={
                          source.status === "syncing" || syncingId === source.id
                        }
                        onClick={() => handleSync(source.id)}
                        size="sm"
                        variant="outline"
                      >
                        {source.status === "syncing" ||
                        syncingId === source.id ? (
                          <Loader2 className="mr-2 size-4 animate-spin" />
                        ) : (
                          <Play className="size-4" />
                        )}
                        {source.status === "syncing" || syncingId === source.id
                          ? "Syncing..."
                          : "Sync Now"}
                      </Button>
                    </div>
                  )}
                </CardContent>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
