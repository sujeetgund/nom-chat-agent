"use client";

import { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { Message } from "@/lib/types";
import { sendMessage, createNewSession, getSessionHistory } from "@/lib/api";
import { MessageList } from "@/components/chat/MessageList";
import { ChatInput } from "@/components/chat/ChatInput";

export default function ChatPage({ params }: { params: Promise<{ sessionId: string }> }) {
  const resolvedParams = use(params);
  const sessionId = resolvedParams.sessionId;

  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agentStatus, setAgentStatus] = useState<string | null>(null);

  const router = useRouter();

  // Fetch session history on mount
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const history = await getSessionHistory(sessionId);
        setMessages(history || []);
      } catch (err) {
        setError("Failed to fetch session history.");
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

    // Add user message to UI optimistically
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: userMessage,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setError(null);

    // Create an assistant placeholder that we'll stream tokens into
    const assistantId = `assistant-${Date.now()}`;
    const assistantPlaceholder: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, assistantPlaceholder]);

    try {
      await sendMessage(sessionId, userMessage, {
        onToken(token) {
          setMessages((prev) => {
            const msgs = [...prev];
            for (let i = msgs.length - 1; i >= 0; i--) {
              if (msgs[i].id === assistantId) {
                msgs[i] = { ...msgs[i], content: msgs[i].content + token };
                break;
              }
            }
            return msgs;
          });
        },
        onStatus(status) {
          setAgentStatus(status?.message || status?.status || null);
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
    }
  };

  return (
    <div className="flex flex-col h-screen bg-white dark:bg-slate-950">
      <header className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 
              className="text-2xl font-bold text-slate-900 dark:text-white cursor-pointer hover:opacity-80 transition-opacity" 
              onClick={() => router.push('/')}
            >
              NOM Chat Agent
            </h1>
            <div className="flex items-center gap-3 mt-1">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Session: {sessionId.slice(0, 8)}...
              </p>
              {agentStatus ? (
                <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 flex items-center gap-2 animate-pulse border border-blue-200 dark:border-blue-800">
                  <span className="w-2 h-2 rounded-full bg-blue-600 dark:bg-blue-400"></span>
                  {agentStatus}
                </span>
              ) : null}
            </div>
          </div>
          <button
            onClick={async () => {
              try {
                const newId = await createNewSession();
                router.push(`/chat/${newId}`);
              } catch (err) {
                setError("Failed to create session");
              }
            }}
            className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 transition-colors text-white px-3 py-1 rounded-md text-sm"
          >
            New Chat
          </button>
        </div>
      </header>

      {error && (
        <div className="bg-red-50 dark:bg-red-900 border-b border-red-200 dark:border-red-800 px-6 py-3">
          <div className="max-w-4xl mx-auto">
            <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
          </div>
        </div>
      )}

      <div className="max-w-4xl mx-auto w-full flex-1 flex flex-col overflow-hidden">
        <MessageList messages={messages} isLoading={isLoading} />
        <ChatInput onSubmit={handleSendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
}
