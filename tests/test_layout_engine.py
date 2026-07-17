"""Tests for LabelLayoutEngine and cumulative region calculations."""

from __future__ import annotations

import pytest

from vinylsplit.labels.layout_engine import LabelLayoutEngine
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


def test_with_offset_shifts_all_boundaries() -> None:
    release = _release_with_tracks(
        (
            _track("One", 1, 100_000),
            _track("Two", 2, 200_000),
        )
    )
    layout = LabelLayoutEngine().generate(release).with_offset(30.0)

    assert layout.regions[0].start_seconds == 30.0
    assert layout.regions[0].end_seconds == 130.0
    assert layout.regions[1].start_seconds == 130.0
    assert layout.regions[1].end_seconds == 330.0
    assert layout.regions[0].duration_seconds == 100.0
    assert layout.regions[1].duration_seconds == 200.0


def test_transformed_scale_multiplies_durations() -> None:
    release = _release_with_tracks(
        (
            _track("One", 1, 100_000),
            _track("Two", 2, 100_000),
        )
    )
    layout = LabelLayoutEngine().generate(release).transformed(
        offset_seconds=10.0,
        scale=1.1,
    )

    assert layout.regions[0].start_seconds == 10.0
    assert layout.regions[0].end_seconds == pytest.approx(120.0)
    assert layout.regions[1].start_seconds == pytest.approx(120.0)
    assert layout.regions[1].end_seconds == pytest.approx(230.0)


def test_negative_offset_clamps_first_start() -> None:
    release = _release_with_tracks((_track("One", 1, 60_000),))
    layout = LabelLayoutEngine().generate(release).with_offset(-5.0)
    assert layout.regions[0].start_seconds == 0.0
    assert layout.regions[0].end_seconds == 60.0


def test_shift_from_index_zero_moves_all() -> None:
    release = _release_with_tracks(
        (
            _track("One", 1, 60_000),
            _track("Two", 2, 60_000),
            _track("Three", 3, 60_000),
        )
    )
    layout = LabelLayoutEngine().generate(release).shift_from_index(0, 10.0)

    assert [r.start_seconds for r in layout.regions] == [10.0, 70.0, 130.0]
    assert [r.duration_seconds for r in layout.regions] == [60.0, 60.0, 60.0]


def test_shift_from_index_two_keeps_track_one() -> None:
    """Move track 2: T1 stays; T2+ shift; T1 end stretches."""
    release = _release_with_tracks(
        (
            _track("One", 1, 60_000),
            _track("Two", 2, 60_000),
            _track("Three", 3, 60_000),
        )
    )
    base = LabelLayoutEngine().generate(release)
    layout = base.shift_from_index(1, 10.0)

    # T1 start fixed, end stretches to new T2 start
    assert layout.regions[0].start_seconds == 0.0
    assert layout.regions[0].end_seconds == 70.0
    assert layout.regions[0].duration_seconds == 70.0
    # T2 and T3 shift, keep duration
    assert layout.regions[1].start_seconds == 70.0
    assert layout.regions[1].end_seconds == 130.0
    assert layout.regions[2].start_seconds == 130.0
    assert layout.regions[2].end_seconds == 190.0


def test_shift_from_index_three_keeps_one_and_two() -> None:
    release = _release_with_tracks(
        (
            _track("One", 1, 60_000),
            _track("Two", 2, 60_000),
            _track("Three", 3, 60_000),
        )
    )
    layout = LabelLayoutEngine().generate(release).shift_from_index(2, 15.0)

    assert layout.regions[0].start_seconds == 0.0
    assert layout.regions[0].end_seconds == 60.0
    assert layout.regions[1].start_seconds == 60.0
    assert layout.regions[1].end_seconds == 135.0  # stretched
    assert layout.regions[2].start_seconds == 135.0
    assert layout.regions[2].end_seconds == 195.0
