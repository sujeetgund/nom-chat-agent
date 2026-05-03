export interface Artifact {
  url: string; // e.g. "/artifacts/PRD_2026-05-03_project-name.md"
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  artifacts?: Artifact[];
}

export interface ChatSession {
  sessionId: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

export interface ChatRequest {
  message: string;
  sessionId?: string;
}

export interface ChatResponse {
  sessionId: string;
  messages: Message[];
  status: "success" | "error";
  error?: string;
}
