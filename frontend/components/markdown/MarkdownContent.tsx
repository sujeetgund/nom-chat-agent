"use client";

import ReactMarkdown from "react-markdown";
import { CodeBlock } from "./CodeBlock";
import { ReactNode } from "react";

interface MarkdownContentProps {
  content: string;
}

export function MarkdownContent({ content }: MarkdownContentProps) {
  return (
    <ReactMarkdown
      components={{
        code: ({
          node,
          inline,
          className,
          children,
          ...props
        }: {
          node?: any;
          inline?: boolean;
          className?: string;
          children?: ReactNode;
          [key: string]: any;
        }) => {
          const match = /language-(\w+)/.exec(className || "");
          const language = match ? match[1] : "plain";
          const code = String(children).replace(/\n$/, "");

          if (inline) {
            return (
              <code
                className="bg-slate-200 dark:bg-slate-800 px-2 py-1 rounded text-sm font-mono"
                {...props}
              >
                {code}
              </code>
            );
          }

          return <CodeBlock language={language} code={code} />;
        },
        p: ({ children }: { children?: ReactNode }) => (
          <p className="mb-3 leading-relaxed">{children}</p>
        ),
        h1: ({ children }: { children?: ReactNode }) => (
          <h1 className="text-2xl font-bold mb-2 mt-4">{children}</h1>
        ),
        h2: ({ children }: { children?: ReactNode }) => (
          <h2 className="text-xl font-bold mb-2 mt-3">{children}</h2>
        ),
        h3: ({ children }: { children?: ReactNode }) => (
          <h3 className="text-lg font-bold mb-2 mt-2">{children}</h3>
        ),
        ul: ({ children }: { children?: ReactNode }) => (
          <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>
        ),
        ol: ({ children }: { children?: ReactNode }) => (
          <ol className="list-decimal list-inside mb-3 space-y-1">
            {children}
          </ol>
        ),
        li: ({ children }: { children?: ReactNode }) => (
          <li className="mb-1">{children}</li>
        ),
        blockquote: ({ children }: { children?: ReactNode }) => (
          <blockquote className="border-l-4 border-slate-400 pl-4 italic text-slate-600 dark:text-slate-400 my-3">
            {children}
          </blockquote>
        ),
        a: ({ href, children }: { href?: string; children?: ReactNode }) => (
          <a
            href={href}
            className="text-blue-600 dark:text-blue-400 hover:underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            {children}
          </a>
        ),
        table: ({ children }: { children?: ReactNode }) => (
          <div className="overflow-x-auto my-3">
            <table className="border-collapse border border-slate-300 dark:border-slate-600 w-full">
              {children}
            </table>
          </div>
        ),
        thead: ({ children }: { children?: ReactNode }) => (
          <thead className="bg-slate-100 dark:bg-slate-800">{children}</thead>
        ),
        tbody: ({ children }: { children?: ReactNode }) => (
          <tbody>{children}</tbody>
        ),
        tr: ({ children }: { children?: ReactNode }) => (
          <tr className="border border-slate-300 dark:border-slate-600">
            {children}
          </tr>
        ),
        td: ({ children }: { children?: ReactNode }) => (
          <td className="border border-slate-300 dark:border-slate-600 p-2">
            {children}
          </td>
        ),
        th: ({ children }: { children?: ReactNode }) => (
          <th className="border border-slate-300 dark:border-slate-600 p-2 text-left">
            {children}
          </th>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
