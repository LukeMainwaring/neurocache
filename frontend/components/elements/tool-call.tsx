"use client";

import { type DynamicToolUIPart, getToolName, type ToolUIPart } from "ai";
import {
  CheckCircleFillIcon,
  ChevronDownIcon,
  CrossSmallIcon,
  LoaderIcon,
} from "../icons";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "../ui/collapsible";
import { BouncingDots } from "./bouncing-dots";

function formatToolName(name: string): string {
  return name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

const TOOL_VERBS: Record<string, string> = {
  search_knowledge_base: "Searching knowledge base",
  web_search: "Searching the web",
};

function getToolVerb(name: string): string {
  return TOOL_VERBS[name] ?? formatToolName(name);
}

export function ToolCall({
  part,
  isStreaming,
}: {
  part: DynamicToolUIPart | ToolUIPart;
  isStreaming?: boolean;
}) {
  const toolName = getToolName(part);
  const isRunning =
    part.state === "input-streaming" ||
    part.state === "input-available" ||
    (isStreaming && part.state === "output-available");
  const isError = part.state === "output-error";
  const isComplete = !isRunning && part.state === "output-available";

  return (
    <Collapsible defaultOpen={isRunning}>
      <CollapsibleTrigger className="group flex w-full cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-muted-foreground text-sm transition-colors hover:bg-muted/50">
        <div className="flex min-w-0 flex-1 items-center gap-2">
          {isRunning && (
            <div className="animate-spin text-muted-foreground">
              <LoaderIcon size={14} />
            </div>
          )}
          {isComplete && (
            <div className="text-green-600 dark:text-green-500">
              <CheckCircleFillIcon size={14} />
            </div>
          )}
          {isError && (
            <div className="text-red-600 dark:text-red-500">
              <CrossSmallIcon size={14} />
            </div>
          )}
          <span className="truncate font-medium">
            {isRunning ? getToolVerb(toolName) : formatToolName(toolName)}
          </span>
          {isRunning && <BouncingDots />}
        </div>
        {!isRunning && (
          <div className="group-data-[state=closed]:-rotate-90 transition-transform duration-200">
            <ChevronDownIcon size={14} />
          </div>
        )}
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="mt-1 ml-7 space-y-2 text-xs">
          {part.input != null &&
            typeof part.input === "object" &&
            Object.keys(part.input as object).length > 0 && (
              <pre className="overflow-x-auto rounded-md bg-muted/50 p-2 text-muted-foreground">
                {JSON.stringify(part.input, null, 2)}
              </pre>
            )}
          {isComplete && part.output != null && (
            <pre className="overflow-x-auto rounded-md bg-muted/50 p-2 text-muted-foreground">
              {typeof part.output === "string"
                ? part.output
                : JSON.stringify(part.output, null, 2)}
            </pre>
          )}
          {isError && part.errorText && (
            <pre className="overflow-x-auto rounded-md bg-red-50 p-2 text-red-700 dark:bg-red-950/30 dark:text-red-400">
              {part.errorText}
            </pre>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
