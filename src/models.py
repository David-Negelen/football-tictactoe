from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ClubRecord:
    source_url: str
    name: str
    scraped_at: datetime


@dataclass
class TransferRecord:
    season: Optional[str]
    from_club: Optional[str]
    to_club: Optional[str]
    fee: Optional[str]
    transfer_date: Optional[str]
    date_iso: Optional[str] = None
    market_value: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class TrophyRecord:
    title: str
    count: Optional[int]
    source_url: Optional[str] = None


@dataclass
class CareerStint:
    club_name: str
    start_season: Optional[str]
    end_season: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]


@dataclass
class PlayerRecord:
    source_url: str
    name: str
    club_name: Optional[str]
    age: Optional[int]
    nationality: Optional[str]
    position: Optional[str]
    market_value: Optional[str]
    contract_expires: Optional[str]
    scraped_at: datetime
    transfers: list[TransferRecord] = field(default_factory=list)
    trophies: list[TrophyRecord] = field(default_factory=list)
    career_stints: list[CareerStint] = field(default_factory=list)


@dataclass
class ClubImportResult:
    club_url: str
    club_name: str
    discovered_players: int
    imported_players: int
    skipped_players: int
