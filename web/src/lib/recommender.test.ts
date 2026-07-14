import { describe, expect, it } from "vitest";

import {
  buildDemoCatalog,
  MOOD_NAMES,
  rankByMood,
  rankByTrack,
} from "./recommender";

describe("portable Signal ranker", () => {
  it("builds a stable catalog with eight tracks per mood", () => {
    const first = buildDemoCatalog();
    const second = buildDemoCatalog();

    expect(first).toEqual(second);
    expect(first).toHaveLength(MOOD_NAMES.length * 8);
    expect(new Set(first.map((track) => track.id)).size).toBe(first.length);
  });

  it("ranks by song, excludes the seed, and sorts descending", () => {
    const catalog = buildDemoCatalog();
    const seed = catalog[0];
    const results = rankByTrack(seed, catalog, 8);

    expect(results).toHaveLength(8);
    expect(results.some((track) => track.id === seed.id)).toBe(false);
    expect(results.every((track) => track.reasons.length === 2)).toBe(true);
    expect(results.map((track) => track.score)).toEqual(
      [...results.map((track) => track.score)].sort((left, right) => right - left),
    );
  });

  it("ranks every supported mood without credentials", () => {
    const catalog = buildDemoCatalog();

    for (const mood of MOOD_NAMES) {
      const results = rankByMood(mood, catalog, 5);
      expect(results).toHaveLength(5);
      expect(results[0].score).toBeGreaterThan(0.9);
      expect(results.every((track) => track.score > 0 && track.score <= 1)).toBe(true);
    }
  });
});
