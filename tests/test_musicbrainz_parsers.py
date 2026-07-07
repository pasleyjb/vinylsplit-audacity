"""Tests for MusicBrainz response parsers."""

from __future__ import annotations

import json
from pathlib import Path

from vinylsplit.metadata.models import Release, ReleaseSummary
from vinylsplit.musicbrainz.parsers import parse_release, parse_release_summaries

_FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def test_parse_release_summaries() -> None:
    summaries = parse_release_summaries(_load_fixture("musicbrainz_search.json"))

    assert len(summaries) == 2
    assert summaries[0] == ReleaseSummary(
        id="release-mbid-1",
        artist="Pink Floyd",
        album="The Dark Side of the Moon",
        release_year="1973",
        country="GB",
        track_count=10,
        release_type="Album",
    )
    assert summaries[1].release_type == "Album (Live)"


def test_parse_release() -> None:
    release = parse_release(_load_fixture("musicbrainz_release.json"))

    assert isinstance(release, Release)
    assert release.id == "release-mbid-1"
    assert release.artist_name == "Pink Floyd"
    assert release.track_count == 2
    assert len(release.media) == 1
    assert release.media[0].tracks[0].title == "Speak to Me"
    assert release.media[0].tracks[0].length_ms == 90000
