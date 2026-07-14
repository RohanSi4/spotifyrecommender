# Signal

Signal helps you get from one song you love to music worth playing next.

**Live app:** [signal-recommender.vercel.app](https://signal-recommender.vercel.app)

## What it does now

The production app in [`web/`](web/) uses the live Spotify catalog instead of a tiny synthetic song list.

- Search any real Spotify song without logging in.
- Explore releases from the seed artist and artists connected through collaborations.
- Open every result directly in Spotify with real album art and metadata.
- Connect an invited Spotify account to find deeper cuts from artists already in your rotation.
- See a real reason for every pick instead of a made-up match percentage.

Spotify no longer gives most new developer apps access to Recommendations, Audio Features, Audio Analysis, or Related Artists. Signal works with the endpoints that are actually available in 2026 and is clear about what each connection means. Spotify also limits development-mode account access to five invited users, while the public search experience works for everyone.

## Web app

```bash
cd web
npm install
cp .env.example .env.local
npm run dev
```

See [`web/README.md`](web/README.md) for Spotify callback setup, environment variables, and deployment details.

Verify the full web app with:

```bash
cd web
npm run check
```

## Original Python recommender

The repository still includes the original offline Python ranking work as a reference implementation. It turns track features or a mood profile into a normalized centroid, ranks a candidate catalog by weighted distance, and explains the closest dimensions. Its 72-track fixture is synthetic and exists for deterministic regression testing, not as a claim about real listener satisfaction.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
ruff check .
python evaluate.py --json
```

Main Python files:

- `recommender.py`: ranking engine, validation, and the legacy Spotify adapter
- `demo_data.py`: reproducible synthetic fixture
- `evaluate.py`: hit-rate, reciprocal-rank, and local latency checks
- `gui_streamlit.py`: original Streamlit interface
- `tests/`: regression and API-boundary coverage

The web app and Python prototype are intentionally separate. The web app is the current portfolio product. The Python code preserves the path that led there.
