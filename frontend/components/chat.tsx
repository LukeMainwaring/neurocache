"use client";

import { useChat } from "@ai-sdk/react";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { listThreadsQueryKey } from "@/api/generated/@tanstack/react-query.gen";
import { getThreadMessages } from "@/api/hooks/threads";
import { ChatHeader } from "@/components/chat-header";
import { useAutoResume } from "@/hooks/use-auto-resume";
import type { ChatMessage } from "@/lib/types";
import { useDataStream } from "./data-stream-provider";
import { Messages } from "./messages";
import { MultimodalInput } from "./multimodal-input";
import { toast } from "./toast";

export function Chat({
  id,
  initialMessages,
  autoResume,
}: {
  id: string;
  initialMessages: ChatMessage[];
  autoResume: boolean;
}) {
  const router = useRouter();
  const queryClient = useQueryClient();

  // Handle browser back/forward navigation
  useEffect(() => {
    const handlePopState = () => {
      // When user navigates back/forward, refresh to sync with URL
      router.refresh();
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, [router]);
  const { setDataStream } = useDataStream();

  const [input, setInput] = useState<string>("");

  const {
    messages,
    setMessages,
    sendMessage,
    status,
    stop,
    regenerate,
    resumeStream,
  } = useChat<ChatMessage>({
    id,
    messages: initialMessages,
    experimental_throttle: 100,
    onData: (dataPart) => {
      setDataStream((ds) => (ds ? [...ds, dataPart] : []));
    },
    onFinish: async () => {
      // Refresh sidebar thread list
      queryClient.invalidateQueries({ queryKey: listThreadsQueryKey() });

      // Refetch messages to get RAG metadata (stored server-side)
      // This ensures "View Sources" button appears after streaming completes
      try {
        const updatedMessages = await getThreadMessages(id);
        if (updatedMessages.length > 0) {
          setMessages(updatedMessages);
        }
      } catch (error) {
        console.error("Failed to refresh messages with RAG metadata:", error);
      }
    },
    onError: (error) => {
      console.error("Chat error:", error);
      toast({
        type: "error",
        description: error.message || "An error occurred",
      });
    },
  });

  const searchParams = useSearchParams();
  const query = searchParams.get("query");

  const [hasAppendedQuery, setHasAppendedQuery] = useState(false);

  useEffect(() => {
    if (query && !hasAppendedQuery) {
      sendMessage({
        role: "user" as const,
        parts: [{ type: "text", text: query }],
      });

      setHasAppendedQuery(true);
      window.history.replaceState({}, "", `/chat/${id}`);
    }
  }, [query, sendMessage, hasAppendedQuery, id]);

  useAutoResume({
    autoResume,
    initialMessages,
    resumeStream,
    setMessages,
  });

  return (
    <div className="overscroll-behavior-contain flex h-dvh min-w-0 touch-pan-y flex-col bg-background">
      <ChatHeader />

      <Messages
        chatId={id}
        messages={messages}
        regenerate={regenerate}
        setMessages={setMessages}
        status={status}
      />

      <div className="sticky bottom-0 z-1 mx-auto flex w-full max-w-4xl gap-2 border-t-0 bg-background px-2 pb-3 md:px-4 md:pb-4">
        <MultimodalInput
          chatId={id}
          input={input}
          messages={messages}
          sendMessage={sendMessage}
          setInput={setInput}
          setMessages={setMessages}
          status={status}
          stop={stop}
        />
      </div>
    </div>
  );
}
