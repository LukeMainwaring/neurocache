import { useMutation } from '@tanstack/react-query'

import { pingRunRouteApiPingRunPostMutation } from '@/client/@tanstack/react-query.gen'

export const usePingNotification = () => {
  const mutation = useMutation({
    ...pingRunRouteApiPingRunPostMutation()
  })

  return {
    pingNotification: mutation.mutateAsync,
    ...mutation
  }
}
