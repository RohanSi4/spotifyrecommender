import { NextResponse } from "next/server";

import { SPOTIFY_SESSION_COOKIE } from "@/lib/spotify-session";

export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.cookies.delete(SPOTIFY_SESSION_COOKIE);
  return response;
}
