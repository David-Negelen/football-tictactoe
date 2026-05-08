from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

_POS_TO_ROW: dict[str, str] = {
    "G": "gk", "GK": "gk",
    "CB": "def", "CD": "def", "CD-L": "def", "CD-R": "def",
    "LB": "def", "RB": "def", "LWB": "def", "RWB": "def", "SW": "def",
    "DM": "mid", "CDM": "mid", "CM": "mid", "LM": "mid", "RM": "mid",
    "AM": "mid", "CAM": "mid", "LAM": "mid", "RAM": "mid",
    "F": "fwd", "FW": "fwd", "LF": "fwd", "RF": "fwd", "CF": "fwd",
    "SS": "fwd", "ST": "fwd", "LW": "fwd", "RW": "fwd", "S": "fwd",
}

_POS_TO_NAME: dict[str, str] = {
    "G": "Goalkeeper", "GK": "Goalkeeper",
    "CB": "Defender", "CD": "Defender", "CD-L": "Defender", "CD-R": "Defender",
    "LB": "Defender", "RB": "Defender", "LWB": "Defender", "RWB": "Defender", "SW": "Defender",
    "DM": "Midfielder", "CDM": "Midfielder", "CM": "Midfielder", "LM": "Midfielder", "RM": "Midfielder",
    "AM": "Midfielder", "CAM": "Midfielder", "LAM": "Midfielder", "RAM": "Midfielder",
    "F": "Forward", "FW": "Forward", "LF": "Forward", "RF": "Forward", "CF": "Forward",
    "SS": "Forward", "ST": "Forward", "LW": "Forward", "RW": "Forward", "S": "Forward",
}

# Competitions to import: (espn_league_id, date_ranges)
IMPORT_CONFIG: list[tuple[str, list[str]]] = [
    ("uefa.champions", [
        "20140801-20150701",
        "20150801-20160701",
        "20160801-20170701",
        "20170801-20180701",
        "20180801-20190701",
        "20190801-20200901",
        "20200901-20210701",
        "20210801-20220701",
        "20220801-20230701",
        "20230801-20240701",
    ]),
    ("fifa.world", [
        "20180601-20180716",
        "20221101-20221219",
    ]),
    ("uefa.euro", [
        "20160601-20160712",
        "20210601-20210712",
        "20240601-20240715",
    ]),
    ("uefa.europa", [
        "20160801-20170701",
        "20170801-20180701",
        "20180801-20190701",
        "20190801-20200901",
        "20200901-20210701",
        "20210801-20220701",
        "20220801-20230701",
        "20230801-20240701",
    ]),
]

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS match_lineups (
    espn_id            TEXT PRIMARY KEY,
    league_id          TEXT NOT NULL,
    competition        TEXT NOT NULL,
    date               TEXT NOT NULL,
    date_display       TEXT NOT NULL,
    venue              TEXT,
    home_name          TEXT NOT NULL,
    home_colour_primary   TEXT NOT NULL,
    home_colour_secondary TEXT NOT NULL,
    home_xi            TEXT NOT NULL,
    away_name          TEXT NOT NULL,
    away_colour_primary   TEXT NOT NULL,
    away_colour_secondary TEXT NOT NULL,
    away_xi            TEXT NOT NULL,
    imported_at        TEXT DEFAULT (datetime('now'))
)
"""


def _hex(raw: str, fallback: str = "334155") -> str:
    raw = raw.strip().lstrip("#")
    return f"#{raw.upper()}" if len(raw) == 6 else f"#{fallback.upper()}"


def _is_white(hex_color: str) -> bool:
    return hex_color.upper() in {"#FFFFFF", "#FAFAFA", "#F5F5F5", "#EEEEEE", "#E5E5E5"}


def _parse_event(event_id: str, league_id: str, session: requests.Session) -> Optional[dict]:
    try:
        r = session.get(f"{_BASE}/{league_id}/summary", params={"event": event_id}, timeout=15)
        if r.status_code != 200:
            return None
        data = r.json()
    except Exception:
        return None

    rosters = data.get("rosters", [])
    if len(rosters) != 2:
        return None

    header = data.get("header", {})
    comp_info = (header.get("competitions") or [{}])[0]
    competition = header.get("league", {}).get("name", "Unknown")

    raw_date = (comp_info.get("date") or "")[:10]
    try:
        date_display = datetime.fromisoformat(raw_date).strftime("%-d %B %Y")
    except Exception:
        date_display = raw_date

    venue_info = data.get("gameInfo", {}).get("venue", {})
    venue_parts = [venue_info.get("fullName", ""), venue_info.get("address", {}).get("city", "")]
    venue = ", ".join(p for p in venue_parts if p)

    # Team colors from competitors block
    team_colours: dict[str, tuple[str, str]] = {}
    for c in comp_info.get("competitors", []):
        t = c.get("team", {})
        primary = _hex(t.get("color", "334155"))
        secondary = _hex(t.get("alternateColor", "1e293b"))
        if _is_white(primary):
            primary, secondary = secondary, primary
        team_colours[t.get("displayName", "")] = (primary, secondary)

    teams = []
    for team_data in rosters:
        team_name = team_data.get("team", {}).get("displayName", "Unknown")
        is_home = team_data.get("homeAway", "home") == "home"

        starters = [p for p in team_data.get("roster", []) if p.get("starter")]
        if len(starters) != 11:
            return None

        xi = []
        for p in starters:
            a = p.get("athlete", {})
            pos_abbr = p.get("position", {}).get("abbreviation", "CM")
            jersey_raw = p.get("jersey", "")
            xi.append({
                "name": a.get("displayName", "Unknown"),
                "jersey": int(jersey_raw) if jersey_raw and str(jersey_raw).isdigit() else None,
                "position": _POS_TO_NAME.get(pos_abbr, "Midfielder"),
                "row": _POS_TO_ROW.get(pos_abbr, "mid"),
            })

        colours = team_colours.get(team_name, ("#dc2626", "#991b1b"))
        teams.append({"name": team_name, "is_home": is_home, "colours": colours, "xi": xi})

    teams.sort(key=lambda t: 0 if t["is_home"] else 1)
    home, away = teams[0], teams[1]

    return {
        "espn_id": str(event_id),
        "league_id": league_id,
        "competition": competition,
        "date": raw_date,
        "date_display": date_display,
        "venue": venue,
        "home_name": home["name"],
        "home_colour_primary": home["colours"][0],
        "home_colour_secondary": home["colours"][1],
        "home_xi": json.dumps(home["xi"]),
        "away_name": away["name"],
        "away_colour_primary": away["colours"][0],
        "away_colour_secondary": away["colours"][1],
        "away_xi": json.dumps(away["xi"]),
    }


def run_import(db_path: str | Path, delay: float = 0.4, verbose: bool = True) -> int:
    """
    Fetch real match lineups from the ESPN API and store them in match_lineups.
    Returns the count of newly inserted rows.
    """
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute(CREATE_TABLE)
    conn.commit()

    session = requests.Session()
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    total_new = 0

    for league_id, date_ranges in IMPORT_CONFIG:
        for date_range in date_ranges:
            if verbose:
                print(f"  [{league_id}] {date_range} … ", end="", flush=True)
            try:
                r = session.get(
                    f"{_BASE}/{league_id}/scoreboard",
                    params={"dates": date_range},
                    timeout=15,
                )
                r.raise_for_status()
                events = r.json().get("events", [])
            except Exception as exc:
                if verbose:
                    print(f"SKIP ({exc})")
                continue

            already = conn.execute(
                f"SELECT espn_id FROM match_lineups WHERE espn_id IN ({','.join('?' * len(events))})",
                [str(e.get("id", "")) for e in events],
            ).fetchall()
            seen_ids = {r["espn_id"] for r in already}

            new_in_range = [e for e in events if str(e.get("id", "")) not in seen_ids]
            if verbose:
                print(f"{len(events)} events, {len(new_in_range)} new", flush=True)
            time.sleep(delay)

            for event in new_in_range:
                event_id = str(event.get("id", ""))
                if not event_id:
                    continue

                match = _parse_event(event_id, league_id, session)
                time.sleep(delay)

                if match is None:
                    continue

                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO match_lineups
                           (espn_id, league_id, competition, date, date_display, venue,
                            home_name, home_colour_primary, home_colour_secondary, home_xi,
                            away_name, away_colour_primary, away_colour_secondary, away_xi)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            match["espn_id"], match["league_id"], match["competition"],
                            match["date"], match["date_display"], match["venue"],
                            match["home_name"], match["home_colour_primary"], match["home_colour_secondary"],
                            match["home_xi"],
                            match["away_name"], match["away_colour_primary"], match["away_colour_secondary"],
                            match["away_xi"],
                        ),
                    )
                    conn.commit()
                    total_new += 1
                    if verbose:
                        print(f"    + {match['home_name']} vs {match['away_name']} ({match['date_display']})")
                except Exception as exc:
                    if verbose:
                        print(f"    ! DB error {event_id}: {exc}")

    conn.close()
    return total_new
