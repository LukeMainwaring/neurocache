"use client";

import { useAuth0 } from "@auth0/auth0-react";
import {
  ChevronUp,
  LogOutIcon,
  MoonIcon,
  SettingsIcon,
  SunIcon,
} from "lucide-react";
import Link from "next/link";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { useMyself } from "@/api/hooks/users";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

export function SidebarUserNav() {
  const { setTheme, resolvedTheme } = useTheme();
  const { logout } = useAuth0();
  const [mounted, setMounted] = useState(false);
  const { data: user } = useMyself();

  useEffect(() => {
    setMounted(true);
  }, []);

  const displayName = user?.nickname || user?.name || "User";
  const initial = displayName.charAt(0).toUpperCase();

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              className="h-12 bg-background data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
              data-testid="user-nav-button"
            >
              <div className="flex size-8 items-center justify-center rounded-full bg-primary font-medium text-primary-foreground text-sm">
                {initial}
              </div>
              <span className="truncate font-medium">{displayName}</span>
              <ChevronUp className="ml-auto size-4" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-(--radix-popper-anchor-width)"
            side="top"
          >
            <DropdownMenuItem asChild className="cursor-pointer">
              <Link href="/settings">
                <SettingsIcon className="mr-2 size-4" />
                Settings
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem
              className="cursor-pointer"
              onSelect={() =>
                setTheme(resolvedTheme === "dark" ? "light" : "dark")
              }
            >
              {mounted ? (
                resolvedTheme === "dark" ? (
                  <MoonIcon className="mr-2 size-4" />
                ) : (
                  <SunIcon className="mr-2 size-4" />
                )
              ) : (
                <SunIcon className="mr-2 size-4" />
              )}
              {mounted
                ? `Toggle ${resolvedTheme === "light" ? "dark" : "light"} mode`
                : "Toggle theme"}
            </DropdownMenuItem>
            <DropdownMenuItem
              className="cursor-pointer"
              onSelect={() =>
                logout({
                  logoutParams: { returnTo: window.location.origin },
                })
              }
            >
              <LogOutIcon className="mr-2 size-4" />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
