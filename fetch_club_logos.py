#!/usr/bin/env python3
"""Downloads a real club-crest image per club in CLUB_LOGO_QUERIES from
Wikipedia's pageimages API into static/club_logos/, and writes the
career_stints.club_name -> local filename mapping to data/club_logos.json.

Why Wikipedia and not Transfermarkt (the site the rest of this app scrapes
from): Transfermarkt's own crest CDN (tmssl.akamaized.net) returns an empty
200 response with an "AdDefend" anti-bot header to every request that isn't
a real logged-in browser session — confirmed with both plain HTTP requests
and a full headless-Chromium page load (same empty result either way), so
it isn't scrapable with this project's existing tooling. Wikipedia's REST
API has no such block and gives a directly-usable logo thumbnail per page
title.

Scoped to the ~78 clubs in category_config.LEAGUE_CATEGORIES (the four
league game modes — the highest-visibility clubs in the app) plus a couple
of extras already hardcoded in app.py's _CAT_ICONS. The other ~6,400
dynamic club categories keep the existing colored-initial fallback badge;
matching those to a correct Wikipedia page automatically isn't reliable
enough to trust without per-club review.

Usage:
    .venv/bin/python3 fetch_club_logos.py
"""

from __future__ import annotations

import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests

OUT_DIR = Path("static/club_logos")
MAPPING_PATH = Path("data/club_logos.json")

# (career_stints.club_name, Wikipedia article title to query pageimages for)
CLUB_LOGO_QUERIES: list[tuple[str, str]] = [
    # Bundesliga
    ("FC Augsburg", "FC Augsburg"),
    ("Union Berlin", "1. FC Union Berlin"),
    ("Werder Bremen", "Werder Bremen"),
    ("Bor. Dortmund", "Borussia Dortmund"),
    ("SV Elversberg", "SV Elversberg"),
    ("E. Frankfurt", "Eintracht Frankfurt"),
    ("SC Freiburg", "SC Freiburg"),
    ("Hamburger SV", "Hamburger SV"),
    ("TSG Hoffenheim", "TSG 1899 Hoffenheim"),
    ("1.FC Köln", "1. FC Köln"),
    ("RB Leipzig", "RB Leipzig"),
    ("B. Leverkusen", "Bayer 04 Leverkusen"),
    ("1.FSV Mainz 05", "1. FSV Mainz 05"),
    ("Bor. M'gladbach", "Borussia Mönchengladbach"),
    ("Bayern München", "FC Bayern Munich"),
    ("SC Paderborn", "SC Paderborn 07"),
    ("FC Schalke 04", "FC Schalke 04"),
    ("VfB Stuttgart", "VfB Stuttgart"),
    # Premier League
    ("Arsenal", "Arsenal F.C."),
    ("Aston Villa", "Aston Villa F.C."),
    ("Bournemouth", "AFC Bournemouth"),
    ("FC Brentford", "Brentford F.C."),
    ("Brighton", "Brighton & Hove Albion F.C."),
    ("Chelsea", "Chelsea F.C."),
    ("Coventry City", "Coventry City F.C."),
    ("Crystal Palace", "Crystal Palace F.C."),
    ("FC Everton", "Everton F.C."),
    ("FC Fulham", "Fulham F.C."),
    ("Hull City", "Hull City A.F.C."),
    ("Ipswich Town", "Ipswich Town F.C."),
    ("Leeds United", "Leeds United F.C."),
    ("Liverpool", "Liverpool F.C."),
    ("Man City", "Manchester City F.C."),
    ("Manchester Utd.", "Manchester United F.C."),
    ("Newcastle", "Newcastle United F.C."),
    ("Nottingham", "Nottingham Forest F.C."),
    ("AFC Sunderland", "Sunderland A.F.C."),
    ("Tottenham", "Tottenham Hotspur F.C."),
    # La Liga
    ("Dep. La Coruña", "Deportivo de La Coruña"),
    ("Alavés", "Deportivo Alavés"),
    ("Esp. Barcelona", "RCD Espanyol"),
    ("FC Barcelona", "FC Barcelona"),
    ("Athletic Bilbao", "Athletic Bilbao"),
    ("FC Elche", "Elche CF"),
    ("FC Getafe", "Getafe CF"),
    ("Atlético Madrid", "Atlético Madrid"),
    ("Real Madrid", "Real Madrid CF"),
    ("FC Málaga", "Málaga CF"),
    ("CA Osasuna", "CA Osasuna"),
    ("Real Sociedad", "Real Sociedad"),
    ("Rac. Santander", "Racing de Santander"),
    ("FC Sevilla", "Sevilla FC"),
    ("Betis Sevilla", "Real Betis"),
    ("FC Valencia", "Valencia CF"),
    ("UD Levante", "Levante UD"),
    ("Rayo Vallecano", "Rayo Vallecano"),
    ("Celta Vigo", "RC Celta de Vigo"),
    ("FC Villarreal", "Villarreal CF"),
    # Serie A
    ("Atalanta", "Atalanta B.C."),
    ("FC Bologna", "Bologna F.C. 1909"),
    ("Cagliari", "Cagliari Calcio"),
    ("Como", "Como 1907"),
    ("AC Florenz", "ACF Fiorentina"),
    ("Frosinone", "Frosinone Calcio"),
    ("Genua CFC", "Genoa C.F.C."),
    ("Lecce", "US Lecce"),
    ("Milan", "AC Milan"),
    ("Inter", "Inter Milan"),
    ("Monza", "AC Monza"),
    ("SSC Neapel", "SSC Napoli"),
    ("AC Parma", "Parma Calcio 1913"),
    ("AS Rom", "AS Roma"),
    ("Lazio Rom", "SS Lazio"),
    ("US Sassuolo", "US Sassuolo Calcio"),
    ("FC Turin", "Torino F.C."),
    ("Juventus", "Juventus F.C."),
    ("Udinese", "Udinese Calcio"),
    ("AC Venezia 1907", "Venezia F.C."),
    # A few extra well-known clubs referenced elsewhere in the app that
    # aren't part of a LEAGUE_CATEGORIES whitelist.
    ("Paris SG", "Paris Saint-Germain F.C."),
    # Fame-tiered clubs in dynamic_categories.py's CLUB_FAME_TIER_1/2/3 that
    # aren't in a current top-flight LEAGUE_CATEGORIES roster (mostly
    # well-known 2nd-division sides, plus a couple of current top-flight
    # clubs the original list above missed) — the ones actually missing a
    # logo as of the last audit, not the full tier list (most of it already
    # has a logo from an earlier run).
    ("VfL Wolfsburg", "VfL Wolfsburg"),
    ("Hertha BSC", "Hertha BSC"),
    ("1.FC Nürnberg", "1. FC Nürnberg"),
    ("Hannover 96", "Hannover 96"),
    ("1.FC K'lautern", "1. FC Kaiserslautern"),
    ("FC St. Pauli", "FC St. Pauli"),
    ("Karlsruher SC", "Karlsruher SC"),
    ("Greuther Fürth", "SpVgg Greuther Fürth"),
    ("Arm. Bielefeld", "Arminia Bielefeld"),
    ("F. Düsseldorf", "Fortuna Düsseldorf"),
    ("Holstein Kiel", "Holstein Kiel"),
    ("Darmstadt 98", "SV Darmstadt 98"),
    ("E. Braunschweig", "Eintracht Braunschweig"),
    ("VfL Bochum", "VfL Bochum"),
    ("RCD Mallorca", "RCD Mallorca"),
    ("FC Girona", "Girona FC"),
    ("Sampdoria", "U.C. Sampdoria"),
    ("Hellas Verona", "Hellas Verona F.C."),
    ("US Palermo", "Palermo F.C."),
    ("Bari", "S.S.C. Bari"),
]

USER_AGENT = "football-tictactoe-logo-fetcher/1.0 (local hobby project; contact via repo)"


def _slugify(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    return slug or "x"


def _get_with_backoff(session: requests.Session, url: str, **kwargs) -> requests.Response:
    delay = 5.0
    for attempt in range(6):
        resp = session.get(url, timeout=10, **kwargs)
        if resp.status_code != 429:
            resp.raise_for_status()
            return resp
        wait = float(resp.headers.get("Retry-After", delay))
        print(f"    (429, backing off {wait:.0f}s)", file=sys.stderr)
        time.sleep(wait)
        delay *= 2
    resp.raise_for_status()
    return resp


def fetch_logo_url(session: requests.Session, title: str) -> str | None:
    # Primary: pageprops.page_image is Wikipedia's designated representative
    # image for the page — correct even when it's non-free/fair-use (which
    # most club crests are). prop=pageimages below silently substitutes a
    # different, *freely licensed* image when the real crest is copyrighted
    # — a stadium photo, a season-performance chart, whatever's free — which
    # produced 8 wrong "logos" (CA Osasuna, Getafe, Torino, Genoa, Lazio,
    # Udinese, Sassuolo, Stuttgart all came back as stadium photos/charts)
    # before this was added. Special:FilePath serves the raw file (SVG or
    # raster) regardless of its license status.
    resp = _get_with_backoff(
        session,
        "https://en.wikipedia.org/w/api.php",
        params={"action": "query", "titles": title, "prop": "pageprops", "redirects": 1, "format": "json"},
    )
    pages = resp.json().get("query", {}).get("pages", {})
    for page in pages.values():
        filename = page.get("pageprops", {}).get("page_image")
        if filename:
            return f"https://en.wikipedia.org/wiki/Special:FilePath/{filename}"

    # Fallback: prop=pageimages / page summary thumbnail (a freely licensed
    # image, not necessarily the crest, but better than nothing).
    time.sleep(1.0)
    resp = _get_with_backoff(
        session,
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "titles": title,
            "prop": "pageimages",
            "piprop": "thumbnail",
            "pithumbsize": 200,
            "redirects": 1,
            "format": "json",
        },
    )
    pages = resp.json().get("query", {}).get("pages", {})
    for page in pages.values():
        thumb = page.get("thumbnail", {}).get("source")
        if thumb:
            return thumb

    time.sleep(1.0)
    quoted = title.replace(" ", "_")
    resp = _get_with_backoff(session, f"https://en.wikipedia.org/api/rest_v1/page/summary/{quoted}")
    data = resp.json()
    return (data.get("thumbnail") or {}).get("source") or (data.get("originalimage") or {}).get("source")


def _extension_from_url(url: str) -> str:
    path = url.split("?", 1)[0]
    suffix = Path(path).suffix.lower()
    return suffix if suffix in (".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp") else ".png"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MAPPING_PATH.parent.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    mapping: dict[str, str] = {}
    if MAPPING_PATH.exists():
        mapping = json.loads(MAPPING_PATH.read_text())

    downloaded = skipped = failed = 0

    for club_name, wiki_title in CLUB_LOGO_QUERIES:
        slug = _slugify(club_name)
        existing = next(OUT_DIR.glob(f"{slug}.*"), None)

        if existing is not None:
            # File is already on disk from an earlier (possibly interrupted)
            # run — just make sure the mapping reflects it and move on
            # without spending another request.
            if mapping.get(club_name) != existing.name:
                mapping[club_name] = existing.name
                MAPPING_PATH.write_text(json.dumps(mapping, ensure_ascii=False, indent=2, sort_keys=True))
            skipped += 1
            continue

        try:
            logo_url = fetch_logo_url(session, wiki_title)
            if not logo_url:
                raise ValueError("no pageimage found")
            time.sleep(3.0)
            img_resp = _get_with_backoff(session, logo_url)
            if not img_resp.content:
                raise ValueError("empty image response")
        except Exception as exc:
            print(f"  FAILED {club_name!r} (query {wiki_title!r}): {exc}", file=sys.stderr)
            failed += 1
            time.sleep(3.0)
            continue

        out_path = OUT_DIR / f"{slug}{_extension_from_url(logo_url)}"
        out_path.write_bytes(img_resp.content)
        mapping[club_name] = out_path.name
        # Written after every success (not just at the end) so a rate-limit
        # kill partway through doesn't lose already-downloaded progress.
        MAPPING_PATH.write_text(json.dumps(mapping, ensure_ascii=False, indent=2, sort_keys=True))
        downloaded += 1
        print(f"  {club_name:20s} <- {wiki_title:35s} -> {out_path}")
        time.sleep(3.0)

    MAPPING_PATH.write_text(json.dumps(mapping, ensure_ascii=False, indent=2, sort_keys=True))
    print(f"\nDone. Downloaded: {downloaded}  Already had: {skipped}  Failed: {failed}")
    print(f"Mapping written to {MAPPING_PATH} ({len(mapping)} clubs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
