"use client";

import { useEffect, useState } from "react";
import { FolderOpen, Loader2, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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
import {
  createKnowledgeSource,
  deleteKnowledgeSource,
  fetchKnowledgeSources,
  type KnowledgeSource,
} from "@/lib/api/backend-client";

const STATUS_LABELS: Record<KnowledgeSource["status"], string> = {
  pending: "Pending",
  connected: "Connected",
  syncing: "Syncing",
  error: "Error",
};

const STATUS_COLORS: Record<KnowledgeSource["status"], string> = {
  pending: "bg-yellow-500",
  connected: "bg-green-500",
  syncing: "bg-blue-500",
  error: "bg-red-500",
};

export default function KnowledgeBasePage() {
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Form state
  const [name, setName] = useState("");
  const [filePath, setFilePath] = useState("");

  useEffect(() => {
    async function loadSources() {
      try {
        const data = await fetchKnowledgeSources();
        setSources(data);
      } catch (error) {
        console.error("Failed to load knowledge sources:", error);
        toast.error("Failed to load knowledge sources");
      } finally {
        setIsLoading(false);
      }
    }
    loadSources();
  }, []);

  function resetForm() {
    setName("");
    setFilePath("");
  }

  async function handleCreate() {
    if (!name.trim() || !filePath.trim()) {
      toast.error("Please fill in all fields");
      return;
    }

    setIsCreating(true);
    try {
      const newSource = await createKnowledgeSource({
        source_type: "obsidian",
        name: name.trim(),
        file_path: filePath.trim(),
      });
      setSources((prev) => [newSource, ...prev]);
      setIsDialogOpen(false);
      resetForm();
      toast.success("Knowledge source added");
    } catch (error) {
      console.error("Failed to create knowledge source:", error);
      toast.error("Failed to add knowledge source");
    } finally {
      setIsCreating(false);
    }
  }

  async function handleDelete(id: string) {
    setDeletingId(id);
    try {
      await deleteKnowledgeSource(id);
      setSources((prev) => prev.filter((s) => s.id !== id));
      toast.success("Knowledge source removed");
    } catch (error) {
      console.error("Failed to delete knowledge source:", error);
      toast.error("Failed to remove knowledge source");
    } finally {
      setDeletingId(null);
    }
  }

  if (isLoading) {
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
          <h2 className="text-lg font-semibold">Knowledge Base</h2>
          <p className="text-sm text-muted-foreground">
            Connect your knowledge sources to enhance AI responses with your personal context.
          </p>
        </div>

        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="size-4 mr-2" />
              Add Source
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Connect Obsidian Vault</DialogTitle>
              <DialogDescription>
                Enter the path to your Obsidian vault folder on your local filesystem.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label htmlFor="name" className="text-sm font-medium leading-none">
                  Name
                </label>
                <Input
                  id="name"
                  placeholder="My Obsidian Vault"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  A friendly name to identify this knowledge source
                </p>
              </div>

              <div className="space-y-2">
                <label htmlFor="file-path" className="text-sm font-medium leading-none">
                  Vault Path
                </label>
                <Input
                  id="file-path"
                  placeholder="/Users/you/Documents/ObsidianVault"
                  value={filePath}
                  onChange={(e) => setFilePath(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  The absolute path to your Obsidian vault folder
                </p>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setIsDialogOpen(false)} disabled={isCreating}>
                Cancel
              </Button>
              <Button onClick={handleCreate} disabled={isCreating}>
                {isCreating && <Loader2 className="size-4 animate-spin mr-2" />}
                Connect
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {sources.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <FolderOpen className="size-12 text-muted-foreground mb-4" />
            <h3 className="font-medium mb-1">No knowledge sources connected</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Connect your Obsidian vault to get started
            </p>
            <Button variant="outline" onClick={() => setIsDialogOpen(true)}>
              <Plus className="size-4 mr-2" />
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
                      <div className={`size-2 rounded-full ${STATUS_COLORS[source.status]}`} />
                      <span className="text-xs text-muted-foreground">
                        {STATUS_LABELS[source.status]}
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => handleDelete(source.id)}
                      disabled={deletingId === source.id}
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
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
