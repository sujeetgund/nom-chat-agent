import { useEffect } from "react";

interface ArtifactModalProps {
  toolCall: any;
  onClose: () => void;
}

export function ArtifactModal({ toolCall, onClose }: ArtifactModalProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-6 animate-in fade-in duration-200">
      <div className="bg-canvas w-full max-w-4xl max-h-[85vh] rounded-xl shadow-2xl flex flex-col border border-hairline overflow-hidden animate-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-hairline bg-surface-card">
          <div className="flex items-center gap-3">
            <span className="text-primary font-bold text-xl leading-none">✱</span>
            <h3 className="font-serif text-xl tracking-tight text-ink font-semibold">
              {toolCall.name}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-hairline transition-colors text-muted hover:text-ink"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 bg-canvas text-ink text-sm">
          {toolCall.args ? (
            <pre className="font-mono whitespace-pre-wrap leading-relaxed text-body bg-surface-soft p-4 rounded-lg border border-hairline">
              {typeof toolCall.args === "string" 
                ? toolCall.args 
                : JSON.stringify(toolCall.args, null, 2)}
            </pre>
          ) : (
            <p className="text-muted italic">No content available for this artifact.</p>
          )}
        </div>
      </div>
    </div>
  );
}
