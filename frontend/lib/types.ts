import type { UIMessage } from "ai";

export type RAGSource = {
  path: string;
  similarity: number;
  content?: string;
  section_header?: string;
  page_number?: number;
  chapter?: string;
  author?: string;
  content_type?: string;
  source_number?: number;
  obsidian_url?: string;
};

export type WebSource = {
  url: string;
  title?: string;
};

export type MessageMetadata = {
  createdAt?: string;
  ragSources?: RAGSource[];
  webSources?: WebSource[];
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
