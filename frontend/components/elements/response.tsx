"use client";

import type { HTMLAttributes, ReactNode } from "react";
import { memo } from "react";
import { type ExtraProps, Streamdown } from "streamdown";
import type { RAGSource } from "@/lib/types";
import { cn } from "@/lib/utils";
import { CitationMarker } from "./citation-marker";

/**
 * Replace [N] citation markers with <cite> HTML tags that Streamdown
 * will render via the components override. Skips replacements inside
 * fenced code blocks and inline code to avoid false positives.
 */
function processCitations(text: string): string {
  const parts = text.split(/(```[\s\S]*?```|`[^`]+`)/g);
  return parts
    .map((part, i) => {
      if (i % 2 === 1) return part;
      return part.replace(/\[(\d+)\](?!\()/g, "<cite>[$1]</cite>");
    })
    .join("");
}

/** Extract citation number from [N] text content inside a <cite> tag. */
function parseCitationNumber(children: ReactNode): number {
  const text = typeof children === "string" ? children : String(children);
  const match = text.match(/\[(\d+)\]/);
  return match ? Number(match[1]) : Number.NaN;
}

function createCiteComponent(sources: RAGSource[]) {
  return function Cite({ children }: HTMLAttributes<HTMLElement> & ExtraProps) {
    const num = parseCitationNumber(children);
    const source = Number.isNaN(num)
      ? undefined
      : sources.find((s) => s.source_number === num);
    return <CitationMarker number={num} source={source} />;
  };
}

type ResponseProps = {
  className?: string;
  children?: string;
  sources?: RAGSource[];
};

export const Response = memo(
  ({ className, sources, children, ...props }: ResponseProps) => {
    const text = typeof children === "string" ? children : "";
    const processedText = sources ? processCitations(text) : text;

    return (
      <Streamdown
        className={cn(
          "size-full [&>*:first-child]:mt-0 [&>*:last-child]:mb-0 [&_code]:whitespace-pre-wrap [&_code]:break-words [&_pre]:max-w-full [&_pre]:overflow-x-auto",
          className,
        )}
        allowedTags={sources ? { cite: [] } : undefined}
        components={
          sources ? { cite: createCiteComponent(sources) } : undefined
        }
        {...props}
      >
        {processedText}
      </Streamdown>
    );
  },
  (prevProps, nextProps) =>
    prevProps.children === nextProps.children &&
    prevProps.sources === nextProps.sources,
);

Response.displayName = "Response";
