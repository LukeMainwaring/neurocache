import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createKnowledgeSourceMutation,
  deleteKnowledgeSourceMutation,
  getKnowledgeSourceDefaultsOptions,
  listKnowledgeSourcesOptions,
  listKnowledgeSourcesQueryKey,
} from "../generated/@tanstack/react-query.gen";
import type { KnowledgeSourceCreateSchema } from "../generated/types.gen";

export const useKnowledgeSources = () => {
  return useQuery(listKnowledgeSourcesOptions());
};

export const useKnowledgeSourceDefaults = () => {
  return useQuery(getKnowledgeSourceDefaultsOptions());
};

export const useCreateKnowledgeSource = () => {
  const queryClient = useQueryClient();
  const mutationResult = useMutation({
    ...createKnowledgeSourceMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listKnowledgeSourcesQueryKey(),
      });
    },
  });

  const createSource = (params: KnowledgeSourceCreateSchema) => {
    return mutationResult.mutateAsync({ body: params });
  };

  return {
    createSource,
    ...mutationResult,
  };
};

export const useDeleteKnowledgeSource = () => {
  const queryClient = useQueryClient();
  const mutationResult = useMutation({
    ...deleteKnowledgeSourceMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listKnowledgeSourcesQueryKey(),
      });
    },
  });

  const deleteSource = (sourceId: string) => {
    return mutationResult.mutateAsync({ path: { source_id: sourceId } });
  };

  return {
    deleteSource,
    ...mutationResult,
  };
};
