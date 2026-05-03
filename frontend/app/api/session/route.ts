import { NextResponse } from "next/server";
import { createSessionServerAction } from "../../actions/session";

export async function POST() {
  try {
    const sessionId = await createSessionServerAction();
    return NextResponse.json({ session_id: sessionId });
  } catch (err: any) {
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
