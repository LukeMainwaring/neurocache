"use client";

import { useAuth0 } from "@auth0/auth0-react";
import { useEffect } from "react";
import { setAccessTokenGetter, setupAuthInterceptor } from "@/api/client";

export function AccessTokenProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const { getAccessTokenSilently } = useAuth0();

  useEffect(() => {
    setupAuthInterceptor(() => getAccessTokenSilently());
    setAccessTokenGetter(() => getAccessTokenSilently());
  }, [getAccessTokenSilently]);

  return <>{children}</>;
}
