"use client";

import {
  BookOpen,
  ChevronDown,
  ChevronUp,
  Loader2,
  Upload,
} from "lucide-react";
import { useState } from "react";
import type { BookSchema } from "@/api/generated/types.gen";
import { useKnowledgeSourceBooks } from "@/api/hooks/knowledge-sources";
import { Button } from "@/components/ui/button";
import { DOC_STATUS_COLORS, formatAuthors } from "./utils";

function BookRow({ book }: { book: BookSchema }) {
  const noteDoc = book.documents.find((d) => d.content_type === "book_note");
  const pdfDoc = book.documents.find((d) => d.content_type === "book_source");

  return (
    <div className="flex items-start justify-between rounded-md px-2 py-1.5 transition-colors hover:bg-muted/50">
      <div className="min-w-0 flex-1 space-y-0.5">
        <p className="truncate font-medium text-sm leading-none">
          {book.title}
        </p>
        {book.author && (
          <p className="truncate text-muted-foreground text-xs">
            {formatAuthors(book.author)}
          </p>
        )}
      </div>
      <div className="ml-3 flex shrink-0 items-center gap-1.5">
        {noteDoc && (
          <span className="inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-xs">
            <span
              className={`size-1.5 rounded-full ${DOC_STATUS_COLORS[noteDoc.status] ?? "bg-gray-400"}`}
            />
            Notes
          </span>
        )}
        {pdfDoc && (
          <span className="inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-xs">
            <span
              className={`size-1.5 rounded-full ${DOC_STATUS_COLORS[pdfDoc.status] ?? "bg-gray-400"}`}
            />
            PDF
          </span>
        )}
      </div>
    </div>
  );
}

export function BookList({
  sourceId,
  onUploadClick,
}: {
  sourceId: string;
  onUploadClick: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const { data: booksData, isLoading } = useKnowledgeSourceBooks(
    sourceId,
    true
  );

  return (
    <>
      <div className="flex items-center gap-1">
        <Button
          onClick={() => setExpanded((prev) => !prev)}
          size="sm"
          variant="ghost"
        >
          <BookOpen className="size-3.5" />
          Books
          {booksData && (
            <span className="text-xs">({booksData.books.length})</span>
          )}
          {expanded ? (
            <ChevronUp className="size-3.5" />
          ) : (
            <ChevronDown className="size-3.5" />
          )}
        </Button>
        <Button onClick={onUploadClick} size="sm" variant="ghost">
          <Upload className="size-3.5" />
          Upload PDF
        </Button>
      </div>

      {expanded && (
        <div className="max-h-64 space-y-0.5 overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="size-4 animate-spin text-muted-foreground" />
            </div>
          ) : booksData?.books.length === 0 ? (
            <p className="py-2 text-center text-muted-foreground text-xs">
              No books found. Add PDFs or notes to Books/ in your vault.
            </p>
          ) : (
            booksData?.books.map((book) => (
              <BookRow book={book} key={book.folder_path} />
            ))
          )}
        </div>
      )}
    </>
  );
}
