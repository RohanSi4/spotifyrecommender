"use client";

import { useMemo, useState } from "react";

import { SignalMark } from "@/components/signal-mark";
import { TrackResult } from "@/components/track-result";
import {
  buildDemoCatalog,
  MOOD_NAMES,
  type MoodName,
  rankByMood,
  rankByTrack,
  type RankedTrack,
} from "@/lib/recommender";

type Mode = "song" | "mood";

const MOOD_COPY: Record<MoodName, string> = {
  happy: "bright",
  sad: "soft",
  energetic: "charged",
  calm: "quiet",
  relaxed: "easy",
  party: "social",
  focus: "locked in",
  workout: "moving",
  romantic: "warm",
};

export function SignalApp() {
  const catalog = useMemo(() => buildDemoCatalog(), []);
  const [mode, setMode] = useState<Mode>("song");
  const [seedId, setSeedId] = useState(catalog[0].id);
  const [mood, setMood] = useState<MoodName>("focus");
  const [results, setResults] = useState<RankedTrack[]>(() =>
    rankByTrack(catalog[0], catalog, 8),
  );
  const [resultContext, setResultContext] = useState("Afterglow Avenue");

  const handleRank = () => {
    if (mode === "song") {
      const seed = catalog.find((track) => track.id === seedId) ?? catalog[0];
      setResults(rankByTrack(seed, catalog, 8));
      setResultContext(seed.name);
    } else {
      setResults(rankByMood(mood, catalog, 8));
      setResultContext(`${MOOD_COPY[mood]} energy`);
    }
  };

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
            className={mode === "mood" ? "active" : ""}
            onClick={() => setMode("mood")}
            aria-pressed={mode === "mood"}
          >
            Start with a mood
          </button>
        </div>

        {mode === "song" ? (
          <div className="control-block">
            <label htmlFor="seed-track">Choose a reference song</label>
            <div className="select-wrap">
              <select id="seed-track" value={seedId} onChange={(event) => setSeedId(event.target.value)}>
                {catalog.map((track) => (
                  <option key={track.id} value={track.id}>
                    {track.name} by {track.artist}
                  </option>
                ))}
              </select>
              <span aria-hidden="true">⌄</span>
            </div>
            <p>We use this song as the target, then rank everything else by closeness.</p>
          </div>
        ) : (
          <fieldset className="control-block mood-fieldset">
            <legend>Pick a direction</legend>
            <div className="mood-grid">
              {MOOD_NAMES.map((name) => (
                <button
                  type="button"
                  key={name}
                  className={mood === name ? "active" : ""}
                  onClick={() => setMood(name)}
                  aria-pressed={mood === name}
                >
                  <span>{name}</span>
                  <small>{MOOD_COPY[name]}</small>
                </button>
              ))}
            </div>
          </fieldset>
        )}

        <button className="rank-button" onClick={handleRank}>
          <SignalMark compact />
          Find my matches
        </button>

        <div className="privacy-note">
          <span aria-hidden="true">✦</span>
          <p><strong>Nothing leaves your browser.</strong><br />This demo has no server-side recommendation call.</p>
        </div>
      </aside>

      <div className="results" aria-live="polite">
        <div className="results-header">
          <div>
            <p className="eyebrow"><span /> Best matches</p>
            <h2>Close to {resultContext}</h2>
          </div>
          <p>{results.length} of {catalog.length} tracks</p>
        </div>

        <div className="result-list">
          {results.map((track, index) => (
            <TrackResult key={track.id} rank={index + 1} track={track} />
          ))}
        </div>
      </div>
    </div>
  );
}
