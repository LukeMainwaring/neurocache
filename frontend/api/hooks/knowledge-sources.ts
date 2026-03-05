import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createKnowledgeSourceMutation,
  deleteKnowledgeSourceMutation,
  getKnowledgeSourceDefaultsOptions,
  ingestAllDocumentsMutation,
  listBooksOptions,
  listBooksQueryKey,
  listKnowledgeSourcesOptions,
  listKnowledgeSourcesQueryKey,
  previewBookPdfMutation,
  retryKnowledgeSourceMutation,
  uploadBookPdfMutation,
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

export const useRetryKnowledgeSource = () => {
  const queryClient = useQueryClient();
  const mutationResult = useMutation({
    ...retryKnowledgeSourceMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listKnowledgeSourcesQueryKey(),
      });
    },
  });

  const retrySource = (sourceId: string) => {
    return mutationResult.mutateAsync({ path: { source_id: sourceId } });
  };

  return {
    retrySource,
    ...mutationResult,
  };
};

export const useKnowledgeSourceBooks = (sourceId: string, enabled: boolean) => {
  return useQuery({
    ...listBooksOptions({ path: { source_id: sourceId } }),
    enabled,
  });
};

export const usePreviewBook = (sourceId: string) => {
  const mutation = useMutation({
    ...previewBookPdfMutation({ path: { source_id: sourceId } }),
  });

  const previewBook = (file: File) =>
    mutation.mutateAsync({
      path: { source_id: sourceId },
      body: { file },
    });

  return { previewBook, ...mutation };
};

export const useUploadBook = (sourceId: string) => {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    ...uploadBookPdfMutation({ path: { source_id: sourceId } }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listBooksQueryKey({ path: { source_id: sourceId } }),
      });
    },
  });

  const uploadBook = (file: File, title: string, author?: string | null) =>
    mutation.mutateAsync({
      path: { source_id: sourceId },
      body: { file, title, author },
    });

  return { uploadBook, ...mutation };
};

export const useSyncKnowledgeSource = () => {
  const queryClient = useQueryClient();
  const mutationResult = useMutation({
    ...ingestAllDocumentsMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listKnowledgeSourcesQueryKey(),
      });
    },
  });

  const syncSource = (sourceId: string) => {
    return mutationResult.mutateAsync({
      path: { source_id: sourceId },
      query: { force_reindex: false },
    });
  };

  return {
    syncSource,
    ...mutationResult,
  };
};
