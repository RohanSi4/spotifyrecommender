# Signal web app

Signal is a live music discovery app built with Next.js and Spotify. A visitor can search the real Spotify catalog, choose any track, and get a mix assembled from that artist's releases and collaborators. Invited Spotify users can also connect their account for deeper cuts based on their actual top songs.

The app does not invent audio traits, similarity scores, or song data. Every result includes real Spotify metadata, album art, a direct listening link, and a plain-language reason for appearing.

## Local setup

```bash
npm install
cp .env.example .env.local
npm run dev
```

Register `http://localhost:3000/api/auth/callback` in the Spotify Developer Dashboard if you want to test account login. Public search works with client credentials and does not require a visitor to log in.

## Environment variables

- `SPOTIFY_CLIENT_ID`: Spotify app client ID
- `SPOTIFY_CLIENT_SECRET`: Spotify app client secret, server only
- `SPOTIFY_REDIRECT_URI`: exact registered callback URL
- `SIGNAL_SESSION_SECRET`: random string of at least 32 characters used to encrypt login cookies

## Verify

```bash
npm run check
```

This runs ESLint, session and rate-limit tests, TypeScript checks, and a production build.

## Production

The live app is [signal-recommender.vercel.app](https://signal-recommender.vercel.app). Vercel deploys the `web` directory from `main`. All four environment variables must be configured in Vercel, and the production callback must be registered with Spotify as `https://signal-recommender.vercel.app/api/auth/callback`.

Spotify limits new development-mode apps to five invited users. That restriction only affects account-based personal mixes. Real catalog search and song-based mixes remain available to every visitor.
