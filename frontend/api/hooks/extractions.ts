import { useMutation, useQuery } from "@tanstack/react-query";
import {
  confirmExtractionMutation,
  getExtractionStatusOptions,
  previewExtractionMutation,
} from "../generated/@tanstack/react-query.gen";

// Ensure client is configured with baseURL
import "../client";

export const useExtractionPreview = () => {
  const mutationResult = useMutation(previewExtractionMutation());

  const previewExtraction = (threadId: string) => {
    return mutationResult.mutateAsync({
      body: { thread_id: threadId },
    });
  };

  return {
    previewExtraction,
    ...mutationResult,
  };
};

export const useExtractionConfirm = () => {
  const mutationResult = useMutation(confirmExtractionMutation());

  const confirmExtraction = (
    threadId: string,
    title: string,
    content: string,
  ) => {
    return mutationResult.mutateAsync({
      body: { thread_id: threadId, title, content },
    });
  };

  return {
    confirmExtraction,
    ...mutationResult,
  };
};

export const useExtractionStatus = (threadId: string | null) => {
  return useQuery({
    ...getExtractionStatusOptions({
      query: { thread_id: threadId ?? "" },
    }),
    enabled: !!threadId,
  });
};
