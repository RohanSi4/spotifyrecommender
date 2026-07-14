import { NextRequest, NextResponse } from "next/server";

import { allowRequest, requestIdentity } from "@/lib/rate-limit";
import { recommendFromSpotifyTrack, SpotifyApiError } from "@/lib/spotify";

export async function POST(request: NextRequest) {
  if (!allowRequest(`recommend:${requestIdentity(request.headers)}`, 12)) {
    return NextResponse.json({ error: "Too many mixes. Give Spotify a minute." }, { status: 429 });
  }
  const body = await request.json().catch(() => null) as { trackId?: unknown } | null;
  const trackId = typeof body?.trackId === "string" ? body.trackId : "";
  if (!/^[A-Za-z0-9]{10,40}$/.test(trackId)) {
    return NextResponse.json({ error: "Choose a Spotify song first." }, { status: 400 });
  }
  try {
    return NextResponse.json(await recommendFromSpotifyTrack(trackId));
  } catch (error) {
    const status = error instanceof SpotifyApiError ? error.status : 502;
    const message = error instanceof Error ? error.message : "Spotify could not build that mix.";
    return NextResponse.json({ error: message }, { status });
  }
}
