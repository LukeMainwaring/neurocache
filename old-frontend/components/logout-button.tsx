'use client'

import { useAuth0 } from '@auth0/auth0-react'
import { Button } from './design-system-components/Button'

export function LogoutButton() {
  const { logout, isAuthenticated } = useAuth0()

  if (!isAuthenticated) {
    return null
  }

  return (
    <Button
      variant="critical"
      size="small"
      onClick={() =>
        logout({ logoutParams: { returnTo: window.location.origin } })
      }
    >
      Log out
    </Button>
  )
}
