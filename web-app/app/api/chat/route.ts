import { getSession } from "@/lib/auth";
import {
  addMessage,
  getMessages,
  getOrCreateConversation,
} from "@/lib/conversations";
import { NextResponse } from "next/server";

const OLLAMA_URL = process.env.OLLAMA_URL ?? "http://localhost:11434";
const DEFAULT_MODEL = process.env.OLLAMA_MODEL ?? "phi35-financial";
const MAX_CONTEXT_MESSAGES = 20;

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  try {
    const body = await request.json();
    const content = (body.content as string)?.trim();
    const conversationId = body.conversationId as number | undefined;

    if (!content) {
      return NextResponse.json({ error: "Message requis" }, { status: 400 });
    }

    const activeConversationId = await getOrCreateConversation(
      session,
      conversationId,
    );

    await addMessage(activeConversationId, "user", content);

    const history = await getMessages(activeConversationId);
    const ollamaMessages = history.slice(-MAX_CONTEXT_MESSAGES).map((m) => ({
      role: m.role,
      content: m.content,
    }));

    const res = await fetch(`${OLLAMA_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: (body.model as string) ?? DEFAULT_MODEL,
        messages: ollamaMessages,
        stream: false,
      }),
      signal: AbortSignal.timeout(120000),
    });

    if (!res.ok) {
      const text = await res.text();
      return NextResponse.json(
        { error: text || "Erreur Ollama" },
        { status: res.status },
      );
    }

    const data = await res.json();
    const assistantContent = data.message?.content ?? "";

    await addMessage(activeConversationId, "assistant", assistantContent);

    return NextResponse.json({
      content: assistantContent,
      conversationId: activeConversationId,
    });
  } catch {
    return NextResponse.json(
      { error: "Impossible de joindre Ollama" },
      { status: 503 },
    );
  }
}
