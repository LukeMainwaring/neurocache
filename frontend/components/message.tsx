"use client";
import type { UseChatHelpers } from "@ai-sdk/react";
import type { DynamicToolUIPart, ToolUIPart } from "ai";
import equal from "fast-deep-equal";
import Image from "next/image";
import { memo } from "react";
import type { ChatMessage } from "@/lib/types";
import { cn, sanitizeText } from "@/lib/utils";
import { useDataStream } from "./data-stream-provider";
import { BouncingDots } from "./elements/bouncing-dots";
import { MessageContent } from "./elements/message";
import { Response } from "./elements/response";
import { ToolCall } from "./elements/tool-call";
import { MessageActions } from "./message-actions";

function isToolPart(type: string): boolean {
  return (
    type === "dynamic-tool" ||
    (type.startsWith("tool-") && type !== "tool-invocation")
  );
}

const AssistantAvatar = ({ isLoading }: { isLoading?: boolean }) => (
  <div
    className={cn(
      "-mt-1 flex size-8 shrink-0 items-center justify-center overflow-hidden rounded-full bg-background ring-1 ring-border",
      isLoading && "animate-synapse",
    )}
  >
    <Image
      alt="Neurocache"
      className="size-full object-cover"
      height={32}
      src="/images/neurocache-logo.png"
      width={32}
    />
  </div>
);

const PurePreviewMessage = ({
  chatId,
  message,
  isLoading,
  setMessages: _setMessages,
  regenerate: _regenerate,
  requiresScrollPadding: _requiresScrollPadding,
}: {
  chatId: string;
  message: ChatMessage;
  isLoading: boolean;
  setMessages: UseChatHelpers<ChatMessage>["setMessages"];
  regenerate: UseChatHelpers<ChatMessage>["regenerate"];
  requiresScrollPadding: boolean;
}) => {
  useDataStream();

  const hasTextParts = message.parts?.some(
    (p) => p.type === "text" && p.text?.trim(),
  );
  const hasToolParts = message.parts?.some((p) => isToolPart(p.type));
  const hasVisibleContent = hasTextParts || hasToolParts;

  return (
    <div
      className="group/message fade-in w-full animate-in duration-200"
      data-role={message.role}
      data-testid={`message-${message.role}`}
    >
      <div
        className={cn("flex w-full items-start gap-2 md:gap-3", {
          "justify-end": message.role === "user",
          "justify-start": message.role === "assistant",
        })}
      >
        {message.role === "assistant" && (
          <AssistantAvatar isLoading={isLoading} />
        )}

        <div
          className={cn("flex flex-col", {
            "gap-2 md:gap-4": hasVisibleContent || isLoading,
            "w-full":
              message.role === "assistant" && (hasVisibleContent || isLoading),
            "max-w-[calc(100%-2.5rem)] sm:max-w-[min(fit-content,80%)]":
              message.role === "user",
          })}
        >
          {!hasVisibleContent && isLoading && message.role === "assistant" && (
            <div className="flex items-center gap-1 p-0 text-muted-foreground text-sm">
              <span className="animate-shimmer">Synapsing</span>
              <BouncingDots />
            </div>
          )}

          {message.parts?.map((part, index) => {
            const { type } = part;
            const key = `message-${message.id}-part-${index}`;
            if (type === "text") {
              return (
                <div key={key}>
                  <MessageContent
                    className={cn({
                      "wrap-break-word w-fit rounded-2xl px-3 py-2 text-right text-white":
                        message.role === "user",
                      "bg-transparent px-0 py-0 text-left":
                        message.role === "assistant",
                    })}
                    data-testid="message-content"
                    style={
                      message.role === "user"
                        ? { backgroundColor: "#006cff" }
                        : undefined
                    }
                  >
                    <Response>{sanitizeText(part.text)}</Response>
                  </MessageContent>
                </div>
              );
            }
            if (isToolPart(type)) {
              return (
                <ToolCall
                  isStreaming={isLoading && !hasTextParts}
                  key={key}
                  part={part as DynamicToolUIPart | ToolUIPart}
                />
              );
            }
            return null;
          })}

          <MessageActions
            chatId={chatId}
            isLoading={isLoading}
            key={`action-${message.id}`}
            message={message}
          />
        </div>
      </div>
    </div>
  );
};

export const PreviewMessage = memo(
  PurePreviewMessage,
  (prevProps, nextProps) => {
    if (
      prevProps.isLoading === nextProps.isLoading &&
      prevProps.message.id === nextProps.message.id &&
      prevProps.requiresScrollPadding === nextProps.requiresScrollPadding &&
      equal(prevProps.message.parts, nextProps.message.parts)
    ) {
      return true;
    }
    return false;
  },
);

export const SynapsingMessage = () => {
  return (
    <div
      className="group/message fade-in w-full animate-in duration-300"
      data-role="assistant"
      data-testid="message-assistant-loading"
    >
      <div className="flex items-start justify-start gap-3">
        <AssistantAvatar isLoading />

        <div className="flex w-full flex-col gap-2 md:gap-4">
          <div className="flex items-center gap-1 p-0 text-muted-foreground text-sm">
            <span className="animate-shimmer">Synapsing</span>
            <BouncingDots />
          </div>
        </div>
      </div>
    </div>
  );
};
