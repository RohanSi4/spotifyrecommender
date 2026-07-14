import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { spotifyConfigured } from "@/lib/spotify";
import {
  decryptSpotifySession,
  encryptSpotifySession,
  refreshSessionIfNeeded,
  SPOTIFY_SESSION_COOKIE,
  spotifyCookieOptions,
} from "@/lib/spotify-session";

export async function GET() {
  const cookieStore = await cookies();
  const stored = decryptSpotifySession(cookieStore.get(SPOTIFY_SESSION_COOKIE)?.value);
  if (!stored) {
    return NextResponse.json({ connected: false, configured: spotifyConfigured() });
  }
  try {
    const { session, refreshed } = await refreshSessionIfNeeded(stored);
    const response = NextResponse.json({
      connected: true,
      configured: true,
      user: {
        displayName: session.displayName,
        imageUrl: session.imageUrl,
      },
    });
    if (refreshed) {
      response.cookies.set(SPOTIFY_SESSION_COOKIE, encryptSpotifySession(session), {
        ...spotifyCookieOptions,
        maxAge: 30 * 24 * 60 * 60,
      });
    }
    return response;
  } catch {
    const response = NextResponse.json({ connected: false, configured: true });
    response.cookies.delete(SPOTIFY_SESSION_COOKIE);
    return response;
  }
}
