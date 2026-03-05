"use client";

import { Loader2, Play, RefreshCw, Trash2 } from "lucide-react";
import { useState } from "react";
import type { KnowledgeSourceSchema } from "@/api/generated/types.gen";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { BookList } from "./book-list";
import { UploadBookDialog } from "./upload-book-dialog";
import { formatRelativeTime, STATUS_COLORS, STATUS_LABELS } from "./utils";

export function VaultSourceCard({
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
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const isConnected =
    source.status === "connected" || source.status === "syncing";
  const hasSynced = !!source.last_synced_at;

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
              <BookList
                onUploadClick={() => setUploadDialogOpen(true)}
                sourceId={source.id}
              />
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
