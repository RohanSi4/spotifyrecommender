import {
  normalizeMixNumber,
  normalizeTrackHistory,
  rotatingSelection,
  rotatingWindow,
  stableVariation,
} from "./recommendation-variety";

const SPOTIFY_API = "https://api.spotify.com/v1";
const SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token";

type SpotifyImage = {
  url: string;
  width: number | null;
  height: number | null;
};

type SpotifyArtist = {
  id: string;
  name: string;
};

type SpotifyAlbum = {
  id: string;
  name: string;
  release_date: string;
  images: SpotifyImage[];
  external_urls: { spotify: string };
};

type SpotifyTrack = {
  id: string;
  name: string;
  artists: SpotifyArtist[];
  album: SpotifyAlbum;
  duration_ms: number;
  explicit: boolean;
  external_urls: { spotify: string };
};

type SpotifySimplifiedTrack = Omit<SpotifyTrack, "album">;

type SpotifyPaging<T> = {
  items: T[];
};

type SpotifySearchResponse = {
  tracks: SpotifyPaging<SpotifyTrack>;
};

type SpotifyTopTracksResponse = SpotifyPaging<SpotifyTrack>;

type TokenResponse = {
  access_token: string;
  token_type: "Bearer";
  expires_in: number;
  refresh_token?: string;
  scope?: string;
};

export type PublicSpotifyTrack = {
  id: string;
  name: string;
  artists: string[];
  artistIds: string[];
  album: string;
  albumId: string;
  imageUrl: string | null;
  spotifyUrl: string;
  durationMs: number;
  explicit: boolean;
  releaseDate: string;
};

export type SpotifyRecommendation = {
  track: PublicSpotifyTrack;
  reasons: string[];
  connection: "closest" | "connected" | "explore";
};

export type SpotifyProfile = {
  account_id?: string;
  id?: string;
  display_name: string | null;
  images?: SpotifyImage[];
};

export class SpotifyApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly retryAfter: number | null = null,
  ) {
    super(message);
  }
}

let clientToken: { value: string; expiresAt: number } | null = null;

export function spotifyConfigured(): boolean {
  return Boolean(process.env.SPOTIFY_CLIENT_ID && process.env.SPOTIFY_CLIENT_SECRET);
}

function spotifyCredentials(): { clientId: string; clientSecret: string } {
  const clientId = process.env.SPOTIFY_CLIENT_ID;
  const clientSecret = process.env.SPOTIFY_CLIENT_SECRET;
  if (!clientId || !clientSecret) {
    throw new SpotifyApiError("Spotify is not configured yet.", 503);
  }
  return { clientId, clientSecret };
}

async function tokenRequest(body: URLSearchParams, withBasicAuth = true): Promise<TokenResponse> {
  const { clientId, clientSecret } = spotifyCredentials();
  const headers: Record<string, string> = {
    "Content-Type": "application/x-www-form-urlencoded",
  };
  if (withBasicAuth) {
    headers.Authorization = `Basic ${Buffer.from(`${clientId}:${clientSecret}`).toString("base64")}`;
  }

  const response = await fetch(SPOTIFY_TOKEN_URL, {
    method: "POST",
    headers,
    body,
    cache: "no-store",
    signal: AbortSignal.timeout(12_000),
  });
  if (!response.ok) {
    throw new SpotifyApiError("Spotify could not finish authentication.", response.status);
  }
  return response.json() as Promise<TokenResponse>;
}

export async function getClientAccessToken(): Promise<string> {
  if (clientToken && clientToken.expiresAt > Date.now() + 60_000) return clientToken.value;
  const token = await tokenRequest(new URLSearchParams({ grant_type: "client_credentials" }));
  clientToken = {
    value: token.access_token,
    expiresAt: Date.now() + token.expires_in * 1000,
  };
  return clientToken.value;
}

export async function exchangeAuthorizationCode(
  code: string,
  redirectUri: string,
): Promise<TokenResponse> {
  return tokenRequest(new URLSearchParams({
    grant_type: "authorization_code",
    code,
    redirect_uri: redirectUri,
  }));
}

export async function refreshSpotifyToken(refreshToken: string): Promise<TokenResponse> {
  return tokenRequest(new URLSearchParams({
    grant_type: "refresh_token",
    refresh_token: refreshToken,
  }));
}

async function spotifyRequest<T>(path: string, accessToken?: string): Promise<T> {
  const token = accessToken ?? await getClientAccessToken();
  const response = await fetch(`${SPOTIFY_API}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
    signal: AbortSignal.timeout(12_000),
  });
  if (!response.ok) {
    const retryAfter = Number(response.headers.get("retry-after"));
    const message = response.status === 403
      ? "This Spotify account is not enabled for the development app."
      : response.status === 429
        ? "Spotify is busy. Try again in a moment."
        : "Spotify could not load that music right now.";
    throw new SpotifyApiError(
      message,
      response.status,
      Number.isFinite(retryAfter) ? retryAfter : null,
    );
  }
  return response.json() as Promise<T>;
}

function publicTrack(track: SpotifyTrack): PublicSpotifyTrack {
  return {
    id: track.id,
    name: track.name,
    artists: track.artists.map((artist) => artist.name),
    artistIds: track.artists.map((artist) => artist.id),
    album: track.album.name,
    albumId: track.album.id,
    imageUrl: track.album.images[0]?.url ?? null,
    spotifyUrl: track.external_urls.spotify,
    durationMs: track.duration_ms,
    explicit: track.explicit,
    releaseDate: track.album.release_date,
  };
}

function albumTrack(track: SpotifySimplifiedTrack, album: SpotifyAlbum): SpotifyTrack {
  return { ...track, album };
}

export async function searchSpotifyTracks(query: string, limit = 8): Promise<PublicSpotifyTrack[]> {
  const cleanQuery = query.trim().slice(0, 120);
  if (cleanQuery.length < 2) return [];
  const params = new URLSearchParams({
    q: cleanQuery,
    type: "track",
    limit: String(Math.min(10, Math.max(1, limit))),
  });
  const result = await spotifyRequest<SpotifySearchResponse>(`/search?${params}`);
  return result.tracks.items.map(publicTrack);
}

export async function getSpotifyProfile(accessToken: string): Promise<SpotifyProfile> {
  return spotifyRequest<SpotifyProfile>("/me", accessToken);
}

async function getTrack(trackId: string, accessToken?: string): Promise<SpotifyTrack> {
  return spotifyRequest<SpotifyTrack>(`/tracks/${encodeURIComponent(trackId)}`, accessToken);
}

type CatalogTrack = {
  track: SpotifyTrack;
  sourceArtist: SpotifyArtist;
  albumRank: number;
  trackPosition: number;
};

async function artistCatalog(
  artist: SpotifyArtist,
  albumLimit: number,
  accessToken?: string,
  albumRotation = 0,
): Promise<CatalogTrack[]> {
  const params = new URLSearchParams({
    include_groups: "album,single",
    limit: String(Math.min(10, Math.max(8, albumLimit))),
  });
  const albums = await spotifyRequest<SpotifyPaging<SpotifyAlbum>>(
    `/artists/${encodeURIComponent(artist.id)}/albums?${params}`,
    accessToken,
  );
  const uniqueAlbums = rotatingWindow(
    [...new Map(albums.items.map((album) => [album.id, album])).values()],
    albumRotation,
    albumLimit,
  );
  const trackPages = await Promise.all(uniqueAlbums.map((album) =>
    spotifyRequest<SpotifyPaging<SpotifySimplifiedTrack>>(
      `/albums/${encodeURIComponent(album.id)}/tracks?limit=50`,
      accessToken,
    ).then((page) => page.items.map((track) => albumTrack(track, album))),
  ));
  return trackPages.flatMap((tracks, albumRank) => tracks.map((track, trackPosition) => ({
    track,
    sourceArtist: artist,
    albumRank,
    trackPosition,
  })));
}

const LOW_VALUE_VERSION = /\b(intro|outro|interlude|skit|commentary|voice memo|instrumental|karaoke|sped up|slowed|radio edit)\b/i;

function candidatePenalty(track: SpotifyTrack, seedName = ""): number {
  let penalty = 0;
  if (track.duration_ms < 75_000) penalty += 50;
  else if (track.duration_ms < 120_000) penalty += 12;
  if (LOW_VALUE_VERSION.test(track.name) && !LOW_VALUE_VERSION.test(seedName)) penalty += 28;
  if (/\b(live|remix|remastered)\b/i.test(track.name) && !/\b(live|remix|remastered)\b/i.test(seedName)) {
    penalty += 10;
  }
  return penalty;
}

function dedupeTracks(tracks: CatalogTrack[], excluded: Set<string>): CatalogTrack[] {
  const seenIds = new Set<string>();
  const seenNames = new Set<string>();
  return tracks.filter(({ track }) => {
    const nameKey = `${track.name.toLowerCase()}::${track.artists[0]?.name.toLowerCase() ?? ""}`;
    if (excluded.has(track.id) || seenIds.has(track.id) || seenNames.has(nameKey)) return false;
    seenIds.add(track.id);
    seenNames.add(nameKey);
    return true;
  });
}

function releaseYear(track: SpotifyTrack): number | null {
  const year = Number(track.album.release_date.slice(0, 4));
  return Number.isFinite(year) ? year : null;
}

export async function recommendFromSpotifyTrack(trackId: string): Promise<{
  seed: PublicSpotifyTrack;
  recommendations: SpotifyRecommendation[];
}> {
  const seed = await getTrack(trackId);
  const seedArtistIds = new Set(seed.artists.map((artist) => artist.id));
  const mainCatalogs = await Promise.all(seed.artists.slice(0, 2).map((artist) =>
    artistCatalog(artist, 6),
  ));
  const mainCatalog = mainCatalogs.flat();

  const collaboratorCounts = new Map<string, { artist: SpotifyArtist; count: number }>();
  for (const { track } of mainCatalog) {
    for (const artist of track.artists) {
      if (seedArtistIds.has(artist.id)) continue;
      const current = collaboratorCounts.get(artist.id);
      collaboratorCounts.set(artist.id, {
        artist,
        count: (current?.count ?? 0) + 1,
      });
    }
  }
  const collaborators = [...collaboratorCounts.values()]
    .sort((left, right) => right.count - left.count || left.artist.name.localeCompare(right.artist.name))
    .slice(0, 3)
    .map(({ artist }) => artist);
  const collaboratorCatalogs = await Promise.all(collaborators.map((artist) =>
    artistCatalog(artist, 2),
  ));

  const candidates = dedupeTracks(
    [...mainCatalog, ...collaboratorCatalogs.flat()],
    new Set([seed.id]),
  );
  const currentYear = new Date().getUTCFullYear();
  const ranked = candidates.filter((candidate) => candidatePenalty(candidate.track, seed.name) < 28)
    .map((candidate) => {
    const sameArtist = candidate.track.artists.some((artist) => seedArtistIds.has(artist.id));
    const collaborator = collaborators.find((artist) => artist.id === candidate.sourceArtist.id);
    const year = releaseYear(candidate.track);
    const reasons = sameArtist
      ? [`more from ${candidate.sourceArtist.name}`, year ? `from ${year}` : "from the catalog"]
      : [
          collaborator ? `connected through ${collaborator.name}` : "from the same artist circle",
          year ? `from ${year}` : "a different branch",
        ];
    const score = (sameArtist ? 100 : 62)
      - candidate.albumRank * 3
      - Math.min(candidate.trackPosition, 12) * 0.15
      - candidatePenalty(candidate.track, seed.name)
      + (year && year >= currentYear - 2 ? 4 : 0)
      + (candidate.track.artists.length > 1 ? 2 : 0);
    return {
      score,
      sourceArtistId: candidate.sourceArtist.id,
      recommendation: {
        track: publicTrack(candidate.track),
        reasons,
        connection: sameArtist ? "closest" as const : "connected" as const,
      },
    };
    }).sort((left, right) => right.score - left.score || left.recommendation.track.name.localeCompare(right.recommendation.track.name));

  const perArtist = new Map<string, number>();
  const perAlbum = new Map<string, number>();
  const recommendations = ranked.filter((entry) => {
    const count = perArtist.get(entry.sourceArtistId) ?? 0;
    const albumCount = perAlbum.get(entry.recommendation.track.albumId) ?? 0;
    const limit = seedArtistIds.has(entry.sourceArtistId) ? 4 : 2;
    if (count >= limit || albumCount >= 2) return false;
    perArtist.set(entry.sourceArtistId, count + 1);
    perAlbum.set(entry.recommendation.track.albumId, albumCount + 1);
    return true;
  }).slice(0, 12).map((entry) => entry.recommendation);

  return { seed: publicTrack(seed), recommendations };
}

export async function recommendationsForSpotifyUser(
  accessToken: string,
  options: { excludeTrackIds?: unknown; mixNumber?: unknown } = {},
): Promise<{
  topTracks: PublicSpotifyTrack[];
  recommendations: SpotifyRecommendation[];
  mixNumber: number;
  freshCount: number;
}> {
  const mixNumber = normalizeMixNumber(options.mixNumber);
  const previouslyShown = new Set(normalizeTrackHistory(options.excludeTrackIds));
  const tasteRanges = [
    { timeRange: "short_term", limit: 20, weight: 1.25 },
    { timeRange: "medium_term", limit: 30, weight: 1 },
    { timeRange: "long_term", limit: 20, weight: 0.8 },
  ] as const;
  const topResponses = await Promise.all(tasteRanges.map(async (range) => {
    const params = new URLSearchParams({
      time_range: range.timeRange,
      limit: String(range.limit),
    });
    const response = await spotifyRequest<SpotifyTopTracksResponse>(
      `/me/top/tracks?${params}`,
      accessToken,
    );
    return { ...range, tracks: response.items };
  }));

  const trackTaste = new Map<string, { track: SpotifyTrack; score: number; bestRank: number }>();
  const artistTaste = new Map<string, { artist: SpotifyArtist; score: number; bestRank: number }>();
  for (const range of topResponses) {
    for (const [trackRank, track] of range.tracks.entries()) {
      const score = range.weight * (range.limit - trackRank);
      const knownTrack = trackTaste.get(track.id);
      trackTaste.set(track.id, {
        track,
        score: (knownTrack?.score ?? 0) + score,
        bestRank: Math.min(knownTrack?.bestRank ?? Number.POSITIVE_INFINITY, trackRank),
      });
      for (const artist of track.artists) {
        const knownArtist = artistTaste.get(artist.id);
        artistTaste.set(artist.id, {
          artist,
          score: (knownArtist?.score ?? 0) + score / Math.sqrt(track.artists.length),
          bestRank: Math.min(knownArtist?.bestRank ?? Number.POSITIVE_INFINITY, trackRank),
        });
      }
    }
  }

  const rankedTopTracks = [...trackTaste.values()]
    .sort((left, right) => right.score - left.score || left.bestRank - right.bestRank);
  const topTracks = rankedTopTracks.map(({ track }) => publicTrack(track));
  const excludedTopTracks = new Set(rankedTopTracks.map(({ track }) => track.id));
  const favoriteArtistPool = [...artistTaste.values()]
    .sort((left, right) => right.score - left.score || left.bestRank - right.bestRank)
    .slice(0, 16);
  const favoriteArtists = rotatingSelection(favoriteArtistPool, mixNumber, 8);
  const selectedFavoriteIds = new Set(favoriteArtists.map(({ artist }) => artist.id));
  const favoriteCatalogs = await Promise.all(favoriteArtists.map(({ artist }, index) =>
    artistCatalog(artist, 2, accessToken, mixNumber * 2 + index),
  ));
  const favoriteCatalog = favoriteCatalogs.flat();

  const collaboratorCounts = new Map<string, {
    artist: SpotifyArtist;
    count: number;
    connectedThrough: SpotifyArtist;
  }>();
  for (const { track, sourceArtist } of favoriteCatalog) {
    for (const artist of track.artists) {
      if (artistTaste.has(artist.id) || selectedFavoriteIds.has(artist.id)) continue;
      const current = collaboratorCounts.get(artist.id);
      collaboratorCounts.set(artist.id, {
        artist,
        count: (current?.count ?? 0) + 1,
        connectedThrough: current?.connectedThrough ?? sourceArtist,
      });
    }
  }
  const collaboratorPool = [...collaboratorCounts.values()]
    .sort((left, right) => right.count - left.count || left.artist.name.localeCompare(right.artist.name));
  const collaborators = rotatingWindow(collaboratorPool, mixNumber * 3, 4);
  const collaboratorCatalogs = await Promise.all(collaborators.map(({ artist }, index) =>
    artistCatalog(artist, 1, accessToken, mixNumber + index),
  ));

  const candidates = dedupeTracks(
    [...favoriteCatalog, ...collaboratorCatalogs.flat()],
    excludedTopTracks,
  );
  const currentYear = new Date().getUTCFullYear();
  const ranked = candidates.filter((candidate) => candidatePenalty(candidate.track) < 28)
    .map((candidate) => {
      const favorite = artistTaste.get(candidate.sourceArtist.id);
      const favoriteRank = favoriteArtistPool.findIndex(
        ({ artist }) => artist.id === candidate.sourceArtist.id,
      );
      const collaborator = collaboratorCounts.get(candidate.sourceArtist.id);
      const year = releaseYear(candidate.track);
      const seenBefore = previouslyShown.has(candidate.track.id);
      const isFavorite = Boolean(favorite);
      const reasons = isFavorite
        ? [
            `from ${candidate.sourceArtist.name}, past the songs you already play`,
            year ? `a ${year} find` : "from deeper in the catalog",
          ]
        : [
            collaborator
              ? `connected through ${collaborator.connectedThrough.name}`
              : "from an artist just outside your usual rotation",
            year && year >= currentYear - 2 ? "a newer find" : "a different corner of the catalog",
          ];
      const score = (isFavorite ? 102 - Math.max(0, favoriteRank) * 2.5 : 72 + (collaborator?.count ?? 0) * 2)
        - candidate.albumRank * 2.5
        - Math.min(candidate.trackPosition, 15) * 0.12
        - candidatePenalty(candidate.track)
        + (year && year >= currentYear - 2 ? 4 : 0)
        + stableVariation(candidate.track.id, mixNumber) * 18
        - (seenBefore ? 120 : 0);
      return {
        score,
        seenBefore,
        sourceArtistId: candidate.sourceArtist.id,
        recommendation: {
          track: publicTrack(candidate.track),
          reasons,
          connection: isFavorite
            ? favoriteRank < 6 ? "closest" as const : "explore" as const
            : collaborator ? "connected" as const : "explore" as const,
        },
      };
    }).sort((left, right) => right.score - left.score
      || left.recommendation.track.name.localeCompare(right.recommendation.track.name));

  const perArtist = new Map<string, number>();
  const perAlbum = new Map<string, number>();
  const recommendations = ranked.filter((entry) => {
    const count = perArtist.get(entry.sourceArtistId) ?? 0;
    const albumCount = perAlbum.get(entry.recommendation.track.albumId) ?? 0;
    if (count >= 2 || albumCount >= 1) return false;
    perArtist.set(entry.sourceArtistId, count + 1);
    perAlbum.set(entry.recommendation.track.albumId, albumCount + 1);
    return true;
  }).slice(0, 16);

  return {
    topTracks: topTracks.slice(0, 8),
    recommendations: recommendations.map((entry) => entry.recommendation),
    mixNumber,
    freshCount: recommendations.filter((entry) => !entry.seenBefore).length,
  };
}
