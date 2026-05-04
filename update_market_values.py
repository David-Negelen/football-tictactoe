#!/usr/bin/env python3
"""Fetch and update market values for all active players from Transfermarkt.

Active players are identified by the '#<number> ' jersey prefix in their name.
Scrapes each player's profile page and extracts market value from the
data-header__market-value-wrapper element, then writes it to players.market_value
in the format "€5.00m" / "€500k".

Usage:
    python3 update_market_values.py [--db data/tictactoe.db] [--delay 1.5] [--limit N]
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.transfermarkt.de"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _parse_german_market_value(text: str) -> str | None:
    """Convert German market value string to '€5.00m' / '€500k' format.

    Examples:
        '4,00 Mio. €'  →  '€4.00m'
        '500 Tsd. €'   →  '€500k'
        '90 Mio. €'    →  '€90.00m'
    """
    text = text.strip()
    # Match patterns like "4,00 Mio. €" or "500 Tsd. €"
    m = re.match(r'^([\d,.]+)\s*(Mio\.|Tsd\.)\s*€$', text)
    if not m:
        return None
    raw, unit = m.group(1), m.group(2)
    try:
        value = float(raw.replace('.', '').replace(',', '.'))
    except ValueError:
        return None
    if 'Mio' in unit:
        return f"€{value:.2f}m"
    else:  # Tsd.
        return f"€{int(round(value))}k"


def _extract_market_value(html: str) -> str | None:
    """Extract current market value from Transfermarkt player profile HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # Primary: data-header__market-value-wrapper anchor
    wrapper = soup.select_one("a.data-header__market-value-wrapper")
    if wrapper:
        # The anchor may also contain a <p> tag with "Letzte Änderung: …" — remove it first.
        for extra in wrapper.select("p"):
            extra.decompose()
        waehrung = wrapper.select_one("span.waehrung")
        if waehrung:
            full_text = wrapper.get_text(" ", strip=True)
            return _parse_german_market_value(full_text)

    # Fallback: meta description contains "Marktwert: X,XX Mio. €"
    meta = soup.find("meta", attrs={"name": "description"})
    if meta:
        content = meta.get("content", "")
        m = re.search(r'Marktwert:\s*([\d,.]+\s*(?:Mio\.|Tsd\.)\s*€)', content)
        if m:
            return _parse_german_market_value(m.group(1))

    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Update market values for active players.")
    parser.add_argument("--db", default="data/tictactoe.db")
    parser.add_argument("--delay", type=float, default=1.5, help="Seconds between requests")
    parser.add_argument("--limit", type=int, default=None, help="Max players to update (for testing)")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"DB not found: {db_path}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Active players: those with the '#<number> ' jersey prefix (not retired)
    rows = conn.execute(
        "SELECT id, name, source_url FROM players WHERE name LIKE '#%' ORDER BY id"
    ).fetchall()

    if args.limit:
        rows = rows[: args.limit]

    total = len(rows)
    print(f"Found {total} active players to update.")

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    updated = 0
    skipped = 0
    last_request = 0.0

    for i, row in enumerate(rows, 1):
        # Respect rate-limit delay
        elapsed = time.monotonic() - last_request
        if elapsed < args.delay:
            time.sleep(args.delay - elapsed)

        try:
            resp = session.get(row["source_url"], timeout=20)
            resp.raise_for_status()
        except Exception as exc:
            print(f"  [{i}/{total}] ✗ fetch error — {row['name']}: {exc}", file=sys.stderr)
            skipped += 1
            last_request = time.monotonic()
            continue

        last_request = time.monotonic()
        mv = _extract_market_value(resp.text)

        if mv is None:
            print(f"  [{i}/{total}] no value  — {row['name']}")
            skipped += 1
            continue

        conn.execute(
            "UPDATE players SET market_value = ?, updated_at = datetime('now') WHERE id = ?",
            (mv, row["id"]),
        )
        conn.commit()
        updated += 1
        print(f"  [{i}/{total}] {mv:>10}  — {row['name']}")

    conn.close()
    print(f"\nDone. Updated: {updated}  Skipped/no value: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
