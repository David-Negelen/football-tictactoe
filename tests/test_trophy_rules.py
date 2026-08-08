from __future__ import annotations

import pytest

from src.trophy_rules import classify_trophy_title

INCLUDED_TITLES = [
    "Weltmeister",
    "UEFA Champions League-Sieger",
    "Spanischer Meister",
    "Deutscher Pokalsieger",
    "Englischer Superpokalsieger",
    "Englischer Ligapokalsieger",
    "Europa-League-Sieger",
    "Copa Libertadores-Sieger",
    "U20-Weltmeister",  # international youth NATIONAL TEAM tournament — legitimate
    "U19-Europameister",
    "Europapokal-der-Landesmeister-Sieger",  # old name for the European Cup — must not be
    # caught by the "Landesmeister" regional-title exclusion pattern (a real
    # bug found and fixed while validating this module against the full
    # real-data title list)
]

EXCLUDED_TITLES = [
    "Torschützenkönig",  # individual top-scorer award, not a team trophy
    "Fußballer des Jahres",
    "FIFA-Puskás-Preis",
    "Deutscher Zweitligameister",  # lower division
    "Italienischer Drittligameister (A)",
    "Meister Serie C2 (D)",  # boundary case: "serie c" pattern must match "Serie C2" too
    "Landespokal-Westfalen-Sieger",  # regional amateur cup
    "Landesmeister Schleswig-Holstein",  # regional title (distinct from the European Cup, above)
    "Deutscher A-Junioren-Meister",  # club-level youth competition, not international
    "Italienischer Jugendmeister (Primavera)",
    "Gewinner des Viareggio",
    "Southeast Asian Games - Zweiter",  # runner-up, not a win
    "Meister Regionalliga Nord (GER)",
]


@pytest.mark.parametrize("title", INCLUDED_TITLES)
def test_real_team_trophies_are_included(title: str) -> None:
    assert classify_trophy_title(title) is True, title


@pytest.mark.parametrize("title", EXCLUDED_TITLES)
def test_individual_youth_lower_tier_and_runner_up_titles_are_excluded(title: str) -> None:
    assert classify_trophy_title(title) is False, title
