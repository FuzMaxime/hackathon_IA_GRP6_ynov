import { hashPassword, createToken, setSessionCookie } from "@/lib/auth";
import { createUser, findUserByUsername } from "@/lib/conversations";
import { NextResponse } from "next/server";

export async function POST(request: Request) {
  try {
    const { username, password } = await request.json();

    if (!username?.trim() || !password) {
      return NextResponse.json(
        { error: "Username et mot de passe requis" },
        { status: 400 },
      );
    }

    if (password.length < 6) {
      return NextResponse.json(
        { error: "Mot de passe minimum 6 caractères" },
        { status: 400 },
      );
    }

    const existing = await findUserByUsername(username.trim());
    if (existing) {
      return NextResponse.json(
        { error: "Ce nom d'utilisateur existe déjà" },
        { status: 409 },
      );
    }

    const passwordHash = await hashPassword(password);
    const userId = await createUser(username.trim(), passwordHash);
    const token = await createToken({ userId, username: username.trim() });
    await setSessionCookie(token);

    return NextResponse.json({ user: { id: userId, username: username.trim() } });
  } catch {
    return NextResponse.json({ error: "Erreur serveur" }, { status: 500 });
  }
}
