from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.db import Database
from src.models import CareerStint, PlayerRecord, TransferRecord, TrophyRecord
from src.pipeline import ImportService
from src.scraper import ParsedClubPage


class _FakeScraper:
    def __init__(self, club_page: ParsedClubPage, players_by_url: dict[str, PlayerRecord]) -> None:
        self.club_page = club_page
        self.players_by_url = players_by_url
        self.fetch_club_calls: list[str] = []
        self.fetch_player_calls: list[str] = []

    def fetch_club(self, url: str) -> ParsedClubPage:
        self.fetch_club_calls.append(url)
        return self.club_page

    def fetch_player(self, url: str) -> PlayerRecord:
        self.fetch_player_calls.append(url)
        return self.players_by_url[url]


def _player(url: str, name: str) -> PlayerRecord:
    return PlayerRecord(
        source_url=url,
        name=name,
        club_name="Testville FC",
        age=22,
        nationality="Testland",
        position="Defense - Center Back",
        market_value="€5.00m",
        contract_expires=None,
        scraped_at=datetime.now(timezone.utc),
        transfers=[TransferRecord(season="20/21", from_club=None, to_club="Testville FC", fee=None, transfer_date=None)],
        trophies=[TrophyRecord(title="Testcup", count=1)],
        career_stints=[CareerStint(club_name="Testville FC", start_season="20/21", end_season=None, start_date=None, end_date=None)],
    )


def _service(tmp_path: Path, club_page: ParsedClubPage, players_by_url: dict[str, PlayerRecord]) -> tuple[ImportService, Database]:
    database = Database(tmp_path / "pipeline.db")
    database.initialize()
    scraper = _FakeScraper(club_page, players_by_url)
    return ImportService(database=database, scraper=scraper), database


def test_import_club_imports_all_discovered_players(tmp_path: Path) -> None:
    club_page = ParsedClubPage(
        name="Testville FC",
        player_urls=["https://tm.test/player/1", "https://tm.test/player/2"],
    )
    players = {
        "https://tm.test/player/1": _player("https://tm.test/player/1", "Alan Adler"),
        "https://tm.test/player/2": _player("https://tm.test/player/2", "Bella Bauer"),
    }
    service, database = _service(tmp_path, club_page, players)

    result = service.import_club("https://tm.test/club/1", historical=False)

    assert result.club_name == "Testville FC"
    assert result.discovered_players == 2
    assert result.imported_players == 2
    assert result.skipped_players == 0
    assert result.refreshed_players == 0

    conn = database.connect()
    try:
        names = {row[0] for row in conn.execute("SELECT name FROM players")}
        assert names == {"Alan Adler", "Bella Bauer"}
        run = conn.execute("SELECT status FROM scrape_runs ORDER BY id DESC LIMIT 1").fetchone()
        assert run[0] == "success"
    finally:
        conn.close()


def test_import_club_skips_already_known_players_without_refresh(tmp_path: Path) -> None:
    club_page = ParsedClubPage(name="Testville FC", player_urls=["https://tm.test/player/1"])
    players = {"https://tm.test/player/1": _player("https://tm.test/player/1", "Alan Adler")}
    service, _database = _service(tmp_path, club_page, players)

    service.import_club("https://tm.test/club/1", historical=False)
    result = service.import_club("https://tm.test/club/1", historical=False)

    assert result.discovered_players == 1
    assert result.imported_players == 0
    assert result.skipped_players == 1
    assert result.refreshed_players == 0


def test_import_club_refreshes_existing_players_when_requested(tmp_path: Path) -> None:
    club_page = ParsedClubPage(name="Testville FC", player_urls=["https://tm.test/player/1"])
    players = {"https://tm.test/player/1": _player("https://tm.test/player/1", "Alan Adler")}
    service, _database = _service(tmp_path, club_page, players)

    service.import_club("https://tm.test/club/1", historical=False)
    result = service.import_club("https://tm.test/club/1", historical=False, refresh_existing=True)

    assert result.discovered_players == 1
    assert result.imported_players == 0
    assert result.refreshed_players == 1
    assert result.skipped_players == 0


def test_import_club_marks_the_scrape_run_failed_and_reraises_on_error(tmp_path: Path, monkeypatch) -> None:
    club_page = ParsedClubPage(name="Testville FC", player_urls=["https://tm.test/player/1"])
    players = {"https://tm.test/player/1": _player("https://tm.test/player/1", "Alan Adler")}
    service, database = _service(tmp_path, club_page, players)

    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(database, "upsert_player", _boom)

    with pytest.raises(RuntimeError, match="boom"):
        service.import_club("https://tm.test/club/1", historical=False)

    conn = database.connect()
    try:
        run = conn.execute("SELECT status, message FROM scrape_runs ORDER BY id DESC LIMIT 1").fetchone()
        assert run[0] == "failed"
        assert "boom" in run[1]
    finally:
        conn.close()
