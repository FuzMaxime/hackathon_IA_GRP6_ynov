const OLLAMA_URL = process.env.OLLAMA_URL ?? "http://localhost:11434";
const DEFAULT_MODEL = process.env.OLLAMA_MODEL ?? "phi35-financial";

type ChatMessage = {
  role: "user" | "assistant" | "system";
  content: string;
};

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const messages = body.messages as ChatMessage[];
    const model = (body.model as string) ?? DEFAULT_MODEL;

    if (!messages?.length) {
      return Response.json({ error: "Messages requis" }, { status: 400 });
    }

    const res = await fetch(`${OLLAMA_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model, messages, stream: false }),
      signal: AbortSignal.timeout(120000),
    });

    if (!res.ok) {
      const text = await res.text();
      return Response.json(
        { error: text || "Erreur Ollama" },
        { status: res.status },
      );
    }

    const data = await res.json();
    return Response.json({ content: data.message?.content ?? "" });
  } catch {
    return Response.json(
      { error: "Impossible de joindre Ollama" },
      { status: 503 },
    );
  }
}
