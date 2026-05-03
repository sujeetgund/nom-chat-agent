"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createNewSession } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStartAsking = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const newSessionId = await createNewSession();
      router.push(`/chat/${newSessionId}`);
    } catch (err) {
      setError("Failed to create session. Is the backend running?");
      console.error(err);
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50 dark:bg-slate-950 items-center justify-center">
      <div className="max-w-2xl w-full px-6 py-12 text-center bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-800">
        <h1 className="text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight mb-4">
          NOM Chat Agent
        </h1>
        <p className="text-lg text-slate-600 dark:text-slate-400 mb-8 max-w-lg mx-auto">
          Your intelligent AI assistant for business solutions. Experience next-generation chat interactions with real-time agent status tracking.
        </p>
        
        {error && (
          <div className="mb-6 p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        <button
          onClick={handleStartAsking}
          disabled={isLoading}
          className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-full text-lg font-medium transition-all shadow-lg hover:shadow-blue-500/30 disabled:opacity-70 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              Starting...
            </>
          ) : (
            "Start Asking"
          )}
        </button>
      </div>
    </div>
  );
}
