'use client'

import { useAuth0 } from '@auth0/auth0-react'
import { isUserAuthorized } from '@/lib/utils/auth'
import { LogoutButton } from '../logout-button'
import { Button } from '../design-system-components/Button'

interface AuthenticationGuardProps {
  children: React.ReactNode
}

export function AuthenticationGuard({ children }: AuthenticationGuardProps) {
  const { isAuthenticated, isLoading, loginWithRedirect, user } = useAuth0()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
          <p className="text-sm text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-6">
        <h1 className="font-bold">Welcome to Uppy!</h1>
        <p>Neurocache</p>
        <Button
          variant="primary"
          size="large"
          onClick={() => loginWithRedirect()}
        >
          Log In
        </Button>
      </div>
    )
  }

  // Check if user is authorized
  if (!isUserAuthorized(user)) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <p>You do not have permission to access this application.</p>
          <LogoutButton />
        </div>
      </div>
    )
  }

  return <>{children}</>
}
