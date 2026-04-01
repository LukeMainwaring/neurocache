"use client";

import { FolderOpen, Loader2, Plus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import {
  useCreateKnowledgeSource,
  useDeleteKnowledgeSource,
  useKnowledgeSourceDefaults,
  useKnowledgeSources,
  useRetryKnowledgeSource,
  useSyncKnowledgeSource,
} from "@/api/hooks/knowledge-sources";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
import { VaultSourceCard } from "./vault-source-card";

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
          `Already up to date — ${documents_skipped} documents unchanged`,
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
