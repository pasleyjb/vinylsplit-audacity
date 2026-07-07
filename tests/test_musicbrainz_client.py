"""Tests for the MusicBrainz API client."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from vinylsplit.musicbrainz.client import MusicBrainzClient, MusicBrainzClientConfig
from vinylsplit.musicbrainz.exceptions import (
    MusicBrainzAPIError,
    MusicBrainzNetworkError,
    MusicBrainzTimeoutError,
)

_FIXTURES = Path(__file__).parent / "fixtures"


def _response(payload: dict, *, status_code: int = 200) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload
    return response


@pytest.fixture
def client() -> MusicBrainzClient:
    config = MusicBrainzClientConfig(min_request_interval=0.0, timeout=1.0)
    return MusicBrainzClient(config=config)


def test_search_releases_returns_summaries(client: MusicBrainzClient) -> None:
    payload = json.loads((_FIXTURES / "musicbrainz_search.json").read_text())
    client._session.get = MagicMock(return_value=_response(payload))

    summaries = client.search_releases("Pink Floyd", "The Dark Side of the Moon")

    assert len(summaries) == 2
    assert summaries[0].artist == "Pink Floyd"
    client._session.get.assert_called_once()


def test_search_releases_requires_query_terms(client: MusicBrainzClient) -> None:
    with pytest.raises(ValueError, match="Enter an artist or album"):
        client.search_releases("", "")


def test_get_release_returns_complete_release(client: MusicBrainzClient) -> None:
    payload = json.loads((_FIXTURES / "musicbrainz_release.json").read_text())
    client._session.get = MagicMock(return_value=_response(payload))

    release = client.get_release("release-mbid-1")

    assert release.id == "release-mbid-1"
    assert release.track_count == 2


def test_network_error_is_raised(client: MusicBrainzClient) -> None:
    client._session.get = MagicMock(
        side_effect=requests.ConnectionError("network down"),
    )

    with pytest.raises(MusicBrainzNetworkError, match="internet connection"):
        client.search_releases("Artist", "Album")


def test_timeout_error_is_raised(client: MusicBrainzClient) -> None:
    client._session.get = MagicMock(side_effect=requests.Timeout("timed out"))

    with pytest.raises(MusicBrainzTimeoutError, match="timed out"):
        client.search_releases("Artist", "Album")


def test_api_error_on_non_200(client: MusicBrainzClient) -> None:
    client._session.get = MagicMock(return_value=_response({}, status_code=503))

    with pytest.raises(MusicBrainzAPIError, match="HTTP 503"):
        client.search_releases("Artist", "Album")
