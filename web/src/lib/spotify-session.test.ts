import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  decryptSpotifySession,
  encryptSpotifySession,
  spotifyRedirectUri,
  type SpotifySession,
} from "./spotify-session";

const session: SpotifySession = {
  accessToken: "access-token",
  refreshToken: "refresh-token",
  expiresAt: 2_000_000_000_000,
  displayName: "Rohan",
  imageUrl: null,
  accountId: "spotify-user",
};

describe("Spotify session cookies", () => {
  beforeEach(() => vi.stubEnv("SIGNAL_SESSION_SECRET", "a-secure-test-key-with-at-least-32-characters"));
  afterEach(() => vi.unstubAllEnvs());

  it("round trips an encrypted session without exposing its tokens", () => {
    const encrypted = encryptSpotifySession(session);
    expect(encrypted).not.toContain(session.accessToken);
    expect(decryptSpotifySession(encrypted)).toEqual(session);
  });

  it("rejects a cookie that has been changed", () => {
    const encrypted = encryptSpotifySession(session);
    const tampered = `${encrypted.slice(0, -2)}aa`;
    expect(decryptSpotifySession(tampered)).toBeNull();
  });

  it("uses the current site callback when no override exists", () => {
    vi.stubEnv("SPOTIFY_REDIRECT_URI", "");
    expect(spotifyRedirectUri("https://signal.example/")).toBe("https://signal.example/api/auth/callback");
  });
});
