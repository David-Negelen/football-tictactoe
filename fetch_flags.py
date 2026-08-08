#!/usr/bin/env python3
"""Downloads a real flag PNG per country in src/countries.py from flagcdn.com
(a free, public flag-image CDN) into static/flags/, so nationality categories
can render an actual flag image instead of relying on the OS's emoji font
for regional-indicator flags (inconsistent rendering, and doesn't cover
subdivision flags like England/Scotland/Wales at all).

flagcdn's code is usually the lowercased ISO 3166-1 alpha-2 code, except for
a handful of cases matching src/countries.py's own flag_override entries
(UK constituent countries use flagcdn's "gb-<subdivision>" convention;
Kosovo uses "xk"). Countries with no real current flag (flag_override is the
white flag "🏳️" — dissolved states/historical entities) are skipped; those
keep the emoji fallback.

Usage:
    .venv/bin/python3 fetch_flags.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import requests

from src.countries import COUNTRIES, country_flag_image_code

FLAGCDN_SIZE = "h60"  # 60px tall, small enough for a category icon
OUT_DIR = Path("static/flags")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    seen_codes: set[str] = set()
    downloaded = skipped = failed = 0

    for country in COUNTRIES:
        code = country_flag_image_code(country.name)
        if code is None:
            skipped += 1
            continue
        if code in seen_codes:
            continue  # e.g. multiple historical names sharing one current flag
        seen_codes.add(code)

        out_path = OUT_DIR / f"{code}.png"
        if out_path.exists():
            continue

        url = f"https://flagcdn.com/{FLAGCDN_SIZE}/{code}.png"
        try:
            resp = session.get(url, timeout=10)
            resp.raise_for_status()
            if not resp.content:
                raise ValueError("empty response")
        except Exception as exc:
            print(f"  FAILED {country.name} ({code}): {exc}", file=sys.stderr)
            failed += 1
            continue

        out_path.write_bytes(resp.content)
        downloaded += 1
        print(f"  {country.name:30s} -> {out_path}")
        time.sleep(0.05)

    print(f"\nDone. Downloaded: {downloaded}  Already had: {len(seen_codes) - downloaded - failed}  Failed: {failed}  No real flag (skipped): {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
