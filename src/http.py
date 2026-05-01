from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional, TypeVar

import requests

from .config import DEFAULT_BACKOFF_BASE, DEFAULT_DELAY_SECONDS, DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT_SECONDS, USER_AGENT

T = TypeVar("T")

# Status codes worth retrying (transient server-side errors)
_RETRYABLE = {429, 500, 502, 503, 504}


@dataclass
class FetchResult:
    url: str
    html: str
    final_url: str


class HttpClient:
    def __init__(
        self,
        delay_seconds: float = DEFAULT_DELAY_SECONDS,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
    ) -> None:
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": USER_AGENT})
        self._delay_seconds = delay_seconds
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._last_request_at: Optional[float] = None

    def get_html(self, url: str) -> FetchResult:
        def _do() -> FetchResult:
            self._respect_delay()
            response = self._session.get(url, timeout=self._timeout_seconds)
            response.raise_for_status()
            self._last_request_at = time.monotonic()
            return FetchResult(url=url, html=response.text, final_url=response.url)

        return self._with_retries(_do, url)

    def get_json(self, url: str, referer: Optional[str] = None) -> dict:
        def _do() -> dict:
            self._respect_delay()
            headers = {"Accept": "application/json"}
            if referer:
                headers["Referer"] = referer
            response = self._session.get(url, headers=headers, timeout=self._timeout_seconds)
            response.raise_for_status()
            self._last_request_at = time.monotonic()
            return response.json()

        return self._with_retries(_do, url)

    def _with_retries(self, fn: Callable[[], T], url: str) -> T:
        last_exc: Exception = RuntimeError("no attempts made")
        for attempt in range(self._max_retries + 1):
            try:
                return fn()
            except requests.HTTPError as exc:
                last_exc = exc
                status = exc.response.status_code if exc.response is not None else None
                if status not in _RETRYABLE or attempt == self._max_retries:
                    raise
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
                if attempt == self._max_retries:
                    raise
            wait = self._backoff_base * (2 ** attempt)
            print(f"           ↻ retry {attempt + 1}/{self._max_retries} in {wait:.0f}s ({last_exc})")
            time.sleep(wait)
        raise last_exc  # unreachable, but satisfies type checker

    def _respect_delay(self) -> None:
        if self._last_request_at is None or self._delay_seconds <= 0:
            return
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self._delay_seconds:
            time.sleep(self._delay_seconds - elapsed)
