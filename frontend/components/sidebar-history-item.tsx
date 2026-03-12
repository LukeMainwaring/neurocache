import Link from "next/link";
import { memo, useEffect, useRef, useState } from "react";
import type { Chat } from "@/lib/types";
import { MoreHorizontalIcon, PencilEditIcon, TrashIcon } from "./icons";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import {
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
} from "./ui/sidebar";

const PureChatItem = ({
  chat,
  isActive,
  isRenaming,
  onCancelRename,
  onDelete,
  onRename,
  onStartRename,
  setOpenMobile,
}: {
  chat: Chat;
  isActive: boolean;
  isRenaming: boolean;
  onCancelRename: () => void;
  onDelete: (chatId: string) => void;
  onRename: (chatId: string, title: string) => void;
  onStartRename: (chatId: string) => void;
  setOpenMobile: (open: boolean) => void;
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [renameValue, setRenameValue] = useState(chat.title ?? "");

  useEffect(() => {
    if (isRenaming) {
      setRenameValue(chat.title ?? "");
      // Defer focus to next frame so input is mounted
      requestAnimationFrame(() => {
        inputRef.current?.focus();
        inputRef.current?.select();
      });
    }
  }, [isRenaming, chat.title]);

  const handleRenameSubmit = () => {
    const trimmed = renameValue.trim();
    if (!trimmed || trimmed === chat.title) {
      onCancelRename();
      return;
    }
    onRename(chat.id, trimmed);
  };

  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild isActive={isActive}>
        {isRenaming ? (
          <div className="flex items-center bg-sidebar-accent text-sidebar-accent-foreground">
            <input
              className="w-full bg-transparent text-sm outline-none"
              onBlur={handleRenameSubmit}
              onChange={(e) => setRenameValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleRenameSubmit();
                } else if (e.key === "Escape") {
                  e.preventDefault();
                  onCancelRename();
                }
              }}
              ref={inputRef}
              value={renameValue}
            />
          </div>
        ) : (
          <Link href={`/chat/${chat.id}`} onClick={() => setOpenMobile(false)}>
            <span>
              {chat.title ?? (
                <span className="animate-pulse text-muted-foreground">
                  Generating...
                </span>
              )}
            </span>
          </Link>
        )}
      </SidebarMenuButton>

      {!isRenaming && (
        <DropdownMenu modal={true}>
          <DropdownMenuTrigger asChild>
            <SidebarMenuAction
              className="mr-0.5 data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
              showOnHover={!isActive}
            >
              <MoreHorizontalIcon />
              <span className="sr-only">More</span>
            </SidebarMenuAction>
          </DropdownMenuTrigger>

          <DropdownMenuContent align="end" side="bottom">
            <DropdownMenuItem
              className="cursor-pointer"
              onSelect={() => onStartRename(chat.id)}
            >
              <PencilEditIcon />
              <span>Rename</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="cursor-pointer text-destructive focus:bg-destructive/15 focus:text-destructive dark:text-red-500"
              onSelect={() => onDelete(chat.id)}
            >
              <TrashIcon />
              <span>Delete</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </SidebarMenuItem>
  );
};

export const ChatItem = memo(PureChatItem, (prevProps, nextProps) => {
  if (prevProps.isActive !== nextProps.isActive) {
    return false;
  }
  if (prevProps.chat.title !== nextProps.chat.title) {
    return false;
  }
  if (prevProps.isRenaming !== nextProps.isRenaming) {
    return false;
  }
  return true;
});
