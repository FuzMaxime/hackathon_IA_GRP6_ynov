import { getSession } from "@/lib/auth";
import {
  getLatestConversation,
  getMessages,
  getUserConversations,
} from "@/lib/conversations";
import { NextResponse } from "next/server";

export async function GET() {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ user: null }, { status: 401 });
  }

  const conversations = await getUserConversations(session.userId);
  const latest = await getLatestConversation(session.userId);
  const messages = latest ? await getMessages(latest.id) : [];

  return NextResponse.json({
    user: { id: session.userId, username: session.username },
    conversations,
    activeConversationId: latest?.id ?? null,
    messages: messages.map((m) => ({ role: m.role, content: m.content })),
  });
}
