"use client";

import { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { Message, Artifact } from "@/lib/types";
import { sendMessage, createNewSession, getSessionHistory } from "@/lib/api";
import { MessageList } from "@/components/chat/MessageList";
import { ChatInput } from "@/components/chat/ChatInput";

export default function ChatPage({ params }: { params: Promise<{ sessionId: string }> }) {
  const resolvedParams = use(params);
  const sessionId = resolvedParams.sessionId;

  const [messages, setMessages] = useState<Message[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agentStatus, setAgentStatus] = useState<string | null>(null);

  const router = useRouter();

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const history = await getSessionHistory(sessionId);
        let loadedMessages = history.messages || [];
        const loadedArtifacts = history.artifacts || [];

        // Attach artifacts to the last assistant message so buttons render
        if (loadedArtifacts.length > 0) {
          const lastAssistantIdx = loadedMessages
            .map((m) => m.role)
            .lastIndexOf("assistant");
          if (lastAssistantIdx !== -1) {
            loadedMessages = [...loadedMessages];
            loadedMessages[lastAssistantIdx] = {
              ...loadedMessages[lastAssistantIdx],
              artifacts: loadedArtifacts,
            };
          }
        }

        setMessages(loadedMessages);
        setArtifacts(loadedArtifacts);
      } catch (err) {
        setError("Failed to fetch session history. Backend might be down.");
        console.error(err);
      }
    };

    if (sessionId) {
      fetchHistory();
    }
  }, [sessionId]);

  const handleSendMessage = async (userMessage: string) => {
    if (!sessionId) {
      setError("Session not initialized");
      return;
    }

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: userMessage,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setError(null);

    try {
      await sendMessage(sessionId, userMessage, {
        onToken(token, runId) {
          const msgId = runId ? `assistant-${runId}` : "assistant-default";
          setMessages((prev) => {
            const msgs = [...prev];
            const idx = msgs.findIndex((m) => m.id === msgId);

            if (idx === -1) {
              msgs.push({
                id: msgId,
                role: "assistant",
                content: token,
                timestamp: new Date(),
              });
            } else {
              msgs[idx] = { ...msgs[idx], content: msgs[idx].content + token };
            }
            return msgs;
          });
        },
        onStatus(status) {
          if (status?.status && status.status !== "idle") {
            setAgentStatus(status.status);
          } else {
            setAgentStatus(null);
          }
        },
        onArtifact(artifact) {
          // Add artifact to the session-level list
          setArtifacts((prev) => [...prev, artifact]);
          // Also attach it to the latest assistant message
          setMessages((prev) => {
            const msgs = [...prev];
            const lastAssistantIdx = msgs.map(m => m.role).lastIndexOf("assistant");
            if (lastAssistantIdx !== -1) {
              const existing = msgs[lastAssistantIdx].artifacts || [];
              msgs[lastAssistantIdx] = {
                ...msgs[lastAssistantIdx],
                artifacts: [...existing, artifact],
              };
            }
            return msgs;
          });
        },
        onDone() {
          setIsLoading(false);
          setAgentStatus(null);
        },
      });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to send message";
      setError(errorMessage);
      console.error(err);
      setIsLoading(false);
      setAgentStatus(null);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-canvas font-sans text-ink relative">
      <header className="h-16 border-b border-hairline flex items-center justify-between px-6 bg-canvas/80 backdrop-blur-sm z-10 sticky top-0 shrink-0">
        <div 
          className="font-serif text-xl font-bold tracking-tight cursor-pointer hover:text-primary transition-colors flex items-center gap-2"
          onClick={() => router.push('/')}
        >
          <span className="text-lg">✱</span> NOM Chat
        </div>
        
        <div className="flex items-center gap-4">
          <button
            onClick={async () => {
              try {
                const newId = await createNewSession();
                router.push(`/chat/${newId}`);
              } catch (err) {
                setError("Failed to create session");
              }
            }}
            className="text-sm font-medium hover:text-primary transition-colors border border-hairline px-3 py-1.5 rounded-md hover:bg-surface-card"
          >
            New Chat
          </button>
        </div>
      </header>

      {error && (
        <div className="bg-error text-on-primary px-6 py-3 text-sm font-medium text-center shrink-0">
          {error}
        </div>
      )}

      <MessageList messages={messages} isLoading={isLoading} agentStatus={agentStatus} />
      
      <ChatInput onSubmit={handleSendMessage} isLoading={isLoading} />
    </div>
  );
}
