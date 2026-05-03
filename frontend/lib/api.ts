import { ChatRequest, ChatResponse, Message } from "./types";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_BASE_URL || "http://localhost:8000";

// Since backend does not require session creation, we'll generate UUID locally.
export async function createNewSession(): Promise<string> {
  return crypto.randomUUID();
}

export type SendMessageOptions = {
  onToken?: (token: string, runId?: string) => void;
  onStatus?: (status: { status: string; message?: string }) => void;
  onToolCall?: (toolCall: { name: string; args: any }, runId?: string) => void;
  onDone?: () => void;
};

export function sendMessage(
  sessionId: string,
  message: string,
  opts: SendMessageOptions = {},
): Promise<ChatResponse> {
  const { onToken, onStatus, onToolCall, onDone } = opts;

  return new Promise<ChatResponse>(async (resolve, reject) => {
    try {
      const response = await fetch(`${BACKEND_URL}/chat/${encodeURIComponent(sessionId)}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error("No response body");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      
      let assistantText = "";
      let finalStatus = "idle";
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";

        for (const event of events) {
          if (!event.trim()) continue;
          
          const lines = event.split("\n");
          let eventType = "message";
          let dataStr = "";

          for (const line of lines) {
            if (line.startsWith("event: ")) {
              eventType = line.slice("event: ".length).trim();
            } else if (line.startsWith("data: ")) {
              dataStr = line.slice("data: ".length).trim();
            }
          }

          if (dataStr) {
            try {
              const payload = JSON.parse(dataStr);
              if (eventType === "message") {
                const token = payload.text || "";
                assistantText += token;
                onToken?.(token, payload.run_id);
              } else if (eventType === "status") {
                finalStatus = payload.status || finalStatus;
                onStatus?.({ status: payload.status });
              } else if (eventType === "tool_call") {
                onToolCall?.(payload, payload.run_id);
              } else if (eventType === "error") {
                console.error("Backend stream error:", payload.detail);
              }
            } catch (err) {
              console.error("Failed to parse SSE JSON payload:", err, dataStr);
            }
          }
        }
      }

      onDone?.();

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
    } catch (err) {
      reject(err as Error);
    }
  });
}

export async function getSessionHistory(sessionId: string): Promise<Message[]> {
  const response = await fetch(
    `${BACKEND_URL}/chat/${encodeURIComponent(sessionId)}/history`,
    {
      method: "GET",
    },
  );

  if (!response.ok) {
    throw new Error("Failed to fetch history");
  }

  const data = await response.json();
  
  // Transform the history to the frontend Message type format
  return (data.messages || [])
    .filter((m: any) => m.type === "ai" || m.type === "human")
    .map((m: any, i: number) => ({
      id: `msg-${i}-${Date.now()}`,
      role: m.type === "ai" ? "assistant" : "user",
      content: m.content || "",
      timestamp: new Date(),
      toolCalls: (m.tool_calls || []).map((tc: any) => ({
        id: tc.id || `tool-${Math.random()}`,
        name: tc.name || "",
        args: tc.args || {}
      })),
    }));
}
