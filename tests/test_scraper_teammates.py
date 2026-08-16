from __future__ import annotations

from src.http import FetchResult
from src.models import TeammateRecord
from src.scraper import TransfermarktScraper


def _row_html(name: str, player_id: str, shared_games: int) -> str:
    return f"""
    <tr>
      <td class="">
        <table class="inline-table">
          <tr>
            <td rowspan="2"><img title="{name}"></td>
            <td class="hauptlink"><a href="/{name.lower().replace(' ', '-')}/profil/spieler/{player_id}" title="{name}">{name}</a></td>
          </tr>
          <tr><td>Mittelfeld</td></tr>
        </table>
      </td>
      <td class="zentriert hauptlink"><a href="#">{shared_games}</a></td>
      <td class="zentriert">2</td>
      <td class="zentriert">2,27</td>
      <td class="zentriert">33</td>
      <td class="zentriert">48.364</td>
    </tr>
    """


def _page_html(rows: list[str], pagination_links: list[str] | None = None) -> str:
    pager = ""
    if pagination_links:
        links = "".join(
            f'<li><a class="tm-pagination__link" href="{href}">{i + 1}</a></li>'
            for i, href in enumerate(pagination_links)
        )
        pager = f'<div class="pager"><ul class="tm-pagination">{links}</ul></div>'
    return f"""
    <html><body>
      <table class="items">
        <thead><tr><th>Gemeinsam mit ...</th><th>Spiele</th><th>Teams</th><th>PPS</th><th>Tore</th><th>Minuten</th></tr></thead>
        <tbody>{"".join(rows)}</tbody>
      </table>
      {pager}
    </body></html>
    """


class _FakeHttpClient:
    """Serves pre-built HTML per URL, no network — mirrors HttpClient's
    get_html(url) -> FetchResult interface without touching anything real."""

    def __init__(self, pages_by_url: dict[str, str]) -> None:
        self._pages = pages_by_url
        self.requested_urls: list[str] = []

    def get_html(self, url: str) -> FetchResult:
        self.requested_urls.append(url)
        if url not in self._pages:
            raise AssertionError(f"unexpected URL requested: {url}")
        return FetchResult(url=url, html=self._pages[url], final_url=url)


def test_extract_shared_matches_page_parses_name_url_and_shared_games() -> None:
    scraper = TransfermarktScraper()
    from bs4 import BeautifulSoup

    html = _page_html([_row_html("Sergio Busquets", "65230", 651)])
    soup = BeautifulSoup(html, "html.parser")
    teammates = scraper._extract_shared_matches_page(soup)

    assert teammates == [
        TeammateRecord(
            teammate_source_url="https://www.transfermarkt.de/sergio-busquets/profil/spieler/65230",
            teammate_name="Sergio Busquets",
            shared_games=651,
        )
    ]


def test_extract_shared_matches_page_returns_empty_list_when_no_table() -> None:
    scraper = TransfermarktScraper()
    from bs4 import BeautifulSoup

    soup = BeautifulSoup("<html><body>no table here</body></html>", "html.parser")
    assert scraper._extract_shared_matches_page(soup) == []


def test_extract_last_page_reads_highest_pagination_link() -> None:
    scraper = TransfermarktScraper()
    from bs4 import BeautifulSoup

    html = _page_html(
        [_row_html("Player One", "1", 10)],
        pagination_links=["/x/gemeinsameSpiele/spieler/1", "/x/gemeinsameSpiele/spieler/1/page/2", "/x/gemeinsameSpiele/spieler/1/page/3"],
    )
    soup = BeautifulSoup(html, "html.parser")
    assert scraper._extract_last_page(soup) == 3


def test_extract_last_page_defaults_to_one_without_a_pager() -> None:
    scraper = TransfermarktScraper()
    from bs4 import BeautifulSoup

    html = _page_html([_row_html("Player One", "1", 10)])
    soup = BeautifulSoup(html, "html.parser")
    assert scraper._extract_last_page(soup) == 1


def test_fetch_shared_matches_walks_every_page(monkeypatch) -> None:
    base = "https://www.transfermarkt.de/anchor/gemeinsameSpiele/spieler/1"
    page1_html = _page_html(
        [_row_html("Player A", "10", 100), _row_html("Player B", "11", 90)],
        pagination_links=[base, f"{base}/page/2"],
    )
    page2_html = _page_html([_row_html("Player C", "12", 5)])
    fake_client = _FakeHttpClient({base: page1_html, f"{base}/page/2": page2_html})

    scraper = TransfermarktScraper(http_client=fake_client)
    teammates = scraper.fetch_shared_matches("https://www.transfermarkt.de/anchor/profil/spieler/1")

    assert [t.teammate_name for t in teammates] == ["Player A", "Player B", "Player C"]
    assert fake_client.requested_urls == [base, f"{base}/page/2"]


def test_fetch_shared_matches_stops_at_a_single_page_when_there_is_no_pager() -> None:
    base = "https://www.transfermarkt.de/anchor/gemeinsameSpiele/spieler/1"
    fake_client = _FakeHttpClient({base: _page_html([_row_html("Solo Teammate", "20", 3)])})

    scraper = TransfermarktScraper(http_client=fake_client)
    teammates = scraper.fetch_shared_matches("https://www.transfermarkt.de/anchor/profil/spieler/1")

    assert [t.teammate_name for t in teammates] == ["Solo Teammate"]
    assert fake_client.requested_urls == [base]


def test_fetch_shared_matches_returns_empty_list_on_initial_fetch_failure() -> None:
    class _FailingClient:
        def get_html(self, url: str) -> FetchResult:
            raise RuntimeError("network down")

    scraper = TransfermarktScraper(http_client=_FailingClient())
    assert scraper.fetch_shared_matches("https://www.transfermarkt.de/anchor/profil/spieler/1") == []
