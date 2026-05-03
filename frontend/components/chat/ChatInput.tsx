import { useState, useRef, useEffect } from "react";

interface ChatInputProps {
  onSubmit: (message: string) => void;
  isLoading: boolean;
}

export function ChatInput({ onSubmit, isLoading }: ChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSubmit = () => {
    if (input.trim() && !isLoading) {
      onSubmit(input.trim());
      setInput("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 w-full max-w-3xl px-4 z-20">
      <div className="bg-surface-card rounded-xl shadow-[0_4px_24px_rgba(20,20,19,0.08)] border border-hairline overflow-hidden transition-all focus-within:border-primary/30 focus-within:shadow-[0_4px_24px_rgba(204,120,92,0.1)]">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask NOM a question..."
          className="w-full max-h-[200px] min-h-[56px] resize-none bg-transparent py-4 px-5 outline-none text-ink text-base placeholder:text-muted focus:ring-0 leading-relaxed"
          rows={1}
          disabled={isLoading}
        />
        <div className="flex items-center justify-between px-3 pb-3">
          <div className="text-xs text-muted-soft font-medium flex items-center gap-1.5 ml-2">
            <span className="w-1.5 h-1.5 rounded-full bg-success"></span>
            NOM is ready
          </div>
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || isLoading}
            className="w-9 h-9 flex items-center justify-center rounded-md bg-primary text-on-primary disabled:opacity-50 disabled:bg-hairline disabled:text-muted transition-colors hover:bg-primary-active"
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="19" x2="12" y2="5"></line>
                <polyline points="5 12 12 5 19 12"></polyline>
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
