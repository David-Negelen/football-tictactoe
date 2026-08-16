from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.match_importer import _hex, _is_white, _parse_event, run_import


# ─── _hex / _is_white (pure helpers) ────────────────────────────────────────

def test_hex_normalizes_a_bare_six_digit_color() -> None:
    assert _hex("dc2626") == "#DC2626"


def test_hex_strips_a_leading_hash() -> None:
    assert _hex("#dc2626") == "#DC2626"


def test_hex_falls_back_on_malformed_input() -> None:
    assert _hex("not-a-color") == "#334155"
    assert _hex("") == "#334155"


def test_hex_uses_the_given_fallback() -> None:
    assert _hex("", fallback="1e293b") == "#1E293B"


def test_is_white_matches_known_near_white_shades() -> None:
    assert _is_white("#FFFFFF") is True
    assert _is_white("#fafafa") is True  # case-insensitive


def test_is_white_rejects_non_white_colors() -> None:
    assert _is_white("#DC2626") is False


# ─── _parse_event ────────────────────────────────────────────────────────────

class _FakeResponse:
    def __init__(self, status_code: int, payload: dict) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        pass


class _FakeSession:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response
        self.requested_urls: list[str] = []

    def get(self, url: str, params=None, timeout=None) -> _FakeResponse:
        self.requested_urls.append(url)
        return self._response


def _starter(name: str, jersey: str, pos_abbr: str) -> dict:
    return {
        "starter": True,
        "athlete": {"displayName": name},
        "jersey": jersey,
        "position": {"abbreviation": pos_abbr},
    }


def _full_event_payload(home_extra=None, away_extra=None) -> dict:
    home_xi = [_starter(f"Home Player {i}", str(i), "CM") for i in range(1, 12)]
    away_xi = [_starter(f"Away Player {i}", str(i), "CB") for i in range(1, 12)]
    return {
        "header": {
            "league": {"name": "UEFA Champions League"},
            "competitions": [{"date": "2019-06-01T20:00Z"}],
        },
        "gameInfo": {"venue": {"fullName": "Wanda Metropolitano", "address": {"city": "Madrid"}}},
        "rosters": [
            {
                "team": {"displayName": "Liverpool FC"},
                "homeAway": "home",
                "roster": home_xi,
            },
            {
                "team": {"displayName": "Tottenham Hotspur"},
                "homeAway": "away",
                "roster": away_xi,
            },
        ],
    }


def test_parse_event_returns_a_well_formed_match_dict() -> None:
    session = _FakeSession(_FakeResponse(200, _full_event_payload()))
    match = _parse_event("400000001", "uefa.champions", session)

    assert match is not None
    assert match["espn_id"] == "400000001"
    assert match["competition"] == "UEFA Champions League"
    assert match["date"] == "2019-06-01"
    assert match["venue"] == "Wanda Metropolitano, Madrid"
    assert match["home_name"] == "Liverpool FC"
    assert match["away_name"] == "Tottenham Hotspur"
    home_xi = json.loads(match["home_xi"])
    assert len(home_xi) == 11
    assert home_xi[0] == {"name": "Home Player 1", "jersey": 1, "position": "Midfielder", "row": "mid"}


def test_parse_event_swaps_colours_when_the_primary_is_near_white() -> None:
    payload = _full_event_payload()
    payload["header"]["competitions"][0]["competitors"] = [
        {"team": {"displayName": "Liverpool FC", "color": "ffffff", "alternateColor": "dc2626"}},
        {"team": {"displayName": "Tottenham Hotspur", "color": "334155", "alternateColor": "1e293b"}},
    ]
    session = _FakeSession(_FakeResponse(200, payload))
    match = _parse_event("400000002", "uefa.champions", session)

    assert match is not None
    # White primary got swapped with its (non-white) alternate, matching
    # _is_white's whole purpose — a near-white shirt shouldn't be the
    # "primary" colour a UI renders as the dominant one.
    assert match["home_colour_primary"] == "#DC2626"
    assert match["home_colour_secondary"] == "#FFFFFF"


def test_parse_event_returns_none_on_non_200_status() -> None:
    session = _FakeSession(_FakeResponse(404, {}))
    assert _parse_event("400000003", "uefa.champions", session) is None


def test_parse_event_returns_none_when_roster_count_is_not_two() -> None:
    payload = _full_event_payload()
    payload["rosters"] = [payload["rosters"][0]]  # only one team
    session = _FakeSession(_FakeResponse(200, payload))
    assert _parse_event("400000004", "uefa.champions", session) is None


def test_parse_event_returns_none_when_a_team_has_fewer_than_eleven_starters() -> None:
    payload = _full_event_payload()
    payload["rosters"][0]["roster"] = payload["rosters"][0]["roster"][:10]  # only 10 starters
    session = _FakeSession(_FakeResponse(200, payload))
    assert _parse_event("400000005", "uefa.champions", session) is None


# ─── run_import ──────────────────────────────────────────────────────────────

class _FakeImportSession:
    """Stands in for requests.Session across both endpoints run_import hits
    (scoreboard listing + per-event summary) — routed by URL suffix."""

    def __init__(self, scoreboard_events: list[dict], event_payloads: dict[str, dict]) -> None:
        self.headers: dict = {}
        self._scoreboard_events = scoreboard_events
        self._event_payloads = event_payloads
        self.summary_requests: list[str] = []

    def get(self, url: str, params=None, timeout=None):
        if url.endswith("/scoreboard"):
            return _FakeResponse(200, {"events": self._scoreboard_events})
        event_id = (params or {}).get("event")
        self.summary_requests.append(event_id)
        return _FakeResponse(200, self._event_payloads[event_id])


def test_run_import_inserts_new_matches_and_skips_already_seen_ones(tmp_path: Path, monkeypatch) -> None:
    import src.match_importer as match_importer

    events = [{"id": "400000001"}]
    payloads = {"400000001": _full_event_payload()}
    fake_session = _FakeImportSession(events, payloads)
    monkeypatch.setattr(match_importer.requests, "Session", lambda: fake_session)
    # Cut the config down to exactly one league/date-range so this doesn't
    # also replay the real many-decade IMPORT_CONFIG list.
    monkeypatch.setattr(match_importer, "IMPORT_CONFIG", [("uefa.champions", ["20190101-20190101"])])

    db_path = tmp_path / "matches.db"
    inserted = run_import(db_path, delay=0, verbose=False)
    assert inserted == 1

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM match_lineups").fetchall()
        assert len(rows) == 1
        assert rows[0]["home_name"] == "Liverpool FC"
    finally:
        conn.close()

    # Running again against the same DB must not duplicate the row — the
    # already-seen espn_id should be filtered out before ever re-fetching it.
    fake_session.summary_requests.clear()
    inserted_again = run_import(db_path, delay=0, verbose=False)
    assert inserted_again == 0
    assert fake_session.summary_requests == []
