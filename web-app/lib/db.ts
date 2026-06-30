import mysql from "mysql2/promise";

let pool: mysql.Pool | null = null;

export function getPool() {
  if (!pool) {
    pool = mysql.createPool({
      host: process.env.MYSQL_HOST ?? "localhost",
      port: Number(process.env.MYSQL_PORT ?? 3306),
      user: process.env.MYSQL_USER ?? "techcorp",
      password: process.env.MYSQL_PASSWORD ?? "techcorp",
      database: process.env.MYSQL_DATABASE ?? "techcorp_chat",
      waitForConnections: true,
      connectionLimit: 10,
    });
  }
  return pool;
}

export async function checkDbConnection(): Promise<boolean> {
  try {
    const connection = await getPool().getConnection();
    await connection.ping();
    connection.release();
    return true;
  } catch {
    return false;
  }
}

export type UserRow = {
  id: number;
  username: string;
  password_hash: string;
};

export type MessageRow = {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: Date;
};

export type ConversationRow = {
  id: number;
  title: string;
  created_at: Date;
  updated_at: Date;
};
