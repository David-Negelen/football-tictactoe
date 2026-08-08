# Tiki-Taka-Toe

A football-themed tic-tac-toe game: each row and column is a category (club,
nationality, position, trophy, age bracket, market-value bracket, …). To
claim a cell you name a real footballer who satisfies **both** the row and
column category — validated against a SQLite database of ~49k players —
then normal tic-tac-toe rules decide the winner.

The Flask app also bundles three smaller tools built on the same dataset:
a searchable player DB explorer (`/`), a "shared players between two clubs"
explorer (`/combos`), and a real-lineup guessing game (`/squad-guesser`).
Tiki-Taka-Toe (`/game`) is the primary product.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
make run          # http://localhost:5001, PORT env var to override
make restart       # kill whatever's on $PORT and restart
```

Or directly: `python3 app.py`. The Flask debug server (`FLASK_DEBUG=1 python3 app.py`)
is for local development only — see [Deployment](#deployment) for production.

## Data

`data/tictactoe.db` (SQLite, not checked into git — see `.gitignore`) holds
the player/club/transfer/trophy dataset the game is built on. It's populated
by the scraper/importer pipeline in `src/` (`src/scraper.py`, `src/pipeline.py`,
`src/match_importer.py`), which pulls from Transfermarkt and ESPN. See
`src/cli.py` for the import CLI, and `import_matches.py` / `update_market_values.py`
/ `update_trophies.py` for the backfill scripts.

If `data/tictactoe.db` is missing, the app still boots (an empty schema is
created automatically) but puzzle generation and search will have no players
to draw from — you'll need to run an import first.

**Data provenance note:** player, club and match data is sourced from
Transfermarkt and ESPN. Before any public deployment, confirm this use is
consistent with their current terms of service.

## Testing

```bash
pytest -v
```

Tests run against a small hand-built fixture dataset (`tests/conftest.py`),
not the real `data/tictactoe.db` — they pass with or without a real dataset
present. Coverage includes: category engine consistency (`check_player()` /
`eligible_player_ids()` / `sql_filter()` must always agree), puzzle
generation invariants, and the `/api/game/*` routes.

## Deployment

```bash
docker build -t tiki-taka-toe .
docker run -v ttt_data:/app/data -p 5001:5001 tiki-taka-toe
```

The image runs via `gunicorn` (see `Dockerfile`), not the Flask dev server.
`data/tictactoe.db` is not baked into the image (186MB, refreshed
independently of app code) — mount it as a volume, or copy it in after the
container starts. `FLASK_DEBUG` defaults to off; only set it to `1` for local
debugging, never in production.

CI (`.github/workflows/ci.yml`) runs the test suite and a Docker build check
on every push/PR to `main`.

## Project layout

```
app.py                  Flask routes (all four surfaces)
src/
  categories.py           Puzzle category engine (Club/Nationality/Position/…)
  category_config.py       Concrete category instances used by the game
  db.py                     SQLite schema + upsert helpers
  scraper.py, pipeline.py    Transfermarkt scraper/importer
  match_importer.py          ESPN lineup importer (for Squad Guesser)
templates/               Server-rendered pages (Tailwind via CDN, vanilla JS)
static/                  PWA assets (manifest, service worker, icons) — game page only
tests/                   pytest suite (fixture-based, no real data required)
```
