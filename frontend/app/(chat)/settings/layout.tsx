"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const settingsTabs = [
  { name: "Personalization", href: "/settings/personalization" },
  { name: "Knowledge Base", href: "/settings/knowledge-base" },
];

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="flex h-dvh flex-col">
      <header className="sticky top-0 flex items-center gap-2 border-b bg-background px-4 py-3">
        <Button asChild size="icon-sm" variant="ghost">
          <Link href="/">
            <ArrowLeft className="size-4" />
          </Link>
        </Button>
        <h1 className="font-semibold">Settings</h1>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <nav className="w-56 shrink-0 border-r p-4">
          <ul className="space-y-1">
            {settingsTabs.map((tab) => (
              <li key={tab.href}>
                <Link
                  className={cn(
                    "block rounded-md px-3 py-2 font-medium text-sm transition-colors",
                    pathname === tab.href
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                  )}
                  href={tab.href}
                >
                  {tab.name}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
