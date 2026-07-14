import { NextRequest, NextResponse } from "next/server";

import { allowRequest, requestIdentity } from "@/lib/rate-limit";
import { searchSpotifyTracks, SpotifyApiError } from "@/lib/spotify";

export async function GET(request: NextRequest) {
  if (!allowRequest(`search:${requestIdentity(request.headers)}`)) {
    return NextResponse.json({ error: "Too many searches. Give it a minute." }, { status: 429 });
  }
  const query = request.nextUrl.searchParams.get("q")?.trim() ?? "";
  if (query.length < 2) return NextResponse.json({ tracks: [] });
  try {
    const tracks = await searchSpotifyTracks(query, 8);
    return NextResponse.json({ tracks }, {
      headers: { "Cache-Control": "public, s-maxage=300, stale-while-revalidate=3600" },
    });
  } catch (error) {
    const status = error instanceof SpotifyApiError ? error.status : 502;
    const message = error instanceof Error ? error.message : "Spotify search failed.";
    return NextResponse.json({ error: message }, { status });
  }
}
