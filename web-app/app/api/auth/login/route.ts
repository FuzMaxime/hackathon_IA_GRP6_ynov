import {
  createToken,
  setSessionCookie,
  verifyPassword,
} from "@/lib/auth";
import { findUserByUsername } from "@/lib/conversations";
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

    const user = await findUserByUsername(username.trim());
    if (!user || !(await verifyPassword(password, user.password_hash))) {
      return NextResponse.json(
        { error: "Identifiants invalides" },
        { status: 401 },
      );
    }

    const token = await createToken({
      userId: user.id,
      username: user.username,
    });
    await setSessionCookie(token);

    return NextResponse.json({
      user: { id: user.id, username: user.username },
    });
  } catch {
    return NextResponse.json({ error: "Erreur serveur" }, { status: 500 });
  }
}
