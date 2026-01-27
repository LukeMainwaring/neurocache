import type { UIMessage } from "ai";

export type MessageMetadata = {
  createdAt: string;
};

export type CustomUIDataTypes = {
  "chat-title": string;
};

export type ChatMessage = UIMessage<MessageMetadata, CustomUIDataTypes>;

export type Chat = {
  id: string;
  title: string | null;
  createdAt: Date;
};
