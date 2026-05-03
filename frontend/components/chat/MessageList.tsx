import { Message } from "@/lib/types";
import { MessageComponent } from "./Message";
import { useEffect, useRef, useState } from "react";

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
  agentStatus: string | null;
}

const STATUS_LABELS: Record<string, string> = {
  thinking: "Thinking",
  researching: "Searching the web",
  searching_kb: "Searching knowledge base",
  writing_prd: "Writing PRD",
  writing_proposal: "Writing proposal",
};

export function MessageList({ messages, isLoading, agentStatus }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [displayedStatus, setDisplayedStatus] = useState<string | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Animate status transitions
  useEffect(() => {
    if (agentStatus) {
      setDisplayedStatus(agentStatus);
    } else {
      // Small delay before clearing so the fade-out animation plays
      const timer = setTimeout(() => setDisplayedStatus(null), 300);
      return () => clearTimeout(timer);
    }
  }, [agentStatus]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-canvas">
        <div className="w-16 h-16 bg-surface-card rounded-full flex items-center justify-center mb-6 shadow-sm border border-hairline">
          <span className="text-3xl text-primary">✱</span>
        </div>
        <h2 className="text-2xl font-serif text-ink tracking-tight mb-3">
          How can I help you today?
        </h2>
        <p className="text-muted text-base max-w-sm">
          Ask me to analyze data, write code, or solve complex problems.
        </p>
      </div>
    );
  }

  const statusLabel = displayedStatus ? STATUS_LABELS[displayedStatus] || displayedStatus.replace(/_/g, " ") : null;

  return (
    <div className="flex-1 overflow-y-auto px-6 py-8 bg-canvas pb-40">
      <div className="max-w-4xl mx-auto flex flex-col w-full">
        {messages.map((message) => (
          <MessageComponent key={message.id} message={message} />
        ))}

        {/* Loading indicator with live status */}
        {isLoading && (
          <div className="flex justify-start mb-8 items-center gap-3">
            <div className="bg-surface-dark w-14 h-10 rounded-xl flex items-center justify-center shadow-md">
              <div className="flex space-x-1">
                <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
            {statusLabel && (
              <span
                key={displayedStatus}
                className={`text-xs font-medium text-muted-soft px-3 py-1 rounded-full
                  border border-hairline-soft bg-surface-soft/50
                  capitalize tracking-wide
                  animate-in fade-in slide-in-from-left-2 duration-300`}
              >
                {statusLabel}
              </span>
            )}
          </div>
        )}
        <div ref={bottomRef} className="h-4" />
      </div>
    </div>
  );
}
