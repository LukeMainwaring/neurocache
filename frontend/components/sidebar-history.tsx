"use client";

import { isToday, isYesterday, subMonths, subWeeks } from "date-fns";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import useSWR from "swr";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  useSidebar,
} from "@/components/ui/sidebar";
import {
  deleteThread,
  getThreads,
  type ThreadSummary,
} from "@/lib/api/backend-client";
import { ChatItem } from "./sidebar-history-item";

type GroupedThreads = {
  today: ThreadSummary[];
  yesterday: ThreadSummary[];
  lastWeek: ThreadSummary[];
  lastMonth: ThreadSummary[];
  older: ThreadSummary[];
};

const groupThreadsByDate = (threads: ThreadSummary[]): GroupedThreads => {
  const now = new Date();
  const oneWeekAgo = subWeeks(now, 1);
  const oneMonthAgo = subMonths(now, 1);

  return threads.reduce(
    (groups, thread) => {
      const threadDate = new Date(thread.created_at);

      if (isToday(threadDate)) {
        groups.today.push(thread);
      } else if (isYesterday(threadDate)) {
        groups.yesterday.push(thread);
      } else if (threadDate > oneWeekAgo) {
        groups.lastWeek.push(thread);
      } else if (threadDate > oneMonthAgo) {
        groups.lastMonth.push(thread);
      } else {
        groups.older.push(thread);
      }

      return groups;
    },
    {
      today: [],
      yesterday: [],
      lastWeek: [],
      lastMonth: [],
      older: [],
    } as GroupedThreads
  );
};

export function SidebarHistory() {
  const { setOpenMobile } = useSidebar();
  const pathname = usePathname();
  const id = pathname?.startsWith("/chat/") ? pathname.split("/")[2] : null;

  const {
    data: threads,
    isLoading,
    mutate,
  } = useSWR<ThreadSummary[]>("threads", getThreads, {
    fallbackData: [],
  });

  // Poll for title updates when any thread has a pending title
  const hasPendingTitles = threads?.some((t) => t.title === null);
  useEffect(() => {
    if (!hasPendingTitles) return;
    const interval = setInterval(() => {
      mutate();
    }, 2000);
    return () => clearInterval(interval);
  }, [hasPendingTitles, mutate]);

  const router = useRouter();
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const handleDelete = async () => {
    const threadToDelete = deleteId;
    const isCurrentThread = pathname === `/chat/${threadToDelete}`;

    setShowDeleteDialog(false);

    if (!threadToDelete) return;

    const deletePromise = deleteThread(threadToDelete);

    toast.promise(deletePromise, {
      loading: "Deleting thread...",
      success: () => {
        mutate((currentThreads) => {
          if (currentThreads) {
            return currentThreads.filter(
              (thread) => thread.id !== threadToDelete
            );
          }
          return currentThreads;
        });

        if (isCurrentThread) {
          router.replace("/");
          router.refresh();
        }

        return "Thread deleted successfully";
      },
      error: "Failed to delete thread",
    });
  };

  if (isLoading) {
    return (
      <SidebarGroup>
        <div className="px-2 py-1 text-sidebar-foreground/50 text-xs">
          Today
        </div>
        <SidebarGroupContent>
          <div className="flex flex-col">
            {[44, 32, 28, 64, 52].map((item) => (
              <div
                className="flex h-8 items-center gap-2 rounded-md px-2"
                key={item}
              >
                <div
                  className="h-4 max-w-(--skeleton-width) flex-1 rounded-md bg-sidebar-accent-foreground/10"
                  style={
                    {
                      "--skeleton-width": `${item}%`,
                    } as React.CSSProperties
                  }
                />
              </div>
            ))}
          </div>
        </SidebarGroupContent>
      </SidebarGroup>
    );
  }

  if (!threads || threads.length === 0) {
    return (
      <SidebarGroup>
        <SidebarGroupContent>
          <div className="px-2 py-2 text-center text-muted-foreground text-sm">
            Your conversations will appear here
          </div>
        </SidebarGroupContent>
      </SidebarGroup>
    );
  }

  const groupedThreads = groupThreadsByDate(threads);

  return (
    <>
      <SidebarGroup>
        <SidebarGroupContent>
          <SidebarMenu>
            {groupedThreads.today.length > 0 && (
              <>
                <div className="px-2 py-1 text-sidebar-foreground/50 text-xs">
                  Today
                </div>
                {groupedThreads.today.map((thread) => (
                  <ChatItem
                    chat={{
                      id: thread.id,
                      title: thread.title,
                      createdAt: new Date(thread.created_at),
                    }}
                    isActive={thread.id === id}
                    key={thread.id}
                    onDelete={(chatId) => {
                      setDeleteId(chatId);
                      setShowDeleteDialog(true);
                    }}
                    setOpenMobile={setOpenMobile}
                  />
                ))}
              </>
            )}

            {groupedThreads.yesterday.length > 0 && (
              <>
                <div className="mt-4 px-2 py-1 text-sidebar-foreground/50 text-xs">
                  Yesterday
                </div>
                {groupedThreads.yesterday.map((thread) => (
                  <ChatItem
                    chat={{
                      id: thread.id,
                      title: thread.title,
                      createdAt: new Date(thread.created_at),
                    }}
                    isActive={thread.id === id}
                    key={thread.id}
                    onDelete={(chatId) => {
                      setDeleteId(chatId);
                      setShowDeleteDialog(true);
                    }}
                    setOpenMobile={setOpenMobile}
                  />
                ))}
              </>
            )}

            {groupedThreads.lastWeek.length > 0 && (
              <>
                <div className="mt-4 px-2 py-1 text-sidebar-foreground/50 text-xs">
                  Last 7 days
                </div>
                {groupedThreads.lastWeek.map((thread) => (
                  <ChatItem
                    chat={{
                      id: thread.id,
                      title: thread.title,
                      createdAt: new Date(thread.created_at),
                    }}
                    isActive={thread.id === id}
                    key={thread.id}
                    onDelete={(chatId) => {
                      setDeleteId(chatId);
                      setShowDeleteDialog(true);
                    }}
                    setOpenMobile={setOpenMobile}
                  />
                ))}
              </>
            )}

            {groupedThreads.lastMonth.length > 0 && (
              <>
                <div className="mt-4 px-2 py-1 text-sidebar-foreground/50 text-xs">
                  Last 30 days
                </div>
                {groupedThreads.lastMonth.map((thread) => (
                  <ChatItem
                    chat={{
                      id: thread.id,
                      title: thread.title,
                      createdAt: new Date(thread.created_at),
                    }}
                    isActive={thread.id === id}
                    key={thread.id}
                    onDelete={(chatId) => {
                      setDeleteId(chatId);
                      setShowDeleteDialog(true);
                    }}
                    setOpenMobile={setOpenMobile}
                  />
                ))}
              </>
            )}

            {groupedThreads.older.length > 0 && (
              <>
                <div className="mt-4 px-2 py-1 text-sidebar-foreground/50 text-xs">
                  Older
                </div>
                {groupedThreads.older.map((thread) => (
                  <ChatItem
                    chat={{
                      id: thread.id,
                      title: thread.title,
                      createdAt: new Date(thread.created_at),
                    }}
                    isActive={thread.id === id}
                    key={thread.id}
                    onDelete={(chatId) => {
                      setDeleteId(chatId);
                      setShowDeleteDialog(true);
                    }}
                    setOpenMobile={setOpenMobile}
                  />
                ))}
              </>
            )}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>

      <AlertDialog onOpenChange={setShowDeleteDialog} open={showDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete your
              chat and remove your data from our servers.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>
              Continue
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

// Export for mutation in chat.tsx
export const chatHistoryKey = "threads";
