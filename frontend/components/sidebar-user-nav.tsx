"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTheme } from "next-themes";
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
import { ChevronUp, MoonIcon, SettingsIcon, SunIcon } from "lucide-react";
import { fetchCurrentUser, type User } from "@/lib/api/backend-client";

export function SidebarUserNav() {
  const { setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    setMounted(true);
    fetchCurrentUser()
      .then(setUser)
      .catch((err) => console.error("Failed to fetch user:", err));
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
              <div className="flex size-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
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
                <SettingsIcon className="size-4 mr-2" />
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
                  <MoonIcon className="size-4 mr-2" />
                ) : (
                  <SunIcon className="size-4 mr-2" />
                )
              ) : (
                <SunIcon className="size-4 mr-2" />
              )}
              {mounted
                ? `Toggle ${resolvedTheme === "light" ? "dark" : "light"} mode`
                : "Toggle theme"}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
