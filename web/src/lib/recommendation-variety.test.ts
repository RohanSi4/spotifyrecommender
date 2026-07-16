import { describe, expect, it } from "vitest";

import {
  MAX_RECOMMENDATION_HISTORY,
  normalizeMixNumber,
  normalizeTrackHistory,
  rotatingSelection,
  rotatingWindow,
  stableVariation,
} from "./recommendation-variety";

describe("recommendation variety", () => {
  it("keeps only valid, unique Spotify track ids", () => {
    expect(normalizeTrackHistory([
      "1234567890AB",
      "bad",
      "1234567890AB",
      42,
      "ZYXWVUTSRQPONMLKJIHGFE",
    ])).toEqual(["1234567890AB", "ZYXWVUTSRQPONMLKJIHGFE"]);
  });

  it("caps history sent to Spotify recommendation logic", () => {
    const ids = Array.from({ length: MAX_RECOMMENDATION_HISTORY + 20 }, (_, index) =>
      `track${String(index).padStart(10, "0")}`,
    );
    expect(normalizeTrackHistory(ids)).toHaveLength(MAX_RECOMMENDATION_HISTORY);
  });

  it("normalizes mix numbers", () => {
    expect(normalizeMixNumber(4)).toBe(4);
    expect(normalizeMixNumber(-1)).toBe(0);
    expect(normalizeMixNumber(2.5)).toBe(0);
    expect(normalizeMixNumber(99_999)).toBe(10_000);
  });

  it("keeps the strongest anchors while rotating the rest", () => {
    const items = ["a", "b", "c", "d", "e", "f", "g", "h", "i"];
    expect(rotatingSelection(items, 0, 5)).toEqual(["a", "b", "c", "d", "e"]);
    expect(rotatingSelection(items, 1, 5)).toEqual(["a", "b", "f", "g", "h"]);
  });

  it("wraps catalog windows instead of returning the same first albums", () => {
    expect(rotatingWindow(["a", "b", "c", "d"], 3, 2)).toEqual(["d", "a"]);
  });

  it("produces stable variation that changes between mixes", () => {
    expect(stableVariation("track-id", 2)).toBe(stableVariation("track-id", 2));
    expect(stableVariation("track-id", 2)).not.toBe(stableVariation("track-id", 3));
  });
});
