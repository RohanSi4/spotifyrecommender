import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import {
  exchangeAuthorizationCode,
  getSpotifyProfile,
  SpotifyApiError,
} from "@/lib/spotify";
import {
  encryptSpotifySession,
  SPOTIFY_SESSION_COOKIE,
  SPOTIFY_STATE_COOKIE,
  spotifyCookieOptions,
  spotifyRedirectUri,
  spotifySessionFromToken,
} from "@/lib/spotify-session";

function resultRedirect(request: NextRequest, result: string): NextResponse {
  const response = NextResponse.redirect(new URL(`/?spotify=${result}#try-it`, request.url));
  response.cookies.delete(SPOTIFY_STATE_COOKIE);
  return response;
}

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");
  const state = request.nextUrl.searchParams.get("state");
  const error = request.nextUrl.searchParams.get("error");
  const cookieStore = await cookies();
  const expectedState = cookieStore.get(SPOTIFY_STATE_COOKIE)?.value;

  if (error) return resultRedirect(request, "cancelled");
  if (!code || !state || !expectedState || state !== expectedState) {
    return resultRedirect(request, "invalid_state");
  }

  try {
    const token = await exchangeAuthorizationCode(
      code,
      spotifyRedirectUri(request.nextUrl.origin),
    );
    const profile = await getSpotifyProfile(token.access_token);
    const session = spotifySessionFromToken(token, profile);
    const response = resultRedirect(request, "connected");
    response.cookies.set(SPOTIFY_SESSION_COOKIE, encryptSpotifySession(session), {
      ...spotifyCookieOptions,
      maxAge: 30 * 24 * 60 * 60,
    });
    return response;
  } catch (error) {
    const result = error instanceof SpotifyApiError && error.status === 403
      ? "not_allowed"
      : "auth_failed";
    return resultRedirect(request, result);
  }
}
