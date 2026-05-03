import { Message, Artifact } from "@/lib/types";
import { MarkdownContent } from "@/components/markdown/MarkdownContent";
import { useEffect, useRef } from "react";

interface MessageProps {
  message: Message;
}

/**
 * Parse display info from an artifact URL.
 * e.g. "/artifacts/PRD_2026-05-03_build-a-meeting-agent.md"
 *   -> { type: "PRD", title: "build a meeting agent" }
 */
function parseArtifactDisplay(url: string): { type: string; title: string; filename: string } {
  const filename = url.split("/").pop() || "";
  const withoutExt = filename.replace(/\.md$/, "");

  // Pattern: TYPE_DATE_slug
  const match = withoutExt.match(/^(PRD|PROPOSAL)_\d{4}-\d{2}-\d{2}_(.+)$/);
  if (match) {
    const type = match[1] === "PRD" ? "PRD" : "Proposal";
    const title = match[2].replace(/-/g, " ");
    return { type, title, filename };
  }

  return { type: "Document", title: withoutExt.replace(/-/g, " "), filename };
}

export function MessageComponent({ message }: MessageProps) {
  const isUser = message.role === "user";
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, []);

  const handleOpenArtifact = (filename: string) => {
    window.open(`/artifact/${encodeURIComponent(filename)}`, "_blank");
  };

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

        {/* Artifact buttons */}
        {message.artifacts && message.artifacts.length > 0 && (
          <div className="mt-6 pt-4 border-t border-surface-dark-soft">
            <p className="text-xs font-semibold text-on-dark-soft uppercase tracking-widest mb-3">
              Generated Documents
            </p>
            <div className="flex flex-wrap gap-2">
              {message.artifacts.map((artifact, idx) => {
                const { type, title, filename } = parseArtifactDisplay(artifact.url);
                return (
                  <button
                    key={`${artifact.url}-${idx}`}
                    onClick={() => handleOpenArtifact(filename)}
                    className="group text-sm px-4 py-2.5 rounded-lg border transition-all duration-200
                      bg-surface-dark-elevated text-on-dark border-surface-dark-soft
                      hover:bg-primary hover:text-on-primary hover:border-primary
                      flex items-center gap-2.5 cursor-pointer"
                  >
                    {/* Document icon */}
                    <svg
                      className="w-4 h-4 opacity-70 group-hover:opacity-100 transition-opacity"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                      <line x1="16" y1="13" x2="8" y2="13" />
                      <line x1="16" y1="17" x2="8" y2="17" />
                      <polyline points="10 9 9 9 8 9" />
                    </svg>
                    <span className="font-medium capitalize">
                      {type}{title ? ` — ${title.slice(0, 40)}` : ""}
                    </span>
                    {/* External link icon */}
                    <svg
                      className="w-3.5 h-3.5 opacity-50 group-hover:opacity-100 transition-opacity ml-1"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                      <polyline points="15 3 21 3 21 9" />
                      <line x1="10" y1="14" x2="21" y2="3" />
                    </svg>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
