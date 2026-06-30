"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import AuthForm from "./AuthForm";

type Message = {
  role: "user" | "assistant";
  content: string;
};

type User = {
  id: number;
  username: string;
};

type Conversation = {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
};

type ConnectionStatus = "checking" | "connected" | "disconnected";

function formatConversationDate(dateStr: string) {
  const date = new Date(dateStr);
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();

  if (isToday) {
    return date.toLocaleTimeString("fr-FR", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  return date.toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
  });
}

export default function Chat() {
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [loadingConversation, setLoadingConversation] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<ConnectionStatus>("checking");
  const [dbConnected, setDbConnected] = useState(false);
  const [models, setModels] = useState<string[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  const refreshConversations = useCallback(async () => {
    const res = await fetch("/api/conversations");
    if (res.ok) {
      const data = await res.json();
      setConversations(data.conversations ?? []);
    }
  }, []);

  const loadSession = useCallback(async () => {
    try {
      const res = await fetch("/api/auth/me");
      if (!res.ok) {
        setUser(null);
        setMessages([]);
        setConversationId(null);
        setConversations([]);
        return;
      }
      const data = await res.json();
      setUser(data.user);
      setMessages(data.messages ?? []);
      setConversationId(data.activeConversationId ?? null);
      setConversations(data.conversations ?? []);
    } catch {
      setUser(null);
    } finally {
      setAuthLoading(false);
    }
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      setStatus(data.connected ? "connected" : "disconnected");
      setDbConnected(data.dbConnected ?? false);
      setModels(data.models ?? []);
    } catch {
      setStatus("disconnected");
      setDbConnected(false);
      setModels([]);
    }
  }, []);

  useEffect(() => {
    loadSession();
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, [loadSession, checkHealth]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleAuthSuccess() {
    setAuthLoading(true);
    await loadSession();
  }

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    setUser(null);
    setMessages([]);
    setConversationId(null);
    setConversations([]);
  }

  async function selectConversation(id: number) {
    if (id === conversationId || loadingConversation) return;

    setLoadingConversation(true);
    try {
      const res = await fetch(`/api/conversations/${id}`);
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error ?? "Impossible de charger la conversation");
      }

      setConversationId(data.conversation.id);
      setMessages(data.messages ?? []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingConversation(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading || status !== "connected" || !user) return;

    const userMessage: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: text, conversationId }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error ?? "Erreur inconnue");
      }

      setConversationId(data.conversationId);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.content },
      ]);
      await refreshConversations();
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

  async function createNewConversation() {
    const res = await fetch("/api/conversations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: "Nouvelle conversation" }),
    });

    if (res.ok) {
      const data = await res.json();
      setConversationId(data.id);
      setMessages([]);
      await refreshConversations();
    }
  }

  if (authLoading) {
    return (
      <div className="flex h-full items-center justify-center bg-white text-zinc-500">
        Chargement…
      </div>
    );
  }

  if (!user) {
    return <AuthForm onSuccess={handleAuthSuccess} />;
  }

  const statusLabel = {
    checking: "Vérification…",
    connected: "Connecté",
    disconnected: "Déconnecté",
  }[status];

  const statusColor = {
    checking: "bg-amber-400",
    connected: "bg-emerald-500",
    disconnected: "bg-red-500",
  }[status];

  return (
    <div className="flex h-full bg-white text-zinc-900">
      {/* Sidebar conversations */}
      <aside className="flex w-64 shrink-0 flex-col border-r border-zinc-200 bg-zinc-50">
        <div className="border-b border-zinc-200 p-4">
          <button
            type="button"
            onClick={createNewConversation}
            className="w-full rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-emerald-500"
          >
            + Nouvelle conversation
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {conversations.length === 0 ? (
            <p className="px-2 py-4 text-center text-xs text-zinc-400">
              Aucune conversation
            </p>
          ) : (
            <ul className="space-y-1">
              {conversations.map((conv) => (
                <li key={conv.id}>
                  <button
                    type="button"
                    onClick={() => selectConversation(conv.id)}
                    disabled={loadingConversation}
                    className={`w-full rounded-lg px-3 py-2.5 text-left transition disabled:opacity-50 ${
                      conversationId === conv.id
                        ? "bg-white shadow-sm ring-1 ring-emerald-200"
                        : "hover:bg-white/70"
                    }`}
                  >
                    <p className="truncate text-sm font-medium text-zinc-800">
                      {conv.title}
                    </p>
                    <p className="mt-0.5 text-xs text-zinc-400">
                      {formatConversationDate(conv.updated_at)}
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>

      {/* Zone chat principale */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex shrink-0 items-center justify-between border-b border-zinc-200 bg-white px-6 py-4">
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-zinc-900">
              TechCorp Financial Assistant
            </h1>
            <p className="text-sm text-zinc-500">
              Connecté en tant que{" "}
              <span className="font-medium text-emerald-600">
                {user.username}
              </span>
            </p>
          </div>
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm text-zinc-700 transition hover:bg-zinc-50"
            >
              Déconnexion
            </button>
            <div className="flex items-center gap-2 text-sm">
              <span className={`h-2.5 w-2.5 rounded-full ${statusColor}`} />
              <span className="text-zinc-600">{statusLabel}</span>
            </div>
          </div>
        </header>

        {status === "disconnected" && (
          <div className="shrink-0 border-b border-red-200 bg-red-50 px-6 py-3 text-sm text-red-700">
            {!dbConnected && "MySQL inaccessible. "}
            Service(s) indisponible(s). Vérifiez Docker et Ollama sur{" "}
            <code className="rounded bg-red-100 px-1 text-red-800">
              localhost:11434
            </code>
            .
          </div>
        )}

        {models.length > 0 && status === "connected" && (
          <div className="shrink-0 border-b border-zinc-100 bg-zinc-50 px-6 py-2 text-xs text-zinc-500">
            Modèles Ollama : {models.join(", ")}
            {conversationId && ` · Conversation #${conversationId}`}
          </div>
        )}

        <div className="flex-1 overflow-y-auto bg-zinc-50 px-6 py-6">
          {loadingConversation ? (
            <div className="flex h-full items-center justify-center text-sm text-zinc-400">
              Chargement de la conversation…
            </div>
          ) : messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-center text-zinc-500">
              <p className="text-4xl">💬</p>
              <p className="text-lg text-zinc-700">Posez une question finance</p>
              <p className="max-w-md text-sm">
                Sélectionnez une conversation ou créez-en une nouvelle.
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
                    className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap shadow-sm ${
                      msg.role === "user"
                        ? "bg-emerald-600 text-white"
                        : "border border-zinc-200 bg-white text-zinc-800"
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="rounded-2xl border border-zinc-200 bg-white px-4 py-3 text-sm text-zinc-400 shadow-sm">
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
          className="shrink-0 border-t border-zinc-200 bg-white px-6 py-4"
        >
          <div className="mx-auto flex max-w-3xl gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                status === "connected"
                  ? "Votre message…"
                  : "En attente des services…"
              }
              disabled={loading || status !== "connected" || loadingConversation}
              className="flex-1 rounded-xl border border-zinc-300 bg-white px-4 py-3 text-sm text-zinc-900 outline-none transition placeholder:text-zinc-400 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={
                loading ||
                !input.trim() ||
                status !== "connected" ||
                loadingConversation
              }
              className="rounded-xl bg-emerald-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Envoyer
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
