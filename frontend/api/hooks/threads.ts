import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ChatMessage } from "@/lib/types";
import {
  deleteThreadMutation,
  listThreadsOptions,
  listThreadsQueryKey,
} from "../generated/@tanstack/react-query.gen";
import { getThreadMessages as getThreadMessagesApi } from "../generated/sdk.gen";

// Ensure client is configured with baseURL
import "../client";

export const useThreads = () => {
  return useQuery(listThreadsOptions());
};

export const useDeleteThread = () => {
  const queryClient = useQueryClient();
  const mutationResult = useMutation({
    ...deleteThreadMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listThreadsQueryKey() });
    },
  });

  const deleteThread = (threadId: string) => {
    return mutationResult.mutateAsync({ path: { thread_id: threadId } });
  };

  return {
    deleteThread,
    ...mutationResult,
  };
};

/**
 * Get all messages for a specific thread.
 *
 * Plain async function for server components (can't use hooks).
 */
export async function getThreadMessages(
  threadId: string,
): Promise<ChatMessage[]> {
  const response = await getThreadMessagesApi({
    path: { thread_id: threadId },
  });

  if (response.error) {
    // On error, response is actually an AxiosError with .error attached
    // Check status via the AxiosError's response property
    const axiosError = response as unknown as {
      response?: { status: number };
      message: string;
    };

    // Thread doesn't exist yet - return empty array
    if (axiosError.response?.status === 404) {
      return [];
    }
    throw new Error(`Failed to fetch thread messages: ${axiosError.message}`);
  }

  // Cast to ChatMessage[] - the backend stores messages in UIMessage format
  return response.data.messages as unknown as ChatMessage[];
}
