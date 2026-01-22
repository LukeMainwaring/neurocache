"use client";

import { FolderOpen, Loader2, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

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
import {
  createKnowledgeSource,
  deleteKnowledgeSource,
  fetchKnowledgeSourceDefaults,
  fetchKnowledgeSources,
  type KnowledgeSource,
  type KnowledgeSourceDefaults,
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

  // Defaults from backend config
  const [defaults, setDefaults] = useState<
    KnowledgeSourceDefaults["obsidian"] | null
  >(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [sourcesData, defaultsData] = await Promise.all([
          fetchKnowledgeSources(),
          fetchKnowledgeSourceDefaults(),
        ]);
        setSources(sourcesData);
        setDefaults(defaultsData.obsidian);
      } catch (error) {
        console.error("Failed to load knowledge sources:", error);
        toast.error("Failed to load knowledge sources");
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  function resetForm() {
    setName("");
    setFilePath("");
  }

  function handleOpenDialog() {
    // Pre-populate form with defaults from backend config
    if (defaults) {
      setName(defaults.name);
      setFilePath(defaults.file_path || "");
    }
    setIsDialogOpen(true);
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
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
