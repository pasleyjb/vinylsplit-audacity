"""Tests for region review comparisons."""

from __future__ import annotations

from vinylsplit.labels.layout_engine import LabelLayoutEngine
from vinylsplit.labels.region_review import build_region_review_rows
from vinylsplit.metadata.models import (
    Artist,
    Medium,
    Release,
    Track,
)


def _sample_layout() -> object:
    release = Release(
        id="release-mbid-1",
        title="Test Album",
        artist=Artist(id="artist-mbid-1", name="Test Artist"),
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
                        title="Alpha",
                        position=1,
                        number="1",
                        length_ms=192_000,
                    ),
                    Track(
                        id="track-2",
                        title="Bravo",
                        position=2,
                        number="2",
                        length_ms=245_000,
                    ),
                ),
            ),
        ),
    )
    return LabelLayoutEngine().generate(release)


def test_build_region_review_rows_flags_large_boundary_differences() -> None:
    layout = _sample_layout()
    audacity_regions = [
        {"text": "01 Alpha", "start": 0.0, "end": 192.0},
        {"text": "02 Bravo", "start": 195.0, "end": 440.0},
    ]

    rows = build_region_review_rows(layout, audacity_regions)

    assert rows[0].has_warning is False
    assert rows[0].start_difference_seconds == 0.0
    assert rows[0].end_difference_seconds == 0.0
    assert rows[1].has_warning is True
    assert rows[1].start_difference_seconds == 3.0
    assert rows[1].end_difference_seconds == 3.0
    assert "start +00:03" in rows[1].difference_display
    assert "end +00:03" in rows[1].difference_display


def test_build_region_review_rows_marks_missing_regions() -> None:
    layout = _sample_layout()
    rows = build_region_review_rows(layout, [])

    assert rows[0].actual_start_seconds is None
    assert rows[0].actual_end_seconds is None
    assert rows[0].start_difference_seconds is None
    assert rows[0].has_warning is False
    assert rows[0].actual_display == "—"


def test_build_region_review_rows_warns_on_end_only_difference() -> None:
    layout = _sample_layout()
    audacity_regions = [
        {"text": "01 Alpha", "start": 0.0, "end": 195.0},
        {"text": "02 Bravo", "start": 192.0, "end": 437.0},
    ]

    rows = build_region_review_rows(layout, audacity_regions)

    assert rows[0].has_warning is True
    assert rows[0].start_difference_seconds == 0.0
    assert rows[0].end_difference_seconds == 3.0