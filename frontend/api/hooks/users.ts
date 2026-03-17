import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  activateMyselfMutation,
  getMyselfOptions,
  getMyselfQueryKey,
  updateMyPersonalizationMutation,
} from "../generated/@tanstack/react-query.gen";
import type {
  UserActivateSchema,
  UserPersonalizationUpdateSchema,
} from "../generated/types.gen";

export const useMyself = () => {
  return useQuery(getMyselfOptions());
};

export const useActivateMyself = () => {
  const queryClient = useQueryClient();
  const mutationResult = useMutation({
    ...activateMyselfMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: getMyselfQueryKey() });
    },
  });

  const activate = (params: UserActivateSchema) => {
    return mutationResult.mutateAsync({ body: params });
  };

  return { activate, ...mutationResult };
};

export const useUpdateMyPersonalization = () => {
  const queryClient = useQueryClient();
  const mutationResult = useMutation({
    ...updateMyPersonalizationMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: getMyselfQueryKey() });
    },
  });

  const updatePersonalization = (params: UserPersonalizationUpdateSchema) => {
    return mutationResult.mutateAsync({
      body: params,
    });
  };

  return {
    updatePersonalization,
    ...mutationResult,
  };
};
