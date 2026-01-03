'use client'

import { Auth0Provider as Auth0ReactProvider } from '@auth0/auth0-react'
import { useRouter } from 'next/navigation'
import type { AppState } from '@auth0/auth0-react'
import ENV_VARS from '@/lib/envVars'

interface Auth0ProviderProps {
  children: React.ReactNode
}

export function Auth0Provider({ children }: Auth0ProviderProps) {
  const router = useRouter()

  const onRedirectCallback = (appState?: AppState) => {
    router.push(appState?.returnTo || '/')
  }

  if (!ENV_VARS.AUTH0_DOMAIN || !ENV_VARS.AUTH0_CLIENT_ID) {
    console.error(
      'Auth0 configuration missing. Please check environment variables.'
    )
    return <>{children}</>
  }

  return (
    <Auth0ReactProvider
      domain={ENV_VARS.AUTH0_DOMAIN}
      clientId={ENV_VARS.AUTH0_CLIENT_ID}
      authorizationParams={{
        redirect_uri: ENV_VARS.BASE_URL,
        audience: ENV_VARS.AUTH0_AUDIENCE
      }}
      onRedirectCallback={onRedirectCallback}
      useRefreshTokens={true}
      cacheLocation="localstorage"
    >
      {children}
    </Auth0ReactProvider>
  )
}
