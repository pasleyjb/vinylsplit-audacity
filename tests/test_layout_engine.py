"""Tests for LabelLayoutEngine and cumulative region calculations."""

from __future__ import annotations

from vinylsplit.labels.layout_engine import LabelLayoutEngine
from vinylsplit.labels.time_format import format_position, format_region_range
from vinylsplit.metadata.models import (
    Artist,
    Medium,
    Release,
    Track,
)


def _release_with_tracks(tracks: tuple[Track, ...]) -> Release:
    return Release(
        id="release-mbid-1",
        title="Test Album",
        artist=Artist(id="artist-mbid-1", name="Test Artist"),
        date="1973-03-01",
        country="GB",
        release_year="1973",
        release_type="Album",
        track_count=len(tracks),
        status="Official",
        media=(
            Medium(
                position=1,
                format="Vinyl",
                track_count=len(tracks),
                tracks=tracks,
            ),
        ),
    )


def _track(title: str, position: int, length_ms: int | None) -> Track:
    return Track(
        id=f"track-{position}",
        title=title,
        position=position,
        number=str(position),
        length_ms=length_ms,
    )


def test_generate_creates_contiguous_regions_from_cumulative_durations() -> None:
    release = _release_with_tracks(
        (
            _track("One", 1, 192_000),
            _track("Two", 2, 245_000),
            _track("Three", 3, 178_000),
            _track("Four", 4, 311_000),
        )
    )

    layout = LabelLayoutEngine().generate(release)

    assert layout.track_count == 4
    assert layout.total_duration_seconds == 926.0
    assert layout.regions[0].start_seconds == 0.0
    assert layout.regions[0].end_seconds == 192.0
    assert layout.regions[1].start_seconds == 192.0
    assert layout.regions[1].end_seconds == 437.0
    assert layout.regions[2].start_seconds == 437.0
    assert layout.regions[2].end_seconds == 615.0
    assert layout.regions[3].start_seconds == 615.0
    assert layout.regions[3].end_seconds == 926.0


def test_region_label_text_uses_numbered_track_lines() -> None:
    release = _release_with_tracks((_track("Speak to Me", 1, 90_000),))

    layout = LabelLayoutEngine().generate(release)

    assert layout.regions[0].label_text == "01 Speak to Me"
    assert layout.regions[0].track_number == "01"
    assert layout.regions[0].title == "Speak to Me"


def test_unknown_track_duration_contributes_zero_seconds() -> None:
    release = _release_with_tracks(
        (
            _track("Known", 1, 60_000),
            _track("Unknown", 2, None),
        )
    )

    layout = LabelLayoutEngine().generate(release)

    assert layout.regions[0].end_seconds == 60.0
    assert layout.regions[1].start_seconds == 60.0
    assert layout.regions[1].end_seconds == 60.0


def test_region_range_formatting_matches_example_durations() -> None:
    release = _release_with_tracks(
        (
            _track("One", 1, 192_000),
            _track("Two", 2, 245_000),
            _track("Three", 3, 178_000),
            _track("Four", 4, 311_000),
        )
    )
    layout = LabelLayoutEngine().generate(release)

    assert format_position(layout.regions[0].start_seconds) == "00:00"
    assert format_position(layout.regions[0].end_seconds) == "03:12"
    assert format_region_range(
        layout.regions[1].start_seconds,
        layout.regions[1].end_seconds,
    ) == "03:12 → 07:17"
    assert format_region_range(
        layout.regions[3].start_seconds,
        layout.regions[3].end_seconds,
    ) == "10:15 → 15:26"