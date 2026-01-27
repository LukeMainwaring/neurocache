import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getMyselfOptions,
  getMyselfQueryKey,
  updateMyPersonalizationMutation,
} from "../generated/@tanstack/react-query.gen";
import { UserPersonalizationUpdateSchema } from "../generated/types.gen";

export const useMyself = () => {
  return useQuery(getMyselfOptions());
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
