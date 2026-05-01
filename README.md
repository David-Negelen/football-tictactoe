# Tictactoe data pipeline

This repository will hold a small Python scraper and SQLite importer for a Transfermarkt-based dataset.

## What this first implementation does

- Crawls a whitelist of clubs.
- Discovers player links from each club page.
- Fetches player pages and extracts a normalized profile plus transfer history.
- Stores clubs, players, memberships, transfers, and scrape runs in SQLite.

## Setup

Create a virtual environment and install dependencies:

```bash
/usr/bin/python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Example import:

```bash
/usr/bin/python3 -m src.cli --db data/tictactoe.db --club-url https://www.transfermarkt.de/...
```

Add one or more club URLs with `--club-url`. The importer will skip players that already exist by source URL and will update their latest snapshot.

## Notes

The scraper is intentionally conservative: it uses a small delay between requests, timeouts, and explicit parsing helpers so the site-specific selectors can be adjusted without changing the database layer.
