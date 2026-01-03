import { Suspense } from "react";
import { Chat } from "@/components/chat";
import { DataStreamHandler } from "@/components/data-stream-handler";

export default function Page() {
  return (
    <Suspense fallback={<div className="flex h-dvh" />}>
      <NewChatPage />
    </Suspense>
  );
}

async function NewChatPage() {
  const id = crypto.randomUUID();
  return (
    <>
      <Chat autoResume={false} id={id} initialMessages={[]} key={id} />
      <DataStreamHandler />
    </>
  );
}
