import { NextResponse } from "next/server";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_BASE_URL || "http://localhost:8000";

export async function GET(req: Request) {
  try {
    const url = new URL(req.url);
    const sessionId = url.searchParams.get("sessionId");
    const message = url.searchParams.get("message") || "";

    if (!sessionId) {
      return NextResponse.json({ error: "missing sessionId" }, { status: 400 });
    }

    const backendUrl = `${BACKEND_URL}/chat/${encodeURIComponent(sessionId)}?message=${encodeURIComponent(
      message,
    )}`;

    const res = await fetch(backendUrl, { method: "GET" });

    if (!res.ok || !res.body) {
      return NextResponse.json({ error: "upstream error" }, { status: 502 });
    }

    // Stream backend response body directly to client
    const { readable, writable } = new TransformStream();

    // Pipe backend body to our writable
    res.body.pipeTo(writable).catch(() => {
      try {
        writable.close();
      } catch {}
    });

    return new Response(readable, {
      status: 200,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache, no-transform",
        Connection: "keep-alive",
      },
    });
  } catch (err: any) {
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
