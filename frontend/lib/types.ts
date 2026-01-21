import type { UIMessage } from "ai";

export type DataPart = { type: "append-message"; message: string };

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

export type User = {
  id: string;
  email: string;
  name: string | null;
  created_at: string;
  updated_at: string;
  custom_instructions: string | null;
  nickname: string | null;
  occupation: string | null;
  about_you: string | null;
};
