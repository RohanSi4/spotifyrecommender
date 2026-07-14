import { createCipheriv, createDecipheriv, createHash, randomBytes } from "node:crypto";

import { refreshSpotifyToken, type SpotifyProfile } from "./spotify";

export const SPOTIFY_SESSION_COOKIE = "signal_spotify_session";
export const SPOTIFY_STATE_COOKIE = "signal_spotify_state";

export type SpotifySession = {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
  displayName: string;
  imageUrl: string | null;
  accountId: string | null;
};

export const spotifyCookieOptions = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
  path: "/",
};

function sessionKey(): Buffer {
  const secret = process.env.SIGNAL_SESSION_SECRET;
  if (!secret || secret.length < 32) {
    throw new Error("SIGNAL_SESSION_SECRET must contain at least 32 characters.");
  }
  return createHash("sha256").update(secret).digest();
}

export function encryptSpotifySession(session: SpotifySession): string {
  const iv = randomBytes(12);
  const cipher = createCipheriv("aes-256-gcm", sessionKey(), iv);
  const encrypted = Buffer.concat([
    cipher.update(JSON.stringify(session), "utf8"),
    cipher.final(),
  ]);
  const tag = cipher.getAuthTag();
  return Buffer.concat([iv, tag, encrypted]).toString("base64url");
}

export function decryptSpotifySession(value: string | undefined): SpotifySession | null {
  if (!value) return null;
  try {
    const packed = Buffer.from(value, "base64url");
    if (packed.length < 29) return null;
    const iv = packed.subarray(0, 12);
    const tag = packed.subarray(12, 28);
    const encrypted = packed.subarray(28);
    const decipher = createDecipheriv("aes-256-gcm", sessionKey(), iv);
    decipher.setAuthTag(tag);
    const json = Buffer.concat([decipher.update(encrypted), decipher.final()]).toString("utf8");
    const session = JSON.parse(json) as Partial<SpotifySession>;
    if (
      typeof session.accessToken !== "string"
      || typeof session.refreshToken !== "string"
      || typeof session.expiresAt !== "number"
      || typeof session.displayName !== "string"
    ) return null;
    return session as SpotifySession;
  } catch {
    return null;
  }
}

export function spotifySessionFromToken(
  token: { access_token: string; refresh_token?: string; expires_in: number },
  profile: SpotifyProfile,
  previousRefreshToken?: string,
): SpotifySession {
  const refreshToken = token.refresh_token ?? previousRefreshToken;
  if (!refreshToken) throw new Error("Spotify did not return a refresh token.");
  return {
    accessToken: token.access_token,
    refreshToken,
    expiresAt: Date.now() + token.expires_in * 1000,
    displayName: profile.display_name?.trim() || "Spotify listener",
    imageUrl: profile.images?.[0]?.url ?? null,
    accountId: profile.account_id ?? profile.id ?? null,
  };
}

export async function refreshSessionIfNeeded(session: SpotifySession): Promise<{
  session: SpotifySession;
  refreshed: boolean;
}> {
  if (session.expiresAt > Date.now() + 60_000) return { session, refreshed: false };
  const token = await refreshSpotifyToken(session.refreshToken);
  return {
    refreshed: true,
    session: {
      ...session,
      accessToken: token.access_token,
      refreshToken: token.refresh_token ?? session.refreshToken,
      expiresAt: Date.now() + token.expires_in * 1000,
    },
  };
}

export function spotifyRedirectUri(origin: string): string {
  return process.env.SPOTIFY_REDIRECT_URI?.trim()
    || `${origin.replace(/\/$/, "")}/api/auth/callback`;
}

export function randomOAuthState(): string {
  return randomBytes(24).toString("base64url");
}
