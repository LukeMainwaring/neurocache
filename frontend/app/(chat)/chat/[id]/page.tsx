import { Suspense } from "react";

import { Chat } from "@/components/chat";
import { DataStreamHandler } from "@/components/data-stream-handler";
import { getThreadMessages } from "@/lib/api/backend-client";

export default function Page(props: { params: Promise<{ id: string }> }) {
  return (
    <Suspense fallback={<div className="flex h-dvh" />}>
      <ChatPage params={props.params} />
    </Suspense>
  );
}

async function ChatPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const initialMessages = await getThreadMessages(id);

  return (
    <>
      <Chat autoResume={true} id={id} initialMessages={initialMessages} />
      <DataStreamHandler />
    </>
  );
}
