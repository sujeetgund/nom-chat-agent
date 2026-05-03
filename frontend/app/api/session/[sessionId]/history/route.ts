import { NextResponse } from "next/server";
import { getHistoryServerAction } from "../../../../actions/session";

export async function GET(
  _req: Request,
  { params }: { params: { sessionId: string } },
) {
  try {
    const data = await getHistoryServerAction(params.sessionId);
    return NextResponse.json(data);
  } catch (err: any) {
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
