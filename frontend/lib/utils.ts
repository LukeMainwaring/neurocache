import type { UIMessage } from "ai";
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import type { ChatMessage } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function sanitizeText(text: string) {
  return text.replace("<has_function_call>", "");
}

export function getTextFromMessage(message: ChatMessage | UIMessage): string {
  return message.parts
    .filter((part) => part.type === "text")
    .map((part) => (part as { type: "text"; text: string }).text)
    .join("");
}
