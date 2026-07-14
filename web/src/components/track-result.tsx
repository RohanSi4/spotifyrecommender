import type { RankedTrack } from "@/lib/recommender";
import { scoreLabel } from "@/lib/recommender";

interface TrackResultProps {
  rank: number;
  track: RankedTrack;
}

export function TrackResult({ rank, track }: TrackResultProps) {
  const hue = (track.id.length * 31 + track.name.charCodeAt(0) * 7) % 360;
  const energy = Math.round(track.features.energy * 100);
  const tempo = Math.round(track.features.tempo);

  return (
    <article className="result-card">
      <div
        className="cover"
        style={{
          background: `radial-gradient(circle at 28% 22%, hsla(${hue}, 92%, 75%, .92), transparent 28%), linear-gradient(145deg, hsl(${hue}, 72%, 42%), hsl(${(hue + 74) % 360}, 62%, 12%))`,
        }}
        aria-hidden="true"
      >
        <span>{String(rank).padStart(2, "0")}</span>
        <div className="cover-wave">
          {[0.55, 0.9, 0.42, 1, 0.64].map((height, index) => (
            <i key={index} style={{ height: `${height * 42}px` }} />
          ))}
        </div>
      </div>

      <div className="result-copy">
        <div className="result-heading">
          <div>
            <h3>{track.name}</h3>
            <p>{track.artist}</p>
          </div>
          <span className="score" aria-label={`${scoreLabel(track.score)} match`}>
            {scoreLabel(track.score)}
          </span>
        </div>

        <div className="reason-list" aria-label="Why it matched">
          {track.reasons.map((reason) => (
            <span key={reason}>{reason}</span>
          ))}
        </div>

        <div className="result-metrics" aria-label="Track features">
          <span>{tempo} bpm</span>
          <span>{energy}% energy</span>
          <span>{track.mood}</span>
        </div>
      </div>
    </article>
  );
}
