import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  deleteThreadMutation,
  listThreadsOptions,
  listThreadsQueryKey,
} from "../generated/@tanstack/react-query.gen";

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
