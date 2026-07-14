export type FeatureName =
  | "danceability"
  | "energy"
  | "loudness"
  | "speechiness"
  | "acousticness"
  | "instrumentalness"
  | "liveness"
  | "valence"
  | "tempo";

export type MoodName =
  | "happy"
  | "sad"
  | "energetic"
  | "calm"
  | "relaxed"
  | "party"
  | "focus"
  | "workout"
  | "romantic";

export interface TrackFeatures {
  danceability: number;
  energy: number;
  loudness: number;
  speechiness: number;
  acousticness: number;
  instrumentalness: number;
  liveness: number;
  valence: number;
  tempo: number;
}

export interface Track {
  id: string;
  name: string;
  artist: string;
  collection: string;
  mood: MoodName;
  features: TrackFeatures;
}

export interface RankedTrack extends Track {
  score: number;
  reasons: string[];
}

interface FeatureSpec {
  min: number;
  max: number;
  weight: number;
  label: string;
}

export const FEATURE_SPECS: Record<FeatureName, FeatureSpec> = {
  danceability: { min: 0, max: 1, weight: 1.1, label: "danceability" },
  energy: { min: 0, max: 1, weight: 1.3, label: "energy" },
  loudness: { min: -60, max: 0, weight: 0.5, label: "intensity" },
  speechiness: { min: 0, max: 1, weight: 0.6, label: "vocal style" },
  acousticness: { min: 0, max: 1, weight: 0.9, label: "acoustic texture" },
  instrumentalness: { min: 0, max: 1, weight: 0.7, label: "instrumental feel" },
  liveness: { min: 0, max: 1, weight: 0.4, label: "live feel" },
  valence: { min: 0, max: 1, weight: 1.2, label: "mood" },
  tempo: { min: 40, max: 220, weight: 0.8, label: "tempo" },
};

export const MOOD_PROFILES: Record<MoodName, Partial<TrackFeatures>> = {
  happy: { valence: 0.82, energy: 0.68, danceability: 0.72, tempo: 124 },
  sad: { valence: 0.18, energy: 0.3, acousticness: 0.62, tempo: 78 },
  energetic: { energy: 0.92, danceability: 0.68, tempo: 150, valence: 0.65 },
  calm: { energy: 0.22, acousticness: 0.78, speechiness: 0.08, tempo: 76 },
  relaxed: { energy: 0.3, acousticness: 0.68, valence: 0.55, tempo: 88 },
  party: { danceability: 0.9, energy: 0.86, valence: 0.76, tempo: 128 },
  focus: { energy: 0.38, instrumentalness: 0.78, speechiness: 0.04, tempo: 100 },
  workout: { energy: 0.96, danceability: 0.78, tempo: 156, valence: 0.62 },
  romantic: { valence: 0.62, energy: 0.42, acousticness: 0.52, tempo: 96 },
};

const FEATURE_NAMES = Object.keys(FEATURE_SPECS) as FeatureName[];
export const MOOD_NAMES = Object.keys(MOOD_PROFILES) as MoodName[];

const TITLES: Record<MoodName, string[]> = {
  happy: ["Afterglow Avenue", "Open Window", "Lemon Light", "Good Company", "Day Off", "Lucky Streak", "Sunroom", "Easy Yes"],
  sad: ["Blue Hour Letters", "Almost Home", "November Glass", "Quiet Goodbye", "Half a Memory", "Night Bus", "Slow Rain", "Elsewhere"],
  energetic: ["Circuit Breaker", "Redline", "Fast Forward", "Voltage", "Second Wind", "Full Send", "No Ceiling", "Momentum"],
  calm: ["Quiet Tides", "Soft Current", "Still Water", "Low Light", "Open Sky", "Driftwood", "Long Exhale", "Sunday Air"],
  relaxed: ["Sunday Static", "Side Street", "Late Checkout", "Window Seat", "Warm Concrete", "Unrushed", "Back Porch", "Slow Lane"],
  party: ["Neon Kitchen", "House Lights", "One More Song", "Midnight Crowd", "Good Trouble", "Disco Receipt", "Out Past Two", "All Together"],
  focus: ["Deep Work Drift", "Quiet Hours", "Flow State", "No Distractions", "Clean Desk", "Long Form", "Single Thread", "In the Zone"],
  workout: ["Last Rep", "Hill Repeat", "Negative Split", "Heavy Set", "Final Lap", "Push Through", "Game Pace", "New Gear"],
  romantic: ["Velvet Polaroid", "Close Enough", "Slow Dance", "Table for Two", "Soft Focus", "Stay a While", "Warm Hands", "Between Us"],
};

const ARTISTS = [
  "Mara Vale",
  "Northbound Club",
  "Sienna Park",
  "Juniper FM",
  "Local Weather",
  "Night Service",
  "Tonal Theory",
  "The Open Roads",
] as const;

function seededValue(seed: number): number {
  const value = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return value - Math.floor(value);
}

function jitter(seed: number): number {
  return (seededValue(seed) + seededValue(seed + 97) + seededValue(seed + 211)) / 3 - 0.5;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function buildFeatures(mood: MoodName, moodIndex: number, trackIndex: number): TrackFeatures {
  return Object.fromEntries(
    FEATURE_NAMES.map((name, featureIndex) => {
      const spec = FEATURE_SPECS[name];
      const center = MOOD_PROFILES[mood][name] ?? (spec.min + spec.max) / 2;
      const spread = (spec.max - spec.min) * (name === "tempo" ? 0.055 : 0.1);
      const value = clamp(
        center + jitter(20260714 + moodIndex * 1009 + trackIndex * 97 + featureIndex * 17) * spread,
        spec.min,
        spec.max,
      );
      return [name, Number(value.toFixed(5))];
    }),
  ) as unknown as TrackFeatures;
}

export function buildDemoCatalog(): Track[] {
  return MOOD_NAMES.flatMap((mood, moodIndex) =>
    TITLES[mood].map((name, trackIndex) => ({
      id: `demo-${mood}-${String(trackIndex + 1).padStart(2, "0")}`,
      name,
      artist: ARTISTS[(moodIndex * 3 + trackIndex) % ARTISTS.length],
      collection: "Signal demo catalog",
      mood,
      features: buildFeatures(mood, moodIndex, trackIndex),
    })),
  );
}

function vectorize(features: TrackFeatures): number[] {
  return FEATURE_NAMES.map((name) => {
    const spec = FEATURE_SPECS[name];
    return clamp((features[name] - spec.min) / (spec.max - spec.min), 0, 1);
  });
}

function similarity(target: number[], candidate: number[]): number {
  const weightedDifference = target.reduce((total, value, index) => {
    const weight = FEATURE_SPECS[FEATURE_NAMES[index]].weight;
    return total + (value - candidate[index]) ** 2 * weight;
  }, 0);
  const totalWeight = FEATURE_NAMES.reduce((total, name) => total + FEATURE_SPECS[name].weight, 0);
  return 1 / (1 + Math.sqrt(weightedDifference / totalWeight));
}

function matchReasons(target: number[], candidate: number[]): string[] {
  return FEATURE_NAMES.map((name, index) => ({
    name,
    difference: Math.abs(target[index] - candidate[index]),
  }))
    .sort((left, right) => left.difference - right.difference)
    .slice(0, 2)
    .map(({ name }) => `similar ${FEATURE_SPECS[name].label}`);
}

function rank(target: number[], candidates: Track[], excludedId?: string, limit = 8): RankedTrack[] {
  return candidates
    .filter((track) => track.id !== excludedId)
    .map((track) => {
      const vector = vectorize(track.features);
      return {
        ...track,
        score: similarity(target, vector),
        reasons: matchReasons(target, vector),
      };
    })
    .sort((left, right) => right.score - left.score || left.id.localeCompare(right.id))
    .slice(0, limit);
}

export function rankByTrack(seed: Track, candidates: Track[], limit = 8): RankedTrack[] {
  return rank(vectorize(seed.features), candidates, seed.id, limit);
}

export function rankByMood(mood: MoodName, candidates: Track[], limit = 8): RankedTrack[] {
  const baseline = Object.fromEntries(
    FEATURE_NAMES.map((name) => {
      const spec = FEATURE_SPECS[name];
      return [name, MOOD_PROFILES[mood][name] ?? (spec.min + spec.max) / 2];
    }),
  ) as unknown as TrackFeatures;
  return rank(vectorize(baseline), candidates, undefined, limit);
}

export function scoreLabel(score: number): string {
  return `${Math.round(score * 100)}%`;
}
