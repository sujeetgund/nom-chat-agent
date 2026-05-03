"use client";

import { Message } from "@/lib/types";
import { MarkdownContent } from "@/components/markdown/MarkdownContent";
import { useEffect, useRef } from "react";

interface MessageProps {
  message: Message;
}

export function MessageComponent({ message }: MessageProps) {
  const isUser = message.role === "user";
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, []);

  return (
    <div
      ref={contentRef}
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4 animate-in`}
    >
      <div
        className={`max-w-2xl rounded-lg px-4 py-3 ${
          isUser
            ? "bg-[#cc785c] text-white rounded-br-none"
            : "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-bl-none border border-slate-200 dark:border-slate-700"
        }`}
      >
        <div className="prose prose-sm dark:prose-invert max-w-none">
          {isUser ? (
            <p className="m-0 whitespace-pre-wrap">{message.content}</p>
          ) : (
            <MarkdownContent content={message.content} />
          )}
        </div>

        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">
              Tools used:
            </p>
            {message.toolCalls.map((tool) => (
              <div
                key={tool.id}
                className="text-xs bg-slate-50 dark:bg-slate-900 p-2 rounded mb-2"
              >
                <p className="font-mono text-slate-600 dark:text-slate-300">
                  {tool.name}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
