from __future__ import annotations

from pathlib import Path

from src.db import Database


def test_database_initialization(tmp_path: Path) -> None:
    db = Database(tmp_path / "sample.db")
    db.initialize()
    assert (tmp_path / "sample.db").exists()
