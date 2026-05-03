import { Message } from "@/lib/types";
import { MarkdownContent } from "@/components/markdown/MarkdownContent";
import { useEffect, useRef, useState } from "react";
import { ArtifactModal } from "./ArtifactModal";

interface MessageProps {
  message: Message;
}

export function MessageComponent({ message }: MessageProps) {
  const isUser = message.role === "user";
  const contentRef = useRef<HTMLDivElement>(null);
  const [selectedArtifact, setSelectedArtifact] = useState<any>(null);

  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, []);

  return (
    <div
      ref={contentRef}
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-8 animate-in`}
    >
      <div
        className={`max-w-3xl w-full rounded-xl px-6 py-5 ${
          isUser
            ? "bg-surface-card text-ink border border-hairline rounded-tr-none ml-12"
            : "bg-surface-dark text-on-dark rounded-tl-none mr-12 shadow-md"
        }`}
      >
        {!isUser && (
          <div className="flex items-center gap-2 mb-4 border-b border-surface-dark-soft pb-3">
            <span className="text-primary font-bold text-lg leading-none">✱</span>
            <span className="text-on-dark-soft text-sm font-medium">NOM Assistant</span>
          </div>
        )}
        <div className={`prose prose-sm max-w-none ${isUser ? "prose-slate" : "prose-invert"}`}>
          {isUser ? (
            <p className="m-0 whitespace-pre-wrap text-base">{message.content}</p>
          ) : (
            <MarkdownContent content={message.content} />
          )}
        </div>

        {(message.toolCalls && message.toolCalls.length > 0) && (
          <div className="mt-6 pt-4 border-t border-surface-dark-soft">
            <p className="text-xs font-semibold text-on-dark-soft uppercase tracking-widest mb-3">
              Generated Artifacts
            </p>
            <div className="flex flex-wrap gap-2">
              {message.toolCalls.map((tool) => {
                const result = message.toolResults?.find(r => r.toolCallId === tool.id)?.result;
                return (
                  <button
                    key={tool.id}
                    onClick={() => setSelectedArtifact({ ...tool, result })}
                    className={`text-xs px-3 py-1.5 rounded-md border transition-colors flex items-center gap-2 ${
                      result 
                        ? "bg-primary text-on-primary border-primary hover:bg-primary-dark" 
                        : "bg-surface-dark-elevated text-on-dark border-surface-dark-soft hover:bg-surface-dark-soft"
                    }`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${result ? "bg-accent-amber animate-pulse" : "bg-muted"}`}></span>
                    {tool.name}
                    {result && (
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                      </svg>
                    )}
                    <svg className="ml-1 opacity-60" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="15 3 21 3 21 9"></polyline>
                      <line x1="10" y1="14" x2="21" y2="3"></line>
                    </svg>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {selectedArtifact && (
        <ArtifactModal 
          toolCall={selectedArtifact} 
          onClose={() => setSelectedArtifact(null)} 
        />
      )}
    </div>
  );
}
