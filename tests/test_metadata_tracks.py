"""Tests for track formatting helpers."""

from __future__ import annotations

from vinylsplit.metadata.models import Artist, Medium, Release, Track
from vinylsplit.metadata.tracks import (
    flatten_tracks,
    format_numbered_track_list,
    format_track_length,
    format_track_number,
)


def _sample_release() -> Release:
    return Release(
        id="release-mbid-1",
        title="The Dark Side of the Moon",
        artist=Artist(id="artist-mbid-1", name="Pink Floyd"),
        date="1973-03-01",
        country="GB",
        release_year="1973",
        release_type="Album",
        track_count=2,
        status="Official",
        media=(
            Medium(
                position=1,
                format="Vinyl",
                track_count=2,
                tracks=(
                    Track(
                        id="track-1",
                        title="Speak to Me",
                        position=1,
                        number="1",
                        length_ms=90000,
                    ),
                    Track(
                        id="track-2",
                        title="Breathe",
                        position=2,
                        number="2",
                        length_ms=163000,
                    ),
                ),
            ),
        ),
    )


def test_flatten_tracks() -> None:
    tracks = flatten_tracks(_sample_release())

    assert len(tracks) == 2
    assert tracks[0].title == "Speak to Me"


def test_format_track_number_zero_pads() -> None:
    track = Track(id=None, title="Test", position=3, number="3")

    assert format_track_number(track) == "03"


def test_format_track_length() -> None:
    assert format_track_length(90000) == "1:30"
    assert format_track_length(None) == "—"


def test_format_numbered_track_list() -> None:
    text = format_numbered_track_list(_sample_release())

    assert text == "01 Speak to Me\n02 Breathe"
