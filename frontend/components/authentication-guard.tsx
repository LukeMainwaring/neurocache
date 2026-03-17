"use client";

import { useAuth0 } from "@auth0/auth0-react";
import { Button } from "@/components/ui/button";

interface AuthenticationGuardProps {
  children: React.ReactNode;
}

export function AuthenticationGuard({ children }: AuthenticationGuardProps) {
  const { isAuthenticated, isLoading, loginWithRedirect } = useAuth0();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
          <p className="text-muted-foreground text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-6">
        <h1 className="font-bold text-3xl">Neurocache</h1>
        <p className="text-muted-foreground">
          Your personal second brain AI assistant
        </p>
        <div className="flex gap-3">
          <Button
            onClick={() =>
              loginWithRedirect({
                authorizationParams: { screen_hint: "signup" },
              })
            }
          >
            Sign up
          </Button>
          <Button onClick={() => loginWithRedirect()} variant="outline">
            Log in
          </Button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
