from __future__ import annotations

import pytest

from src.trophy_rules import classify_trophy_title

INCLUDED_TITLES = [
    "Weltmeister",
    "UEFA Champions League-Sieger",
    "Spanischer Meister",
    "Deutscher Pokalsieger",
    "Europa-League-Sieger",
    "Conference League-Sieger",
    "Copa Libertadores-Sieger",
    "Afrikameister",
    "AFC-Champions-League-Sieger",
    "U20-Weltmeister",  # international youth NATIONAL TEAM tournament — legitimate
    "U19-Europameister",
    "Europapokal-der-Landesmeister-Sieger",  # old name for the European Cup — must not be
    # caught by the "Landesmeister" regional-title exclusion pattern (a real
    # bug found and fixed while validating this module against the full
    # real-data title list)
    # England is a deliberate exception to the Super Cup / League Cup
    # exclusion below — the Community Shield and the League Cup (Carabao/
    # EFL Cup) are both genuinely recognizable English silverware, not just
    # domestic trivia the way most countries' equivalents are.
    "Englischer Superpokalsieger",
    "Englischer Ligapokalsieger",
]

EXCLUDED_TITLES = [
    "Torschützenkönig",  # individual top-scorer award, not a team trophy
    "Fußballer des Jahres",
    "FIFA-Puskás-Preis",
    "Gewinner Ballon d'Or",  # individual award, not a team trophy
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
    # A domestic Super Cup is a single exhibition match, not a competition
    # — every country's has the same low-prestige reputation (England's
    # Community Shield is the one deliberate exception, see INCLUDED_TITLES
    # above).
    "Deutscher Superpokalsieger",
    "Spanischer Superpokalsieger",
    # A League Cup is real silverware, but a clear notch below the national
    # cup everywhere the two coexist — only the one "major cup" per country
    # is kept (England's is again the one exception).
    "Deutscher Ligapokalsieger",
    # Second-tier continental club competitions — each confederation's
    # Europa-League-equivalent, not its Champions-League-equivalent (which
    # *is* kept, e.g. AFC-Champions-League-Sieger above).
    "Copa Sudamericana-Sieger",
    "AFC Cup-Sieger",
    "CONCACAF League-Sieger",
    "CAF-Confederation-Cup-Sieger",
    # Nations Leagues and regional multi-sport games are a tier below the
    # actual continental championship / the Olympics.
    "Sieger UEFA Nations League",
    "Asian Games Goldmedaille",
]


@pytest.mark.parametrize("title", INCLUDED_TITLES)
def test_real_team_trophies_are_included(title: str) -> None:
    assert classify_trophy_title(title) is True, title


@pytest.mark.parametrize("title", EXCLUDED_TITLES)
def test_individual_youth_lower_tier_and_runner_up_titles_are_excluded(title: str) -> None:
    assert classify_trophy_title(title) is False, title
