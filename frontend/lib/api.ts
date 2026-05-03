import { ChatResponse, Message, Artifact } from "./types";

const BACKEND_URL = "/api";

// Generate UUID locally.
export async function createNewSession(): Promise<string> {
  return crypto.randomUUID();
}

export type SendMessageOptions = {
  onToken?: (token: string, runId?: string) => void;
  onStatus?: (status: { status: string; node?: string }) => void;
  onArtifact?: (artifact: Artifact) => void;
  onDone?: () => void;
};

export function sendMessage(
  sessionId: string,
  message: string,
  opts: SendMessageOptions = {},
): Promise<ChatResponse> {
  const { onToken, onStatus, onArtifact, onDone } = opts;

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
                onStatus?.({ status: payload.status, node: payload.node });
              } else if (eventType === "artifact") {
                onArtifact?.(payload as Artifact);
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

export async function getSessionHistory(sessionId: string): Promise<{ messages: Message[]; artifacts: Artifact[] }> {
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
  
  const messages: Message[] = (data.messages || []).map((m: any) => ({
    id: m.id || `msg-${Math.random()}`,
    role: m.role,
    content: m.content || "",
    timestamp: m.timestamp ? new Date(m.timestamp) : new Date(),
  }));

  // artifacts from backend are URL strings, convert to Artifact objects
  const artifacts: Artifact[] = (data.artifacts || []).map((url: string) => ({
    url: typeof url === "string" ? url : (url as any).url || "",
  }));

  return { messages, artifacts };
}
