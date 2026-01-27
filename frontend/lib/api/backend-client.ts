/**
 * Backend API client for Neurocache backend.
 *
 * Contains server-side utilities that can't be replaced by TanStack Query hooks.
 */

const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface Message {
  id: string;
  role: "user" | "assistant";
  parts: Array<{
    type: "text";
    text: string;
  }>;
}

export interface ThreadMessagesResponse {
  thread_id: string;
  messages: Message[];
}

/**
 * Get all messages for a specific thread.
 *
 * Used by server components for initial data fetching.
 */
export async function getThreadMessages(threadId: string): Promise<Message[]> {
  const response = await fetch(`${API_URL}/api/threads/${threadId}/messages`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!response.ok) {
    if (response.status === 404) {
      // Thread doesn't exist yet - return empty array
      return [];
    }
    throw new Error(`Failed to fetch thread messages: ${response.statusText}`);
  }

  const data: ThreadMessagesResponse = await response.json();
  return data.messages;
}
