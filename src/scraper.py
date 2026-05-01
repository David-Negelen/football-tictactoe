from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from .config import BASE_URL
from .http import HttpClient
from .models import CareerStint, PlayerRecord, TransferRecord


@dataclass
class ParsedClubPage:
    name: str
    player_urls: list[str]


@dataclass
class ParsedLeaguePage:
    name: str
    club_urls: list[str]


class TransfermarktScraper:
    def __init__(self, http_client: Optional[HttpClient] = None) -> None:
        self._http = http_client or HttpClient()

    # ------------------------------------------------------------------ public

    @staticmethod
    def is_league_url(url: str) -> bool:
        return "/wettbewerb/" in url

    def fetch_league(self, league_url: str) -> ParsedLeaguePage:
        result = self._http.get_html(league_url)
        soup = BeautifulSoup(result.html, "html.parser")
        name = self._extract_title(soup) or league_url
        club_urls = self._extract_club_urls(soup)
        return ParsedLeaguePage(name=name, club_urls=club_urls)

    def fetch_club(self, club_url: str) -> ParsedClubPage:
        result = self._http.get_html(club_url)
        return self.parse_club_page(result.html, result.final_url)

    def fetch_player(self, player_url: str) -> PlayerRecord:
        result = self._http.get_html(player_url)
        player = self.parse_player_page(result.html, result.final_url)
        player_id = self._player_id_from_url(result.final_url)
        if player_id:
            player.transfers = self._fetch_transfers_api(player_id, result.final_url)
            player.career_stints = self._compute_career_stints(player.transfers)
        return player

    def parse_club_page(self, html: str, fallback_url: str) -> ParsedClubPage:
        soup = BeautifulSoup(html, "html.parser")
        name = self._extract_title(soup) or fallback_url
        player_urls = self._extract_player_urls(soup)
        return ParsedClubPage(name=name, player_urls=player_urls)

    def parse_player_page(self, html: str, player_url: str) -> PlayerRecord:
        soup = BeautifulSoup(html, "html.parser")
        info = self._build_info_map(soup)

        name = self._extract_title(soup) or player_url
        age = self._extract_age(info)
        nationality = self._first_value(info, {"staatsbürgerschaft", "nationality", "nationalität"})
        position = self._first_value(info, {"position", "hauptposition"})
        club_name = self._first_value(info, {"aktueller verein", "current club", "verein"})
        contract_expires = self._first_value(info, {"vertrag bis", "contract expires", "vertragsende"})
        market_value = self._first_value(info, {"marktwert", "market value"})

        # Strip image alt-text noise that sometimes ends up in nationality
        if nationality:
            nationality = nationality.strip().split("\n")[0].strip()

        return PlayerRecord(
            source_url=player_url,
            name=name,
            club_name=club_name,
            age=age,
            nationality=nationality,
            position=position,
            market_value=market_value,
            contract_expires=contract_expires,
            scraped_at=datetime.now(timezone.utc),
        )

    # --------------------------------------------------------------- internals

    def _extract_club_urls(self, soup: BeautifulSoup) -> list[str]:
        seen: set[str] = set()
        urls: list[str] = []
        for link in soup.select("a[href]"):
            href = link.get("href") or ""
            if "/verein/" not in href:
                continue
            absolute_url = urljoin(BASE_URL, href)
            parts = urlsplit(absolute_url)
            path = parts.path
            # Normalize to kader URL and strip any /saison_id/... suffix
            path = re.sub(r'/(?:startseite|kader)/verein/(\d+).*', r'/kader/verein/\1', path)
            if "/kader/verein/" not in path:
                continue
            canonical = urlunsplit(parts._replace(path=path, query="", fragment=""))
            if canonical not in seen:
                seen.add(canonical)
                urls.append(canonical)
        return urls

    def _build_info_map(self, soup: BeautifulSoup) -> dict[str, str]:
        info: dict[str, str] = {}
        # Transfermarkt info-table: alternating --regular / --bold span siblings
        for label_span in soup.select("span.info-table__content--regular"):
            key = label_span.get_text(" ", strip=True).lower().rstrip(":").strip()
            if not key:
                continue
            value_span = label_span.find_next_sibling("span")
            if value_span:
                value = value_span.get_text(" ", strip=True)
                if value:
                    info.setdefault(key, value)
        # Generic fallback: table rows with two cells
        for row in soup.select("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) >= 2:
                key = cells[0].get_text(" ", strip=True).lower().rstrip(":").strip()
                value = cells[1].get_text(" ", strip=True)
                if key and value:
                    info.setdefault(key, value)
        return info

    def _extract_age(self, info: dict[str, str]) -> Optional[int]:
        for key in ("alter", "age"):
            if key in info:
                return self._parse_int(info[key])
        # Transfermarkt: "Geb./Alter:" value is "27.03.1986 (40)"
        for key in ("geb./alter", "geburtsdatum", "date of birth", "born"):
            if key in info:
                m = re.search(r'\((\d+)\)', info[key])
                if m:
                    return int(m.group(1))
        return None

    def _first_value(self, info: dict[str, str], keys: set[str]) -> Optional[str]:
        for key in keys:
            if key in info:
                return info[key] or None
        return None

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        tag = soup.find("h1")
        if tag is None:
            tag = soup.find("title")
        if tag is None:
            return None
        return tag.get_text(" ", strip=True) or None

    def _extract_player_urls(self, soup: BeautifulSoup) -> list[str]:
        seen: set[str] = set()
        urls: list[str] = []
        for link in soup.select("a[href]"):
            href = link.get("href") or ""
            if "/profil/spieler/" in href or "/player/" in href:
                absolute_url = urljoin(BASE_URL, href)
                # Strip query params — same player can appear with different ?saison_id=
                parts = urlsplit(absolute_url)
                canonical = urlunsplit(parts._replace(query="", fragment=""))
                if canonical not in seen:
                    seen.add(canonical)
                    urls.append(canonical)
        return urls

    def _player_id_from_url(self, url: str) -> Optional[str]:
        # https://www.transfermarkt.de/name/profil/spieler/17259
        m = re.search(r'/spieler/(\d+)', url)
        return m.group(1) if m else None

    def _fetch_transfers_api(self, player_id: str, referer: str) -> list[TransferRecord]:
        api_url = f"{BASE_URL}/ceapi/transferHistory/list/{player_id}"
        try:
            data = self._http.get_json(api_url, referer=referer)
        except Exception:
            return []
        transfers = []
        for t in data.get("transfers", []):
            transfers.append(TransferRecord(
                season=t.get("season"),
                from_club=(t.get("from") or {}).get("clubName") or None,
                to_club=(t.get("to") or {}).get("clubName") or None,
                fee=t.get("fee") or None,
                transfer_date=t.get("date") or None,
                date_iso=t.get("dateUnformatted") or None,
                market_value=t.get("marketValue") or None,
                source_url=f"{BASE_URL}{t['url']}" if t.get("url") else None,
            ))
        return transfers

    def _compute_career_stints(self, transfers: list[TransferRecord]) -> list[CareerStint]:
        arrivals: dict[str, tuple[Optional[str], Optional[str]]] = {}
        stints: list[CareerStint] = []

        for t in sorted(transfers, key=lambda x: x.date_iso or ""):
            if t.from_club:
                start = arrivals.pop(t.from_club, (None, None))
                stints.append(CareerStint(
                    club_name=t.from_club,
                    start_season=start[0],
                    end_season=t.season,
                    start_date=start[1],
                    end_date=t.transfer_date,
                ))
            if t.to_club:
                arrivals[t.to_club] = (t.season, t.transfer_date)

        for club_name, (start_season, start_date) in arrivals.items():
            stints.append(CareerStint(
                club_name=club_name,
                start_season=start_season,
                end_season=None,
                start_date=start_date,
                end_date=None,
            ))

        return stints

    def _parse_int(self, value: Optional[str]) -> Optional[int]:
        if value is None:
            return None
        digits = "".join(ch for ch in value if ch.isdigit())
        return int(digits) if digits else None
