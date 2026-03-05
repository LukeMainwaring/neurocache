import type { KnowledgeSourceSchema } from "@/api/generated/types.gen";

export function formatRelativeTime(dateString: string): string {
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

export function formatAuthors(raw: string): string {
  return raw
    .split(";")
    .map((s) => s.trim())
    .filter(Boolean)
    .join(", ");
}

export const STATUS_LABELS: Record<KnowledgeSourceSchema["status"], string> = {
  pending: "Pending",
  connected: "Connected",
  syncing: "Syncing",
  error: "Error",
};

export const STATUS_COLORS: Record<KnowledgeSourceSchema["status"], string> = {
  pending: "bg-yellow-500",
  connected: "bg-green-500",
  syncing: "bg-blue-500",
  error: "bg-red-500",
};

export const DOC_STATUS_COLORS: Record<string, string> = {
  indexed: "bg-green-500",
  processing: "bg-blue-500",
  pending: "bg-yellow-500",
  error: "bg-red-500",
  deleted: "bg-gray-400",
};
