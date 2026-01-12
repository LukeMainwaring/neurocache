/**
 * Proxy route for chat - forwards requests to backend
 */
export async function POST(request: Request) {
  const body = await request.json();

  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
  const streamUrl = `${backendUrl}/api/chat/stream`;

  // Extract the latest user message content
  const userMessage = body.messages
    ? body.messages[body.messages.length - 1]
    : null;

  if (!userMessage || userMessage.role !== "user") {
    return new Response(JSON.stringify({ error: "No user message found" }), {
      status: 400,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }

  // Extract text content from message parts
  const content =
    userMessage.parts?.find((p: any) => p.type === "text")?.text ||
    userMessage.content ||
    "";

  // Prepare request for backend
  const backendPayload = {
    content,
    thread_id: body.id, // useChat sends the chat ID
  };

  // Forward the request to the backend
  const response = await fetch(streamUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(backendPayload),
    credentials: "include",
  });

  // Return the streaming response with headers from backend
  return new Response(response.body, {
    headers: {
      "Content-Type": "text/plain",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
      // Forward the protocol version header from backend (required for Vercel AI SDK)
      "x-vercel-ai-ui-message-stream":
        response.headers.get("x-vercel-ai-ui-message-stream") || "v1",
    },
  });
}
