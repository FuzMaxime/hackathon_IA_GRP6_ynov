import { getPool } from "@/lib/db";
import type { RowDataPacket, ResultSetHeader } from "mysql2";

export async function createUser(username: string, passwordHash: string) {
  const [result] = await getPool().execute<ResultSetHeader>(
    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
    [username, passwordHash],
  );
  return result.insertId;
}

export async function findUserByUsername(username: string) {
  const [rows] = await getPool().execute<RowDataPacket[]>(
    "SELECT id, username, password_hash FROM users WHERE username = ?",
    [username],
  );
  return rows[0] as
    | { id: number; username: string; password_hash: string }
    | undefined;
}
