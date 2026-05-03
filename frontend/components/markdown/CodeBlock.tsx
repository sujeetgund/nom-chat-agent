"use client";

import { useEffect, useRef } from "react";

interface CodeBlockProps {
  language?: string;
  code: string;
}

export function CodeBlock({ language = "plain", code }: CodeBlockProps) {
  const ref = useRef<HTMLPreElement>(null);

  useEffect(() => {
    if (ref.current && typeof window !== "undefined") {
      // Dynamic highlight.js import
      import("highlight.js").then((hljs) => {
        if (ref.current) {
          ref.current.classList.add(`language-${language}`);
          ref.current.textContent = code;
          // Use the default export
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
