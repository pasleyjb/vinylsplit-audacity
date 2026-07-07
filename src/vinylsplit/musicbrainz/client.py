"""MusicBrainz web service client."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote

import requests

from vinylsplit import __version__
from vinylsplit.metadata.models import Release, ReleaseSummary
from vinylsplit.musicbrainz.exceptions import (
    MusicBrainzAPIError,
    MusicBrainzNetworkError,
    MusicBrainzTimeoutError,
)
from vinylsplit.musicbrainz.parsers import parse_release, parse_release_summaries

_DEFAULT_BASE_URL = "https://musicbrainz.org/ws/2"
_DEFAULT_USER_AGENT = (
    f"vinylsplit-audacity/{__version__} "
    "(https://github.com/vinylsplit/vinylsplit-audacity)"
)


@dataclass
class MusicBrainzClientConfig:
    """Configuration for :class:`MusicBrainzClient`."""

    base_url: str = _DEFAULT_BASE_URL
    user_agent: str = _DEFAULT_USER_AGENT
    timeout: float = 10.0
    min_request_interval: float = 1.0
    search_limit: int = 25


@dataclass
class MusicBrainzClient:
    """Search and retrieve release metadata from MusicBrainz.

    The client enforces MusicBrainz rate limits and surfaces network failures
    as typed exceptions suitable for UI messaging.
    """

    config: MusicBrainzClientConfig = field(default_factory=MusicBrainzClientConfig)
    _session: requests.Session = field(default_factory=requests.Session, repr=False)
    _last_request_at: float = field(default=0.0, init=False, repr=False)
    _logger: logging.Logger = field(
        default_factory=lambda: logging.getLogger(__name__),
        init=False,
        repr=False,
    )

    def search_releases(self, artist: str, album: str) -> list[ReleaseSummary]:
        """Search for releases matching *artist* and *album*.

        Args:
            artist: Artist name query.
            album: Album title query.

        Returns:
            Matching release summaries, which may be empty when nothing is found.

        Raises:
            MusicBrainzError: On network, timeout, or API failures.
            ValueError: When both query terms are empty.
        """
        artist = artist.strip()
        album = album.strip()
        if not artist and not album:
            msg = "Enter an artist or album name to search."
            raise ValueError(msg)

        query = _build_search_query(artist=artist, album=album)
        params = {
            "query": query,
            "fmt": "json",
            "limit": str(self.config.search_limit),
        }
        payload = self._get("release/", params=params)
        summaries = parse_release_summaries(payload)
        self._logger.info(
            "MusicBrainz search returned %d release(s) for query=%r",
            len(summaries),
            query,
        )
        return summaries

    def get_release(self, release_id: str) -> Release:
        """Fetch a complete release, including media and recordings.

        Args:
            release_id: MusicBrainz release MBID.

        Returns:
            Parsed :class:`~vinylsplit.metadata.models.Release`.
        """
        release_id = release_id.strip()
        if not release_id:
            msg = "Release id is required."
            raise ValueError(msg)

        params = {
            "inc": "artist-credits+labels+recordings+media+release-groups",
            "fmt": "json",
        }
        payload = self._get(f"release/{quote(release_id)}", params=params)
        release = parse_release(payload)
        self._logger.info(
            "Loaded MusicBrainz release %s (%s)", release.id, release.title
        )
        return release

    def _get(self, path: str, *, params: dict[str, str]) -> dict[str, Any]:
        """Issue a rate-limited GET request."""
        self._throttle()
        url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"

        try:
            response = self._session.get(
                url,
                params=params,
                headers={"User-Agent": self.config.user_agent},
                timeout=self.config.timeout,
            )
        except requests.Timeout as exc:
            msg = (
                f"MusicBrainz request timed out after {self.config.timeout:g} seconds."
            )
            raise MusicBrainzTimeoutError(msg) from exc
        except requests.ConnectionError as exc:
            msg = "Unable to reach MusicBrainz. Check your internet connection."
            raise MusicBrainzNetworkError(msg) from exc
        except requests.RequestException as exc:
            msg = f"MusicBrainz request failed: {exc}"
            raise MusicBrainzNetworkError(msg) from exc

        if response.status_code != 200:
            msg = f"MusicBrainz returned HTTP {response.status_code}."
            raise MusicBrainzAPIError(msg, status_code=response.status_code)

        try:
            payload = response.json()
        except ValueError as exc:
            msg = "MusicBrainz returned an invalid JSON response."
            raise MusicBrainzAPIError(msg) from exc

        if not isinstance(payload, dict):
            msg = "MusicBrainz returned an unexpected response shape."
            raise MusicBrainzAPIError(msg)

        return payload

    def _throttle(self) -> None:
        """Respect MusicBrainz's one-request-per-second policy."""
        elapsed = time.monotonic() - self._last_request_at
        remaining = self.config.min_request_interval - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_request_at = time.monotonic()


def _build_search_query(*, artist: str, album: str) -> str:
    """Build a Lucene query for the MusicBrainz search endpoint."""
    terms: list[str] = []
    if artist:
        terms.append(f'artist:"{_escape_query(artist)}"')
    if album:
        terms.append(f'release:"{_escape_query(album)}"')
    return " AND ".join(terms)


def _escape_query(value: str) -> str:
    """Escape characters that break Lucene query syntax."""
    return value.replace("\\", "\\\\").replace('"', '\\"')
