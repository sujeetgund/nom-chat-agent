"use client";

import { useEffect, useRef, useState } from "react";

interface CodeBlockProps {
  language?: string;
  code: string;
}

// Dedicated component for rendering Mermaid diagrams
function MermaidDiagram({ code }: { code: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ref.current || typeof window === "undefined") return;

    let cancelled = false;

    import("mermaid").then((mermaidModule) => {
      if (cancelled) return;
      const mermaid = mermaidModule.default;

      mermaid.initialize({
        startOnLoad: false,
        theme: "dark",
        securityLevel: "loose",
      });

      // Generate a unique id for each diagram to avoid conflicts
      const id = `mermaid-${Math.random().toString(36).slice(2)}`;

      mermaid
        .render(id, code)
        .then(({ svg }) => {
          if (ref.current && !cancelled) {
            ref.current.innerHTML = svg;
          }
        })
        .catch((err) => {
          if (!cancelled) {
            console.error("Mermaid render error:", err);
            setError(String(err));
          }
        });
    });

    return () => {
      cancelled = true;
    };
  }, [code]);

  if (error) {
    // Fallback: show raw code with an error notice
    return (
      <div className="my-4 rounded-lg border border-red-700 bg-slate-900 overflow-x-auto">
        <div className="text-xs text-red-400 px-4 py-2 border-b border-red-700">
          mermaid — render error
        </div>
        <pre className="p-4 text-sm text-slate-300 font-mono whitespace-pre">{code}</pre>
      </div>
    );
  }

  return (
    <div className="my-4 rounded-lg border border-slate-700 bg-slate-900 p-4 overflow-x-auto">
      <div ref={ref} className="flex justify-center" />
    </div>
  );
}

export function CodeBlock({ language = "plain", code }: CodeBlockProps) {
  const ref = useRef<HTMLPreElement>(null);

  // Render Mermaid diagrams natively
  if (language === "mermaid") {
    return <MermaidDiagram code={code} />;
  }

  useEffect(() => {
    if (ref.current && typeof window !== "undefined") {
      import("highlight.js").then((hljs) => {
        if (ref.current) {
          ref.current.classList.add(`language-${language}`);
          ref.current.textContent = code;
          (hljs.default || hljs).highlightElement(ref.current);
        }
      });
    }
  }, [language, code]);

  return (
    <div className="relative overflow-x-auto bg-slate-900 rounded-lg my-4 border border-slate-700">
      {language && (
        <div className="text-xs font-mono text-slate-400 px-4 py-2 border-b border-slate-700">
          {language}
        </div>
      )}
      <pre ref={ref} className="p-4 text-sm text-slate-200 font-mono">
        {code}
      </pre>
      <button
        onClick={() => navigator.clipboard.writeText(code)}
        className="absolute top-8 right-2 px-3 py-1 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded text-xs"
      >
        Copy
      </button>
    </div>
  );
}

