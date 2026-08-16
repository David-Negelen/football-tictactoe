from __future__ import annotations

from src.famous_matches import FAMOUS_MATCHES, get_random_match

# The fields /api/squad-guesser/game (app.py) reads straight off whatever
# get_random_match() returns, with no validation of its own — a malformed
# entry here would surface as a KeyError in production, not a clean error.
_REQUIRED_MATCH_KEYS = {"id", "competition", "date", "venue", "home", "away"}
_REQUIRED_TEAM_KEYS = {"name", "colour_primary", "colour_secondary", "xi"}


def test_get_random_match_returns_one_of_the_famous_matches() -> None:
    ids = {m["id"] for m in FAMOUS_MATCHES}
    for _ in range(20):
        assert get_random_match()["id"] in ids


def test_every_famous_match_has_the_shape_the_route_relies_on() -> None:
    assert FAMOUS_MATCHES, "fixture data must not be empty"
    seen_ids = set()
    for match in FAMOUS_MATCHES:
        assert _REQUIRED_MATCH_KEYS <= match.keys(), match.get("id")
        assert match["id"] not in seen_ids, f"duplicate match id: {match['id']}"
        seen_ids.add(match["id"])

        for side in ("home", "away"):
            team = match[side]
            assert _REQUIRED_TEAM_KEYS <= team.keys(), f"{match['id']}/{side}"
            assert team["xi"], f"{match['id']}/{side} has an empty starting XI"
            for player in team["xi"]:
                assert player.get("name"), f"{match['id']}/{side} has a player with no name"
