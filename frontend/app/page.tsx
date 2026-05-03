"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createNewSession } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const handleStartAsking = async () => {
    setIsLoading(true);
    try {
      const newSessionId = await createNewSession();
      router.push(`/chat/${newSessionId}`);
    } catch (err) {
      console.error(err);
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-canvas text-ink">
      {/* Top Nav */}
      <header className="h-16 border-b border-hairline flex items-center px-6 sticky top-0 bg-canvas/80 backdrop-blur-md z-10">
        <div className="max-w-6xl w-full mx-auto flex items-center justify-between">
          <div className="font-serif text-2xl tracking-tight text-ink font-bold flex items-center gap-2">
            <span className="text-xl">✱</span> NOM Chat
          </div>
          <div className="flex items-center gap-6">
            <button className="text-sm font-medium hover:text-primary transition-colors">Sign in</button>
            <button
              onClick={handleStartAsking}
              className="bg-primary text-on-primary px-5 py-2 rounded-md font-medium text-sm hover:bg-primary-active transition-colors shadow-sm"
            >
              Try NOM
            </button>
          </div>
        </div>
      </header>

      {/* Hero Band */}
      <main className="flex-1 flex flex-col pt-24 pb-32">
        <div className="max-w-6xl mx-auto w-full px-6 grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
          
          <div className="flex flex-col gap-8">
            <h1 className="font-serif text-6xl md:text-7xl leading-[1.05] tracking-[-0.02em] text-ink max-w-lg">
              Meet your thinking partner
            </h1>
            <p className="text-body text-lg max-w-md leading-relaxed">
              NOM is an advanced AI agent designed to help you analyze, understand, and build. Fast, capable, and highly agentic.
            </p>
            <div className="pt-4 flex items-center gap-4">
              <button
                onClick={handleStartAsking}
                disabled={isLoading}
                className="bg-primary text-on-primary px-6 py-3 rounded-md font-medium flex items-center gap-2 hover:bg-primary-active transition-colors disabled:opacity-70 disabled:cursor-not-allowed text-base shadow-sm"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                    Starting...
                  </>
                ) : (
                  "Talk to NOM"
                )}
              </button>
              <button className="bg-transparent text-ink px-6 py-3 rounded-md font-medium border border-hairline hover:bg-surface-card transition-colors text-base">
                Read Research
              </button>
            </div>
          </div>

          <div className="bg-surface-dark text-on-dark rounded-xl p-8 shadow-2xl relative overflow-hidden aspect-[4/3] flex flex-col border border-surface-dark-elevated">
            <div className="flex items-center gap-2 mb-6 border-b border-surface-dark-soft pb-4">
              <div className="w-3 h-3 rounded-full bg-[#FF5F56]"></div>
              <div className="w-3 h-3 rounded-full bg-[#FFBD2E]"></div>
              <div className="w-3 h-3 rounded-full bg-[#27C93F]"></div>
              <div className="ml-4 text-xs font-mono text-muted-soft">NOM Terminal</div>
            </div>
            
            <div className="font-mono text-sm leading-relaxed text-on-dark-soft flex-1">
              <div className="flex items-start gap-3">
                <span className="text-primary mt-1">❯</span>
                <p className="text-on-dark">Analyzing architectural constraints...</p>
              </div>
              <div className="flex items-start gap-3 mt-4">
                <span className="text-accent-teal mt-1">✓</span>
                <p>Dependency graph compiled.</p>
              </div>
              <div className="flex items-start gap-3 mt-2">
                <span className="text-accent-teal mt-1">✓</span>
                <p>Postgres context instantiated.</p>
              </div>
              <div className="flex items-start gap-3 mt-6">
                <span className="text-primary mt-1">❯</span>
                <p className="text-on-dark animate-pulse">Generating optimizations...</p>
              </div>
            </div>
          </div>
          
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-surface-dark text-on-dark-soft py-16 px-6 mt-auto">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between gap-8">
          <div className="font-serif text-xl tracking-tight text-on-dark flex items-center gap-2">
            <span className="text-lg">✱</span> NOM
          </div>
          <div className="text-sm">
            © {new Date().getFullYear()} NOM Research. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
