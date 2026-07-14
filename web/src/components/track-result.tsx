import Image from "next/image";

import { SignalMark } from "@/components/signal-mark";
import type { SpotifyRecommendation } from "@/lib/spotify";

interface TrackResultProps {
  rank: number;
  recommendation: SpotifyRecommendation;
}

const CONNECTION_LABELS: Record<SpotifyRecommendation["connection"], string> = {
  closest: "close in",
  connected: "artist connection",
  explore: "worth a detour",
};

export function TrackResult({ rank, recommendation }: TrackResultProps) {
  const { track, reasons, connection } = recommendation;
  const year = track.releaseDate.slice(0, 4);

  return (
    <article className="result-card">
      <a className="cover" href={track.spotifyUrl} target="_blank" rel="noreferrer" aria-label={`Play ${track.name} on Spotify`}>
        {track.imageUrl ? (
          <Image src={track.imageUrl} alt={`${track.album} cover`} fill sizes="(max-width: 760px) 76px, 92px" />
        ) : (
          <span className="cover-fallback"><SignalMark /></span>
        )}
        <span className="result-rank">{String(rank).padStart(2, "0")}</span>
      </a>

      <div className="result-copy">
        <div className="result-heading">
          <div>
            <h3><a href={track.spotifyUrl} target="_blank" rel="noreferrer">{track.name}</a></h3>
            <p>{track.artists.join(", ")}</p>
          </div>
          <span className={`connection ${connection}`}>{CONNECTION_LABELS[connection]}</span>
        </div>

        <div className="reason-list" aria-label="Why it is here">
          {reasons.map((reason) => <span key={reason}>{reason}</span>)}
        </div>

        <div className="result-footer">
          <span>{track.album}{year ? ` · ${year}` : ""}</span>
          <a href={track.spotifyUrl} target="_blank" rel="noreferrer" aria-label={`Open ${track.name} in Spotify`}>
            Spotify ↗
          </a>
        </div>
      </div>
    </article>
  );
}
