import { ChatRequest, ChatResponse, Message } from "./types";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_BASE_URL || "http://localhost:8000";

// Use local Next.js server routes under /api to perform server-side requests
const API_BASE = ""; // relative to same origin

export async function createNewSession(): Promise<string> {
  const response = await fetch(`${API_BASE}/api/session`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("Failed to create session");
  }

  const data = await response.json();
  return (data.session_id || data.sessionId) as string;
}

export type SendMessageOptions = {
  onToken?: (token: string) => void;
  onStatus?: (status: { status: string; message?: string }) => void;
  onDone?: () => void;
};

export function sendMessage(
  sessionId: string,
  message: string,
  opts: SendMessageOptions = {},
): Promise<ChatResponse> {
  const { onToken, onStatus, onDone } = opts;

  return new Promise<ChatResponse>((resolve, reject) => {
    try {
      const url = `/api/chat?sessionId=${encodeURIComponent(
        sessionId,
      )}&message=${encodeURIComponent(message)}`;

      const es = new EventSource(url);

      let assistantText = "";
      let finalStatus = "idle";

      es.addEventListener("status", (e: MessageEvent) => {
        try {
          const payload = JSON.parse(e.data);
          finalStatus = payload.status || finalStatus;
          onStatus?.(payload);
        } catch (err) {
          // ignore malformed
        }
      });

      es.addEventListener("token", (e: MessageEvent) => {
        try {
          const payload = JSON.parse(e.data);
          const token = payload.token || "";
          assistantText += token;
          onToken?.(token);
        } catch (err) {
          // ignore
        }
      });

      es.addEventListener("done", (e: MessageEvent) => {
        try {
          const payload = JSON.parse(e.data || "{}");
          finalStatus = payload.status || finalStatus;
        } catch (err) {
          // ignore
        }
        onDone?.();
        es.close();

        const resp: ChatResponse = {
          sessionId,
          status: "success",
          messages: [
            {
              id: `assistant-${Date.now()}`,
              role: "assistant",
              content: assistantText,
              timestamp: new Date(),
            },
          ],
        };

        resolve(resp);
      });

      es.onerror = (err) => {
        es.close();
        reject(new Error("SSE connection error"));
      };
    } catch (err) {
      reject(err as Error);
    }
  });
}

export async function getSessionHistory(sessionId: string): Promise<Message[]> {
  const response = await fetch(
    `/api/session/${encodeURIComponent(sessionId)}/history`,
    {
      method: "GET",
    },
  );

  if (!response.ok) {
    throw new Error("Failed to fetch history");
  }

  const data = await response.json();
  return data.messages as Message[];
}
