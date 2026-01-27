import { memo } from "react";
import { toast } from "sonner";
import { useCopyToClipboard } from "usehooks-ts";
import type { ChatMessage } from "@/lib/types";
import { Action, Actions } from "./elements/actions";
import { CopyIcon, FileTextIcon } from "./icons";
import { RAGSourcesDialog } from "./rag-sources-dialog";

export function PureMessageActions({
  chatId: _chatId,
  message,
  isLoading,
}: {
  chatId: string;
  message: ChatMessage;
  isLoading: boolean;
}) {
  const [_, copyToClipboard] = useCopyToClipboard();

  if (isLoading) {
    return null;
  }

  const textFromParts = message.parts
    ?.filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("\n")
    .trim();

  const handleCopy = async () => {
    if (!textFromParts) {
      toast.error("There's no text to copy!");
      return;
    }

    await copyToClipboard(textFromParts);
    toast.success("Copied to clipboard!");
  };

  // User messages get copy action and optionally view sources
  if (message.role === "user") {
    const ragSources = message.metadata?.ragSources;

    return (
      <Actions className="-mr-0.5 justify-end">
        {ragSources && ragSources.length > 0 && (
          <RAGSourcesDialog
            sources={ragSources}
            trigger={
              <Action tooltip="View sources">
                <FileTextIcon />
              </Action>
            }
          />
        )}
        <Action onClick={handleCopy} tooltip="Copy">
          <CopyIcon />
        </Action>
      </Actions>
    );
  }

  // Assistant messages get only copy action
  return (
    <Actions className="-ml-0.5">
      <Action onClick={handleCopy} tooltip="Copy">
        <CopyIcon />
      </Action>
    </Actions>
  );
}

export const MessageActions = memo(
  PureMessageActions,
  (prevProps, nextProps) => {
    if (prevProps.isLoading !== nextProps.isLoading) {
      return false;
    }

    return true;
  }
);
