"use client";

import { useEffect } from "react";
import { useSWRConfig } from "swr";
import { useDataStream } from "./data-stream-provider";
import { chatHistoryKey } from "./sidebar-history";

export function DataStreamHandler() {
  const { dataStream, setDataStream } = useDataStream();
  const { mutate } = useSWRConfig();

  useEffect(() => {
    if (!dataStream?.length) {
      return;
    }

    const newDeltas = dataStream.slice();
    setDataStream([]);

    for (const delta of newDeltas) {
      // Handle chat title updates (refresh sidebar)
      if (delta.type === "data-chat-title") {
        mutate(chatHistoryKey);
        continue;
      }
    }
  }, [dataStream, setDataStream, mutate]);

  return null;
}
