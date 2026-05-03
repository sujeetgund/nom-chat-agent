"use client";

import { useState, useEffect, use } from "react";
import { MarkdownContent } from "@/components/markdown/MarkdownContent";

export default function ArtifactViewerPage({
  params,
}: {
  params: Promise<{ filename: string }>;
}) {
  const resolvedParams = use(params);
  const filename = decodeURIComponent(resolvedParams.filename);

  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchArtifact = async () => {
      try {
        const response = await fetch(`/api/artifacts/${encodeURIComponent(filename)}`);
        if (!response.ok) {
          throw new Error(
            response.status === 404
              ? "Artifact not found"
              : `Failed to fetch artifact: ${response.statusText}`
          );
        }
        const text = await response.text();
        setContent(text);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load artifact");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchArtifact();
  }, [filename]);

  // Derive a nice title from the filename
  const displayTitle = filename
    .replace(/\.md$/, "")
    .replace(/^(PRD|PROPOSAL)_/, (match) => match.replace("_", " — ").trim() + " ")
    .replace(/_/g, " ");

  return (
    <div className="min-h-screen bg-canvas text-ink font-sans">
      {/* Header */}
      <header className="h-16 border-b border-hairline flex items-center justify-between px-6 bg-canvas/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <span className="text-primary font-bold text-xl leading-none">✱</span>
          <h1 className="font-serif text-lg tracking-tight font-semibold truncate max-w-[600px]">
            {displayTitle}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              if (content) {
                const blob = new Blob([content], { type: "text/markdown" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = filename;
                a.click();
                URL.revokeObjectURL(url);
              }
            }}
            disabled={!content}
            className="text-sm font-medium border border-hairline px-3 py-1.5 rounded-md
              hover:bg-surface-card hover:text-primary transition-colors
              disabled:opacity-40 disabled:cursor-not-allowed
              flex items-center gap-2"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Download
          </button>
          <button
            onClick={() => window.print()}
            className="text-sm font-medium border border-hairline px-3 py-1.5 rounded-md
              hover:bg-surface-card hover:text-primary transition-colors
              flex items-center gap-2"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="6 9 6 2 18 2 18 9" />
              <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
              <rect x="6" y="14" width="12" height="8" />
            </svg>
            Print
          </button>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-6 py-10">
        {loading && (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <p className="text-muted text-sm">Loading artifact…</p>
          </div>
        )}

        {error && (
          <div className="bg-error/10 border border-error/30 text-error rounded-lg px-6 py-4 text-sm">
            {error}
          </div>
        )}

        {content && (
          <article className="prose prose-lg max-w-none prose-slate
            prose-headings:font-serif prose-headings:tracking-tight
            prose-h1:text-3xl prose-h1:mb-6
            prose-h2:text-2xl prose-h2:mt-10 prose-h2:mb-4
            prose-h3:text-xl prose-h3:mt-8 prose-h3:mb-3
            prose-p:leading-relaxed prose-p:text-body
            prose-li:text-body
            prose-strong:text-ink
            prose-a:text-primary prose-a:no-underline hover:prose-a:underline
            print:prose-sm"
          >
            <MarkdownContent content={content} />
          </article>
        )}
      </main>

      {/* Print styles */}
      <style dangerouslySetInnerHTML={{ __html: `
        @media print {
          header, button { display: none !important; }
          main { padding: 0 !important; max-width: none !important; }
          body { background: white !important; }
        }
      `}} />
    </div>
  );
}
