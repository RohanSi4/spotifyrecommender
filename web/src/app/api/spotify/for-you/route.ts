import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { allowRequest, requestIdentity } from "@/lib/rate-limit";
import { recommendationsForSpotifyUser, SpotifyApiError } from "@/lib/spotify";
import {
  decryptSpotifySession,
  encryptSpotifySession,
  refreshSessionIfNeeded,
  SPOTIFY_SESSION_COOKIE,
  spotifyCookieOptions,
} from "@/lib/spotify-session";

export async function POST(request: NextRequest) {
  if (!allowRequest(`personal:${requestIdentity(request.headers)}`, 8)) {
    return NextResponse.json({ error: "Too many refreshes. Give Spotify a minute." }, { status: 429 });
  }
  const cookieStore = await cookies();
  const stored = decryptSpotifySession(cookieStore.get(SPOTIFY_SESSION_COOKIE)?.value);
  if (!stored) {
    return NextResponse.json({ error: "Connect Spotify to build your mix." }, { status: 401 });
  }
  try {
    const { session, refreshed } = await refreshSessionIfNeeded(stored);
    const response = NextResponse.json(await recommendationsForSpotifyUser(session.accessToken));
    if (refreshed) {
      response.cookies.set(SPOTIFY_SESSION_COOKIE, encryptSpotifySession(session), {
        ...spotifyCookieOptions,
        maxAge: 30 * 24 * 60 * 60,
      });
    }
    return response;
  } catch (error) {
    const status = error instanceof SpotifyApiError ? error.status : 502;
    const message = error instanceof Error ? error.message : "Spotify could not build your mix.";
    return NextResponse.json({ error: message }, { status });
  }
}
