"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

import { SignalMark } from "@/components/signal-mark";
import { TrackResult } from "@/components/track-result";
import { normalizeMixNumber, normalizeTrackHistory } from "@/lib/recommendation-variety";
import type { PublicSpotifyTrack, SpotifyRecommendation } from "@/lib/spotify";

type Mode = "song" | "personal";
type Connection = {
  checked: boolean;
  connected: boolean;
  configured: boolean;
  user?: { displayName: string; imageUrl: string | null };
};

const QUICK_SEARCHES = ["Nights Frank Ocean", "SZA Snooze", "Tyler the Creator", "Drake Passionfruit"];
const PERSONAL_MIX_STORAGE = "signal-personal-mixes-v1";

type PersonalMixMemory = {
  trackIds: string[];
  mixNumber: number;
};

function readPersonalMixMemory(): PersonalMixMemory {
  try {
    const stored = JSON.parse(window.localStorage.getItem(PERSONAL_MIX_STORAGE) ?? "null") as {
      trackIds?: unknown;
      mixNumber?: unknown;
    } | null;
    return {
      trackIds: normalizeTrackHistory(stored?.trackIds),
      mixNumber: normalizeMixNumber(stored?.mixNumber),
    };
  } catch {
    return { trackIds: [], mixNumber: 0 };
  }
}

function savePersonalMixMemory(memory: PersonalMixMemory) {
  window.localStorage.setItem(PERSONAL_MIX_STORAGE, JSON.stringify(memory));
}

async function readJson<T>(response: Response): Promise<T> {
  const body = await response.json() as T & { error?: string };
  if (!response.ok) throw new Error(body.error || "Something went wrong. Try again.");
  return body;
}

export function SignalApp() {
  const [mode, setMode] = useState<Mode>("song");
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<PublicSpotifyTrack[]>([]);
  const [selected, setSelected] = useState<PublicSpotifyTrack | null>(null);
  const [recommendations, setRecommendations] = useState<SpotifyRecommendation[]>([]);
  const [topTracks, setTopTracks] = useState<PublicSpotifyTrack[]>([]);
  const [personalFreshCount, setPersonalFreshCount] = useState(0);
  const [resultTitle, setResultTitle] = useState("Your next songs will show up here");
  const [searching, setSearching] = useState(false);
  const [building, setBuilding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [connection, setConnection] = useState<Connection>({
    checked: false,
    connected: false,
    configured: true,
  });

  useEffect(() => {
    const status = new URLSearchParams(window.location.search).get("spotify");
    const notices: Record<string, string> = {
      connected: "Spotify is connected. Your personal mix is ready when you are.",
      cancelled: "Spotify connection was cancelled. You can still search every song.",
      not_allowed: "That Spotify account is not on this app's small test list yet.",
      invalid_state: "That login took too long. Please try connecting again.",
      auth_failed: "Spotify could not finish connecting. Public search still works.",
      unavailable: "Spotify login is not configured yet. Public search still works.",
    };
    if (status && notices[status]) {
      queueMicrotask(() => setNotice(notices[status]));
    }

    fetch("/api/spotify/me", { cache: "no-store" })
      .then((response) => readJson<Omit<Connection, "checked">>(response))
      .then((data) => {
        setConnection({ ...data, checked: true });
        if (data.connected) setMode("personal");
      })
      .catch(() => setConnection({ checked: true, connected: false, configured: false }));
  }, []);

  useEffect(() => {
    const cleanQuery = query.trim();
    if (cleanQuery.length < 2) return;
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setSearching(true);
      setError(null);
      try {
        const response = await fetch(`/api/spotify/search?q=${encodeURIComponent(cleanQuery)}`, {
          signal: controller.signal,
        });
        const data = await readJson<{ tracks: PublicSpotifyTrack[] }>(response);
        setSearchResults(data.tracks);
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") return;
        setError(caught instanceof Error ? caught.message : "Spotify search failed.");
      } finally {
        if (!controller.signal.aborted) setSearching(false);
      }
    }, 350);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  async function buildFromSong() {
    if (!selected) return;
    setBuilding(true);
    setError(null);
    try {
      const response = await fetch("/api/spotify/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ trackId: selected.id }),
      });
      const data = await readJson<{
        seed: PublicSpotifyTrack;
        recommendations: SpotifyRecommendation[];
      }>(response);
      setRecommendations(data.recommendations);
      setTopTracks([]);
      setResultTitle(`A few ways out from ${data.seed.name}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Spotify could not build that mix.");
    } finally {
      setBuilding(false);
    }
  }

  async function buildPersonalMix() {
    setBuilding(true);
    setError(null);
    try {
      const memory = readPersonalMixMemory();
      const response = await fetch("/api/spotify/for-you", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          excludeTrackIds: memory.trackIds,
          mixNumber: memory.mixNumber,
        }),
      });
      const data = await readJson<{
        topTracks: PublicSpotifyTrack[];
        recommendations: SpotifyRecommendation[];
        mixNumber: number;
        freshCount: number;
      }>(response);
      setRecommendations(data.recommendations);
      setTopTracks(data.topTracks);
      setPersonalFreshCount(data.freshCount);
      setResultTitle(data.mixNumber === 0
        ? "Fresh picks from across your Spotify taste"
        : "Another route through your Spotify taste");
      savePersonalMixMemory({
        trackIds: normalizeTrackHistory([
          ...data.recommendations.map(({ track }) => track.id),
          ...memory.trackIds,
        ]),
        mixNumber: data.mixNumber + 1,
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Spotify could not build your mix.");
    } finally {
      setBuilding(false);
    }
  }

  async function disconnect() {
    await fetch("/api/auth/logout", { method: "POST" });
    setConnection({ checked: true, connected: false, configured: true });
    setMode("song");
    setTopTracks([]);
    setRecommendations([]);
    setPersonalFreshCount(0);
    setResultTitle("Your next songs will show up here");
    setNotice("Spotify disconnected.");
    window.localStorage.removeItem(PERSONAL_MIX_STORAGE);
  }

  function resetPersonalMixMemory() {
    window.localStorage.removeItem(PERSONAL_MIX_STORAGE);
    setNotice("Signal forgot the earlier mixes on this browser. Your next mix starts fresh.");
  }

  function selectTrack(track: PublicSpotifyTrack) {
    setSelected(track);
    setQuery("");
    setSearchResults([]);
    setError(null);
  }

  return (
    <div className="engine-shell">
      <aside className="controls" aria-label="Recommendation controls">
        <div className="mode-switch" aria-label="Recommendation type">
          <button
            className={mode === "song" ? "active" : ""}
            onClick={() => setMode("song")}
            aria-pressed={mode === "song"}
          >
            Start with a song
          </button>
          <button
            className={mode === "personal" ? "active" : ""}
            onClick={() => setMode("personal")}
            aria-pressed={mode === "personal"}
          >
            Use my Spotify
          </button>
        </div>

        {notice ? <p className="status-note">{notice}</p> : null}

        {mode === "song" ? (
          <div className="control-block">
            <label htmlFor="track-search">Search any song on Spotify</label>
            <div className="search-wrap">
              <input
                id="track-search"
                type="search"
                value={query}
                onChange={(event) => {
                  const value = event.target.value;
                  setQuery(value);
                  if (value.trim().length < 2) {
                    setSearchResults([]);
                    setSearching(false);
                  }
                }}
                placeholder="Try a song, artist, or both"
                autoComplete="off"
              />
              <span aria-hidden="true">{searching ? "•••" : "⌕"}</span>
            </div>

            {searchResults.length > 0 ? (
              <div className="search-results" aria-label="Spotify search results">
                {searchResults.map((track) => (
                  <button key={track.id} type="button" onClick={() => selectTrack(track)}>
                    {track.imageUrl ? (
                      <Image src={track.imageUrl} alt="" width={44} height={44} />
                    ) : <span className="art-fallback"><SignalMark compact /></span>}
                    <span><strong>{track.name}</strong><small>{track.artists.join(", ")}</small></span>
                  </button>
                ))}
              </div>
            ) : query.trim().length < 2 ? (
              <div className="quick-searches" aria-label="Try a search">
                {QUICK_SEARCHES.map((term) => (
                  <button type="button" key={term} onClick={() => setQuery(term)}>{term}</button>
                ))}
              </div>
            ) : !searching ? <p className="empty-search">No songs found. Try a shorter search.</p> : null}

            {selected ? (
              <div className="selected-track">
                {selected.imageUrl ? <Image src={selected.imageUrl} alt="" width={58} height={58} /> : null}
                <div><span>Starting with</span><strong>{selected.name}</strong><small>{selected.artists.join(", ")}</small></div>
                <button type="button" onClick={() => setSelected(null)} aria-label="Clear selected song">×</button>
              </div>
            ) : null}

            <button className="rank-button" onClick={buildFromSong} disabled={!selected || building}>
              <SignalMark compact />
              {building ? "Digging through Spotify..." : "Build a real mix"}
            </button>
            <p className="control-help">No login needed. Every result is a real Spotify track you can play.</p>
          </div>
        ) : (
          <div className="control-block personal-block">
            {!connection.checked ? (
              <div className="loading-card"><SignalMark /><p>Checking your Spotify connection...</p></div>
            ) : connection.connected ? (
              <>
                <div className="account-card">
                  {connection.user?.imageUrl ? (
                    <Image src={connection.user.imageUrl} alt="" width={54} height={54} />
                  ) : <span className="avatar-fallback"><SignalMark compact /></span>}
                  <div><span>Connected as</span><strong>{connection.user?.displayName || "Spotify listener"}</strong></div>
                  <button type="button" onClick={disconnect}>Log out</button>
                </div>
                <p>Signal checks your recent, medium-term, and longtime favorites, then branches into deeper releases and featured artists.</p>
                <button className="rank-button" onClick={() => buildPersonalMix()} disabled={building}>
                  <SignalMark compact />
                  {building
                    ? "Finding songs you have not seen here..."
                    : topTracks.length > 0 ? "Give me 16 more songs" : "Make my personal mix"}
                </button>
                <p className="mix-memory-note">
                  Signal remembers earlier picks on this browser so each new mix can go somewhere else.
                  {topTracks.length > 0 ? (
                    <button type="button" onClick={resetPersonalMixMemory}>Start over</button>
                  ) : null}
                </p>
              </>
            ) : (
              <>
                <div className="connect-card">
                  <SignalMark />
                  <h3>Let your listening history do the work.</h3>
                  <p>Connect Spotify and Signal will look past your obvious favorites for songs you may have missed.</p>
                  {connection.configured ? (
                    <a className="spotify-button" href="/api/auth/login">Connect Spotify</a>
                  ) : <span className="disabled-button">Spotify login is being set up</span>}
                </div>
                <p className="beta-note">Spotify currently limits new developer apps to five invited listeners. Public song search works for everyone.</p>
              </>
            )}
          </div>
        )}

        {error ? <p className="error-note" role="alert">{error}</p> : null}
      </aside>

      <div className="results" aria-live="polite" aria-busy={building}>
        <div className="results-header">
          <div>
            <p className="eyebrow"><span /> Live Spotify catalog</p>
            <h2>{resultTitle}</h2>
          </div>
          {recommendations.length ? (
            <p>{topTracks.length > 0
              ? `${personalFreshCount} fresh picks`
              : `${recommendations.length} real tracks`}</p>
          ) : null}
        </div>

        {topTracks.length > 0 ? (
          <div className="taste-strip">
            <span>Based on</span>
            {topTracks.slice(0, 5).map((track) => <small key={track.id}>{track.name}</small>)}
          </div>
        ) : null}

        {building ? (
          <div className="results-empty loading-results">
            <SignalMark />
            <h3>Looking beyond the obvious picks</h3>
            <p>Pulling releases and artist connections from Spotify now.</p>
          </div>
        ) : recommendations.length ? (
          <div className="result-list">
            {recommendations.map((recommendation, index) => (
              <TrackResult key={recommendation.track.id} rank={index + 1} recommendation={recommendation} />
            ))}
          </div>
        ) : (
          <div className="results-empty">
            <div className="empty-record"><SignalMark /></div>
            <h3>Start with something you actually listen to.</h3>
            <p>Search any song, or connect Spotify for a mix built from your own rotation.</p>
          </div>
        )}
      </div>
    </div>
  );
}
