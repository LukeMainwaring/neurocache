"use client";

import type { AppState } from "@auth0/auth0-react";
import { Auth0Provider as Auth0ReactProvider } from "@auth0/auth0-react";
import { useRouter } from "next/navigation";

interface Auth0ProviderProps {
  children: React.ReactNode;
}

export function Auth0Provider({ children }: Auth0ProviderProps) {
  const router = useRouter();

  const onRedirectCallback = (appState?: AppState) => {
    router.push(appState?.returnTo || "/");
  };

  const domain = process.env.NEXT_PUBLIC_AUTH0_DOMAIN;
  const clientId = process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID;
  const audience = process.env.NEXT_PUBLIC_AUTH0_AUDIENCE;

  if (!domain || !clientId) {
    console.error(
      "Auth0 configuration missing. Please check NEXT_PUBLIC_AUTH0_DOMAIN and NEXT_PUBLIC_AUTH0_CLIENT_ID.",
    );
    return <>{children}</>;
  }

  return (
    <Auth0ReactProvider
      authorizationParams={{
        redirect_uri:
          typeof window !== "undefined" ? window.location.origin : undefined,
        audience,
      }}
      cacheLocation="localstorage"
      clientId={clientId}
      domain={domain}
      onRedirectCallback={onRedirectCallback}
      useRefreshTokens={true}
    >
      {children}
    </Auth0ReactProvider>
  );
}
