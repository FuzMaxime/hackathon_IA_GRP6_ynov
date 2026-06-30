const OLLAMA_URL = process.env.OLLAMA_URL ?? "http://localhost:11434";

export async function GET() {
  try {
    const res = await fetch(`${OLLAMA_URL}/api/tags`, {
      signal: AbortSignal.timeout(5000),
    });

    if (!res.ok) {
      throw new Error("Ollama unreachable");
    }

    const data = await res.json();
    const models =
      data.models?.map((m: { name: string }) => m.name) ?? [];

    return Response.json({ connected: true, models });
  } catch {
    return Response.json({ connected: false, models: [] }, { status: 503 });
  }
}
