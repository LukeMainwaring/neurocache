/**
 * Backend API client for Neurocache backend.
 *
 * Provides functions to interact with the FastAPI backend for:
 * - Listing threads
 * - Loading thread messages
 * - Deleting threads
 * - Streaming chat responses
 */

const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface ThreadSummary {
  id: string;
  thread_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ThreadListResponse {
  threads: ThreadSummary[];
}

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
 * Get list of all threads for the current user.
 * Sorted by most recently updated first.
 */
export async function getThreads(): Promise<ThreadSummary[]> {
  const response = await fetch(`${API_URL}/api/threads`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include", // Include cookies for auth
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch threads: ${response.statusText}`);
  }

  const data: ThreadListResponse = await response.json();
  return data.threads;
}

/**
 * Get all messages for a specific thread.
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

/**
 * Delete a thread and all its messages.
 */
export async function deleteThread(threadId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/threads/${threadId}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Failed to delete thread: ${response.statusText}`);
  }
}

/**
 * Get the chat stream URL for a thread.
 * Used by Vercel AI SDK's useChat hook.
 */
export function getChatStreamUrl(): string {
  return `${API_URL}/api/chat/stream`;
}

// User API
export interface User {
  id: string;
  email: string;
  name: string | null;
  created_at: string;
  updated_at: string;
  custom_instructions: string | null;
  nickname: string | null;
  occupation: string | null;
  about_you: string | null;
}

export interface UserPersonalizationUpdate {
  custom_instructions?: string | null;
  nickname?: string | null;
  occupation?: string | null;
  about_you?: string | null;
}

/**
 * Get the current user's profile.
 */
export async function fetchCurrentUser(): Promise<User> {
  const response = await fetch(`${API_URL}/api/users/myself`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch user: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Update the current user's personalization settings.
 */
export async function updateUserPersonalization(
  data: UserPersonalizationUpdate
): Promise<User> {
  const response = await fetch(`${API_URL}/api/users/myself/personalization`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`Failed to update user: ${response.statusText}`);
  }

  return response.json();
}

// Knowledge Source API
export interface KnowledgeSource {
  id: string;
  user_id: string;
  source_type: "obsidian" | "notion" | "local_folder";
  name: string;
  file_path: string | null;
  status: "pending" | "connected" | "syncing" | "error";
  last_synced_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeSourceCreate {
  source_type: "obsidian" | "notion" | "local_folder";
  name: string;
  file_path?: string;
}

/**
 * Get all knowledge sources for the current user.
 */
export async function fetchKnowledgeSources(): Promise<KnowledgeSource[]> {
  const response = await fetch(`${API_URL}/api/knowledge-sources`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(
      `Failed to fetch knowledge sources: ${response.statusText}`
    );
  }

  const data = await response.json();
  return data.sources;
}

/**
 * Create a new knowledge source.
 */
export async function createKnowledgeSource(
  data: KnowledgeSourceCreate
): Promise<KnowledgeSource> {
  const response = await fetch(`${API_URL}/api/knowledge-sources`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(
      `Failed to create knowledge source: ${response.statusText}`
    );
  }

  return response.json();
}

/**
 * Delete a knowledge source.
 */
export async function deleteKnowledgeSource(id: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/knowledge-sources/${id}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(
      `Failed to delete knowledge source: ${response.statusText}`
    );
  }
}

export interface KnowledgeSourceDefaults {
  obsidian: {
    name: string;
    file_path: string | null;
  };
}

/**
 * Fetch default values for creating a knowledge source.
 */
export async function fetchKnowledgeSourceDefaults(): Promise<KnowledgeSourceDefaults> {
  const response = await fetch(`${API_URL}/api/knowledge-sources/defaults`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(
      `Failed to fetch knowledge source defaults: ${response.statusText}`
    );
  }

  return response.json();
}
