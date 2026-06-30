import { getSession } from "@/lib/auth";
import { createConversation, getUserConversations } from "@/lib/conversations";
import { NextResponse } from "next/server";

export async function GET() {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const conversations = await getUserConversations(session.userId);
  return NextResponse.json({ conversations });
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const body = await request.json().catch(() => ({}));
  const title = body.title as string | undefined;

  const id = await createConversation(session.userId, title);
  return NextResponse.json({ id });
}
