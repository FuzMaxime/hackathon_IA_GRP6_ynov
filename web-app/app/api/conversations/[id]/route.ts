import { getSession } from "@/lib/auth";
import {
  getConversationForUser,
  getMessages,
} from "@/lib/conversations";
import { NextResponse } from "next/server";

type Params = { params: Promise<{ id: string }> };

export async function GET(_request: Request, { params }: Params) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const { id } = await params;
  const conversationId = Number(id);
  if (Number.isNaN(conversationId)) {
    return NextResponse.json({ error: "ID invalide" }, { status: 400 });
  }

  const conversation = await getConversationForUser(
    conversationId,
    session.userId,
  );
  if (!conversation) {
    return NextResponse.json(
      { error: "Conversation introuvable" },
      { status: 404 },
    );
  }

  const messages = await getMessages(conversationId);
  return NextResponse.json({
    conversation,
    messages: messages.map((m) => ({ role: m.role, content: m.content })),
  });
}
