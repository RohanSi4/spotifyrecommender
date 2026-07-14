import { NextRequest, NextResponse } from "next/server";

import {
  randomOAuthState,
  SPOTIFY_STATE_COOKIE,
  spotifyCookieOptions,
  spotifyRedirectUri,
} from "@/lib/spotify-session";

export async function GET(request: NextRequest) {
  const clientId = process.env.SPOTIFY_CLIENT_ID;
  if (!clientId || !process.env.SPOTIFY_CLIENT_SECRET || !process.env.SIGNAL_SESSION_SECRET) {
    return NextResponse.redirect(new URL("/?spotify=unavailable#try-it", request.url));
  }
  const state = randomOAuthState();
  const authorizeUrl = new URL("https://accounts.spotify.com/authorize");
  authorizeUrl.search = new URLSearchParams({
    response_type: "code",
    client_id: clientId,
    scope: "user-read-private user-top-read",
    redirect_uri: spotifyRedirectUri(request.nextUrl.origin),
    state,
    show_dialog: "false",
  }).toString();
  const response = NextResponse.redirect(authorizeUrl);
  response.cookies.set(SPOTIFY_STATE_COOKIE, state, {
    ...spotifyCookieOptions,
    maxAge: 10 * 60,
  });
  return response;
}
