"use server";

import { NextRequest } from "next/server";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_BASE_URL || "http://localhost:8000";

export async function createSessionServerAction(): Promise<string> {
  const res = await fetch(`${BACKEND_URL}/chat/session`, {
    method: "POST",
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to create session on backend");
  const data = await res.json();
  return data.session_id || data.sessionId;
}

export async function getHistoryServerAction(sessionId: string): Promise<any> {
  const res = await fetch(
    `${BACKEND_URL}/chat/${encodeURIComponent(sessionId)}/history`,
    {
      method: "GET",
      cache: "no-store",
    },
  );
  if (!res.ok) throw new Error("Failed to fetch history from backend");
  return await res.json();
}
