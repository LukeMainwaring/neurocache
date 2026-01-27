import { useQuery } from "@tanstack/react-query";
import { getMyselfOptions } from "../generated/@tanstack/react-query.gen";

export const useMyself = () => {
  return useQuery(getMyselfOptions());
};
