import { useAuth0 } from '@auth0/auth0-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { type AxiosError } from 'axios'

import {
  getMyselfApiCustomerMyselfGetOptions,
  updateCustomerApiCustomerCustomerIdPutMutation,
  resetCustomerHistoryApiCustomerCustomerIdResetHistoryPostMutation,
  getMyselfApiCustomerMyselfGetQueryKey
} from '@/client/@tanstack/react-query.gen'
import {
  type UserSchemaOutput,
  type UserSchemaInput
} from '@/client/types.gen'

export const useMyself = (opts = {}) => {
  const { isAuthenticated, logout } = useAuth0()
  try {
    return useQuery({
      ...getMyselfApiCustomerMyselfGetOptions(),
      ...opts,
      throwOnError: true,
      enabled: isAuthenticated
    })
  } catch (error) {
    const errorResponse = (error as AxiosError)?.response
    if (errorResponse?.status === 403) {
      logout({ logoutParams: { returnTo: window.location.origin } })
    }
    return {
      data: {} as UserSchemaOutput,
      error: error as Error,
      isLoading: false
    }
  }
}

export const useUpdateCustomer = () => {
  const queryClient = useQueryClient()
  const { data: customer } = useMyself()
  const customerId = customer?.user_id

  const updateCustomerMutationResult = useMutation({
    ...updateCustomerApiCustomerCustomerIdPutMutation(),
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: getMyselfApiCustomerMyselfGetQueryKey()
      })
    }
  })

  const updateCustomer = async (body: UserSchemaInput) => {
    if (!customerId) {
      throw new Error('No customer ID available')
    }
    return updateCustomerMutationResult.mutateAsync({
      path: { user_id: customerId },
      body
    })
  }

  return { updateCustomer, ...updateCustomerMutationResult }
}

export const useResetCustomerHistory = () => {
  const queryClient = useQueryClient()
  const { data: customer } = useMyself()
  const customerId = customer?.user_id

  const resetCustomerHistoryMutationResult = useMutation({
    ...resetCustomerHistoryApiCustomerCustomerIdResetHistoryPostMutation(),
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: getMyselfApiCustomerMyselfGetQueryKey()
      })
    }
  })
  const resetCustomerHistory = async () => {
    if (!customerId) {
      throw new Error('No customer ID available')
    }
    return resetCustomerHistoryMutationResult.mutateAsync({
      path: { user_id: customerId }
    })
  }
  return { resetCustomerHistory, ...resetCustomerHistoryMutationResult }
}
