# Signal web demo

This folder is the public, credential-free version of Signal. It is a standalone
Next.js app designed to deploy from the `web` root on Vercel.

The interaction is real. A visitor can select any of 72 deterministic demo
tracks or choose one of nine mood profiles. Ranking happens entirely in the
browser using the same normalized, weighted nine-feature method documented in
the Python engine at the repository root.

## Run it

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Verify it

```bash
npm run check
```

That command runs ESLint, the portable ranking tests, and a production build.

## Deploy it on Vercel

Use these project settings:

- Project name: `signal-recommender`
- Root directory: `web`
- Framework preset: Next.js
- Install command: `npm install`
- Build command: `npm run build`
- Output directory: leave blank
- Environment variables: none

The app has no server-side data dependency, OAuth flow, cookie, or required
secret. Vercel can deploy every push to the repository's main branch.

## Honest scope

Spotify restricts audio-feature access for most new development apps. This
hosted demo therefore uses synthetic track names and feature profiles. It shows
the real ranking behavior without presenting synthetic results as listener
research or production recommendation quality.
