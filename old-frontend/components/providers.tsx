'use client'

import { MessagesStoreProvider } from '@/providers/messages-store-provider'
import { RagAppStoreProvider } from '@/providers/rag-app-store-provider'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider as NextThemesProvider } from 'next-themes'

import type { ComponentProps } from 'react'
import { SidebarProvider } from '@/lib/hooks/use-sidebar'
import { ThemeProvider } from './design-system-components/ThemeProvider'
import { TooltipProvider } from './design-system-components/Tooltip'
import { Auth0Provider } from './providers/Auth0Provider'
import { AuthenticationGuard } from './providers/AuthenticationGuard'
import { AccessTokenProvider } from '@/providers/AccessTokenProvider'
type ThemeProviderProps = ComponentProps<typeof NextThemesProvider>

export function Providers({ children, ...props }: ThemeProviderProps) {
  const queryClient = new QueryClient()
  return (
    <QueryClientProvider client={queryClient}>
      <NextThemesProvider {...props}>
        <ThemeProvider>
          <Auth0Provider>
            <AccessTokenProvider>
              <AuthenticationGuard>
                <RagAppStoreProvider>
                  <MessagesStoreProvider>
                    <SidebarProvider>
                      <TooltipProvider>{children}</TooltipProvider>
                    </SidebarProvider>
                  </MessagesStoreProvider>
                </RagAppStoreProvider>
              </AuthenticationGuard>
            </AccessTokenProvider>
          </Auth0Provider>
        </ThemeProvider>
      </NextThemesProvider>
    </QueryClientProvider>
  )
}
