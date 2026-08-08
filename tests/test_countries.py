from __future__ import annotations

from src.countries import COUNTRY_BY_NAME, country_flag, parse_nationality_tokens


def test_single_nationality_parses_to_one_token() -> None:
    assert parse_nationality_tokens("Deutschland") == ["Deutschland"]


def test_dual_national_compound_splits_into_two_tokens() -> None:
    assert parse_nationality_tokens("Deutschland Türkei") == ["Deutschland", "Türkei"]


def test_multiword_country_name_is_not_fractured() -> None:
    """The historic bug this guards against: a naive str.split() would turn
    "Vereinigte Staaten" into two bogus tokens "Vereinigte" + "Staaten"."""
    assert parse_nationality_tokens("Vereinigte Staaten") == ["Vereinigte Staaten"]


def test_multiword_country_inside_a_compound_is_not_fractured() -> None:
    assert parse_nationality_tokens("Deutschland Vereinigte Staaten") == ["Deutschland", "Vereinigte Staaten"]


def test_territory_that_never_appears_standalone_still_parses() -> None:
    """"Guadeloupe" alone never appears as a sole nationality in the real
    data — only ever paired with France — so this specifically exercises
    that the parser doesn't need a token to appear standalone to know it."""
    assert parse_nationality_tokens("Frankreich Guadeloupe") == ["Frankreich", "Guadeloupe"]


def test_unknown_placeholder_value_is_unparseable() -> None:
    """"k. A." ("keine Angabe" / no data) is a real value in the dataset and
    must never be silently treated as a country."""
    assert parse_nationality_tokens("k. A.") == []


def test_completely_unknown_string_is_unparseable() -> None:
    assert parse_nationality_tokens("Nichtexistiertland") == []


def test_every_country_has_a_flag() -> None:
    for name in COUNTRY_BY_NAME:
        flag = country_flag(name)
        assert flag, f"{name} has no flag"


def test_uk_nations_use_distinct_subdivision_flags_not_the_uk_flag() -> None:
    # England/Scotland/Wales share ISO code "GB" but must not collapse to
    # the same rendered flag, or a settings/solve view showing "England"
    # and "Wales" side by side would be visually indistinguishable.
    flags = {country_flag("England"), country_flag("Schottland"), country_flag("Wales")}
    assert len(flags) == 3
