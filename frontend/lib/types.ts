import type { UIMessage } from "ai";

export type RAGSource = {
  path: string;
  similarity: number;
  content?: string;
};

export type MessageMetadata = {
  createdAt?: string;
  ragSources?: RAGSource[];
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
