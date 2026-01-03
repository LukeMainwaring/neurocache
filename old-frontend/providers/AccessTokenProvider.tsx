import { useAuth0 } from '@auth0/auth0-react'
import { useEffect } from 'react'

import { setupAuthInterceptor } from '@/app/api/apiClient'

export function AccessTokenProvider({
  children
}: {
  children: React.ReactNode
}) {
  const { getAccessTokenSilently } = useAuth0()

  useEffect(() => {
    setupAuthInterceptor(() => getAccessTokenSilently())
  }, [getAccessTokenSilently])

  return <>{children}</>
}
