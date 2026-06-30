"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Message = {
  role: "user" | "assistant";
  content: string;
};

type ConnectionStatus = "checking" | "connected" | "disconnected";

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<ConnectionStatus>("checking");
  const [models, setModels] = useState<string[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      setStatus(data.connected ? "connected" : "disconnected");
      setModels(data.models ?? []);
    } catch {
      setStatus("disconnected");
      setModels([]);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading || status !== "connected") return;

    const userMessage: Message = { role: "user", content: text };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: nextMessages }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error ?? "Erreur inconnue");
      }

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.content },
      ]);
    } catch (err) {
      const error =
        err instanceof Error ? err.message : "Erreur de communication";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `⚠️ ${error}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function clearChat() {
    setMessages([]);
  }

  const statusLabel = {
    checking: "Vérification…",
    connected: "Connecté",
    disconnected: "Déconnecté",
  }[status];

  const statusColor = {
    checking: "bg-amber-400",
    connected: "bg-emerald-400",
    disconnected: "bg-red-400",
  }[status];

  return (
    <div className="flex h-full flex-col bg-zinc-950 text-zinc-100">
      <header className="flex shrink-0 items-center justify-between border-b border-zinc-800 px-6 py-4">
        <div>
          <h1 className="text-lg font-semibold tracking-tight">
            TechCorp Financial Assistant
          </h1>
          <p className="text-sm text-zinc-400">Phi-3.5-Financial via Ollama</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={clearChat}
            className="rounded-lg border border-zinc-700 px-3 py-1.5 text-sm text-zinc-300 transition hover:bg-zinc-800"
          >
            Effacer
          </button>
          <div className="flex items-center gap-2 text-sm">
            <span className={`h-2.5 w-2.5 rounded-full ${statusColor}`} />
            <span className="text-zinc-300">{statusLabel}</span>
          </div>
        </div>
      </header>

      {status === "disconnected" && (
        <div className="shrink-0 border-b border-red-900/50 bg-red-950/40 px-6 py-3 text-sm text-red-300">
          Ollama inaccessible. Vérifiez que le serveur tourne sur{" "}
          <code className="rounded bg-red-900/50 px-1">localhost:11434</code> et
          que le modèle{" "}
          <code className="rounded bg-red-900/50 px-1">phi35-financial</code>{" "}
          est créé.
        </div>
      )}

      {models.length > 0 && status === "connected" && (
        <div className="shrink-0 border-b border-zinc-800 px-6 py-2 text-xs text-zinc-500">
          Modèles disponibles : {models.join(", ")}
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-center text-zinc-500">
            <p className="text-4xl">💬</p>
            <p className="text-lg">Posez une question finance</p>
            <p className="max-w-md text-sm">
              Exemples : ETF, bilan comptable, analyse de risque, prévisions de
              trésorerie…
            </p>
          </div>
        ) : (
          <div className="mx-auto flex max-w-3xl flex-col gap-4">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "bg-emerald-600 text-white"
                      : "bg-zinc-800 text-zinc-100"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="rounded-2xl bg-zinc-800 px-4 py-3 text-sm text-zinc-400">
                  <span className="inline-flex gap-1">
                    <span className="animate-bounce">·</span>
                    <span className="animate-bounce [animation-delay:150ms]">
                      ·
                    </span>
                    <span className="animate-bounce [animation-delay:300ms]">
                      ·
                    </span>
                  </span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <form
        onSubmit={handleSubmit}
        className="shrink-0 border-t border-zinc-800 px-6 py-4"
      >
        <div className="mx-auto flex max-w-3xl gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              status === "connected"
                ? "Votre message…"
                : "En attente de connexion Ollama…"
            }
            disabled={loading || status !== "connected"}
            className="flex-1 rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm outline-none transition placeholder:text-zinc-500 focus:border-emerald-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim() || status !== "connected"}
            className="rounded-xl bg-emerald-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Envoyer
          </button>
        </div>
      </form>
    </div>
  );
}
