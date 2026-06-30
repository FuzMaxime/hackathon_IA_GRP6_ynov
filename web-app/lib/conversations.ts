import { getPool, type ConversationRow, type MessageRow } from "@/lib/db";
import type { Session } from "@/lib/auth";
import type { RowDataPacket, ResultSetHeader } from "mysql2";

export async function createConversation(userId: number, title?: string) {
  const [result] = await getPool().execute<ResultSetHeader>(
    "INSERT INTO conversations (user_id, title) VALUES (?, ?)",
    [userId, title ?? "Nouvelle conversation"],
  );
  return result.insertId;
}

export async function getUserConversations(userId: number) {
  const [rows] = await getPool().execute<RowDataPacket[]>(
    `SELECT id, title, created_at, updated_at
     FROM conversations
     WHERE user_id = ?
     ORDER BY updated_at DESC`,
    [userId],
  );
  return rows as ConversationRow[];
}

export async function getLatestConversation(userId: number) {
  const [rows] = await getPool().execute<RowDataPacket[]>(
    `SELECT id, title, created_at, updated_at
     FROM conversations
     WHERE user_id = ?
     ORDER BY updated_at DESC
     LIMIT 1`,
    [userId],
  );
  return rows[0] as ConversationRow | undefined;
}

export async function getConversationForUser(
  conversationId: number,
  userId: number,
) {
  const [rows] = await getPool().execute<RowDataPacket[]>(
    `SELECT id, title, created_at, updated_at
     FROM conversations
     WHERE id = ? AND user_id = ?`,
    [conversationId, userId],
  );
  return rows[0] as ConversationRow | undefined;
}

export async function getMessages(conversationId: number) {
  const [rows] = await getPool().execute<RowDataPacket[]>(
    `SELECT id, role, content, created_at
     FROM messages
     WHERE conversation_id = ?
     ORDER BY created_at ASC`,
    [conversationId],
  );
  return rows as MessageRow[];
}

export async function addMessage(
  conversationId: number,
  role: "user" | "assistant",
  content: string,
) {
  await getPool().execute(
    "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
    [conversationId, role, content],
  );
  await getPool().execute(
    "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
    [conversationId],
  );
}

export async function clearConversationMessages(
  conversationId: number,
  userId: number,
) {
  const conversation = await getConversationForUser(conversationId, userId);
  if (!conversation) return null;

  await getPool().execute("DELETE FROM messages WHERE conversation_id = ?", [
    conversationId,
  ]);
  return conversation;
}

export async function getOrCreateConversation(
  session: Session,
  conversationId?: number,
) {
  if (conversationId) {
    const existing = await getConversationForUser(
      conversationId,
      session.userId,
    );
    if (existing) return existing.id;
  }

  const latest = await getLatestConversation(session.userId);
  if (latest) return latest.id;

  return createConversation(session.userId);
}
