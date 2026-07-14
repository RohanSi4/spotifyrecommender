# Signal: an explainable music recommender

Signal is an offline-first retrieval experiment for ranking tracks by audio
features. It turns one or more reference tracks, or a mood profile, into a
normalized feature centroid, then ranks a candidate catalog by weighted
distance. Every result includes its score and the two closest matching feature
dimensions.

The default experience is a polished, deterministic demo. It needs no Spotify
account, API key, or network access. Start Streamlit, leave **Demo catalog**
selected, choose **Reference track**, and click **Rank similar tracks** for the
canonical credential-free portfolio path.

The repository also includes a standalone public browser experience in
[`web/`](web/). It ports the same nine-feature weighted ranking method to
TypeScript, needs no secrets, and is ready to deploy from the `web` root on
Vercel. Use the browser app for the hosted portfolio demo and the Python app for
Spotify OAuth experiments, the evaluator, and reference tests.

**Live demo:** [signal-recommender.vercel.app](https://signal-recommender.vercel.app)

## Why this version is honest

Earlier portfolio copy mentioned a 64% match rate at 25, sub-500 ms generation,
and 42% fewer API calls. There was no checked-in dataset or benchmark capable of
reproducing those claims, so they are intentionally **not project results**.

This repository now includes an executable evaluator. On the included 72-track
synthetic regression fixture, the current implementation produced:

- hit-rate@5: **100%**
- mean reciprocal rank: **0.9931**
- local ranking latency: emitted as median and p95 for every run, but not pinned
  as a cross-machine performance claim

Run the evaluator on your machine for a latency sample. The fixture is made of
deliberately separated synthetic mood clusters, so its quality numbers prove
determinism and catch ranking regressions. They do **not** measure real-user
satisfaction or production recommendation relevance.

```bash
python evaluate.py
python evaluate.py --json --iterations 1000
```

## Try it

Python 3.10+ is supported.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run gui_streamlit.py
```

The app opens in **Demo catalog** mode. Choose a reference track or mood and
rank the fixture immediately. A small CLI path exercises the same ranking core:

```bash
python main.py --mood focus --limit 10
python main.py --benchmark
```

## Architecture

```text
Streamlit / CLI
      │
      ├── deterministic demo catalog ─────────────┐
      │                                           ▼
      └── Spotify OAuth → library metadata → RecommendationEngine
                                                  │
                          validate → normalize → centroid → rank → explain
```

- `recommender.py` contains the pure `RecommendationEngine`, feature schema,
  mood profiles, ranking evaluator, and the thin optional Spotify adapter.
- `demo_data.py` generates the publishable fixture from a fixed random seed.
- `evaluate.py` runs leave-one-out hit-rate/MRR evaluation and local latency
  measurement without credentials.
- `gui_streamlit.py` is the maintained UI. `gui.py` is a compatibility launcher.
- `data_collector.py` owns paginated Spotify library reads.
- `tests/` covers ranking order, seed exclusion, invalid data, API restrictions,
  pagination limits, and evaluator determinism.

The ranking core uses nine continuous audio dimensions. `key` and `mode` are
excluded because treating categorical encodings as continuous distance would
produce misleading similarity. Tempo and loudness are range-normalized;
perceptually useful dimensions such as energy and valence receive documented
weights. Seed tracks are excluded from candidates, duplicates are removed, and
ties are stable by track ID.

## Optional Spotify connection

Create an app in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard),
allowlist the test account, and register this exact local callback:
`http://127.0.0.1:8888/callback`.

```bash
cp .env.example .env
# Fill in the three values, then:
streamlit run gui_streamlit.py
```

Only `user-library-read` and `playlist-modify-private` are requested. Secrets and
OAuth caches are ignored by Git. Tests use fakes and never require credentials.

## Spotify API limitations (important)

Spotify restricted Recommendations, Audio Features, Audio Analysis, and Related
Artists for new and development-mode apps in November 2024. Existing extended
quota apps were exempt at that time. In February 2026, Spotify also changed
development-mode access and replaced playlist write paths; new extended-quota
applications are limited to qualifying organizations. See Spotify's official
[2024 endpoint announcement](https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api),
[February 2026 migration guide](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide),
and [quota-mode documentation](https://developer.spotify.com/documentation/web-api/concepts/quota-modes).

Practical effect:

- Demo mode and all tests always work.
- OAuth and library metadata can work for an allowlisted Premium test user.
- Live content/mood ranking needs Audio Features access. Most development-mode
  apps will receive a 403; the UI explains this instead of failing silently.
- The legacy Spotify Recommendations method remains isolated for older
  extended-quota apps, but the main UI does not depend on it.
- Spotify applies a rolling-window rate limit and returns 429 with
  `Retry-After`; calls are batched where the API permits. See the official
  [rate-limit guide](https://developer.spotify.com/documentation/web-api/concepts/rate-limits).

## Development

```bash
pip install -r requirements-dev.txt
pytest -q
ruff check .
ruff format --check .
python evaluate.py --json
```

Verify the hosted experience separately:

```bash
cd web
npm install
npm run check
```

No recommendation-quality claim should be added to this README or a portfolio
unless the dataset, labels, protocol, and command that reproduces it are checked
into the repository.
