/**
 * Proxy route for chat - forwards requests to backend.
 *
 * The Vercel AI SDK useChat hook sends the full request body
 * (including trigger, id, and messages) which the backend's
 * VercelAIAdapter consumes directly.
 */
export async function POST(request: Request) {
  const body = await request.json();

  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const authHeader = request.headers.get("Authorization");
  if (authHeader) {
    headers.Authorization = authHeader;
  }

  const response = await fetch(`${backendUrl}/api/chat/stream`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
    credentials: "include",
  });

  return new Response(response.body, {
    status: response.status,
    headers: Object.fromEntries(response.headers.entries()),
  });
}
