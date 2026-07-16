const SPOTIFY_ID = /^[A-Za-z0-9]{10,40}$/;

export const MAX_RECOMMENDATION_HISTORY = 120;

export function normalizeTrackHistory(value: unknown): string[] {
  if (!Array.isArray(value)) return [];

  const unique = new Set<string>();
  for (const entry of value) {
    if (typeof entry !== "string" || !SPOTIFY_ID.test(entry) || unique.has(entry)) continue;
    unique.add(entry);
    if (unique.size >= MAX_RECOMMENDATION_HISTORY) break;
  }
  return [...unique];
}

export function normalizeMixNumber(value: unknown): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < 0) return 0;
  return Math.min(value, 10_000);
}

export function rotatingSelection<T>(items: T[], mixNumber: number, count: number): T[] {
  if (count <= 0 || items.length === 0) return [];
  if (items.length <= count) return [...items];

  const anchorCount = Math.min(2, count);
  const anchors = items.slice(0, anchorCount);
  const rotatingPool = items.slice(anchorCount);
  const rotatingCount = count - anchorCount;
  const offset = (mixNumber * Math.max(1, rotatingCount)) % rotatingPool.length;
  const rotating = Array.from(
    { length: rotatingCount },
    (_, index) => rotatingPool[(offset + index) % rotatingPool.length],
  );
  return [...anchors, ...rotating];
}

export function rotatingWindow<T>(items: T[], offset: number, count: number): T[] {
  if (count <= 0 || items.length === 0) return [];
  const size = Math.min(items.length, count);
  const start = ((offset % items.length) + items.length) % items.length;
  return Array.from({ length: size }, (_, index) => items[(start + index) % items.length]);
}

export function stableVariation(key: string, mixNumber: number): number {
  let hash = 2166136261 ^ mixNumber;
  for (let index = 0; index < key.length; index += 1) {
    hash ^= key.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0) / 0xffffffff;
}
