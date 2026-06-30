import { checkDbConnection } from "@/lib/db";

const OLLAMA_URL = process.env.OLLAMA_URL ?? "http://localhost:11434";

export async function GET() {
  const dbConnected = await checkDbConnection();

  let ollamaConnected = false;
  let models: string[] = [];

  try {
    const res = await fetch(`${OLLAMA_URL}/api/tags`, {
      signal: AbortSignal.timeout(5000),
    });

    if (res.ok) {
      const data = await res.json();
      models = data.models?.map((m: { name: string }) => m.name) ?? [];
      ollamaConnected = true;
    }
  } catch {
    ollamaConnected = false;
  }

  const connected = dbConnected && ollamaConnected;

  return Response.json(
    { connected, dbConnected, ollamaConnected, models },
    { status: connected ? 200 : 503 },
  );
}
