"""Tests for export metadata and region matching."""

from __future__ import annotations

from vinylsplit.export.metadata import build_export_regions, build_track_metadata
from vinylsplit.labels.layout_engine import LabelLayoutEngine
from vinylsplit.metadata.models import (
    Artist,
    Medium,
    Release,
    Track,
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
        release_group_id="release-group-1",
        genre="Album",
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
                        length_ms=90_000,
                    ),
                    Track(
                        id="track-2",
                        title="Breathe",
                        position=2,
                        number="2",
                        length_ms=163_000,
                    ),
                ),
            ),
        ),
    )


def test_build_export_regions_uses_audacity_boundaries() -> None:
    release = _sample_release()
    layout = LabelLayoutEngine().generate(release)
    tracks = list(release.media[0].tracks)
    audacity_regions = [
        {"text": "01 Speak to Me", "start": 1.0, "end": 91.0},
        {"text": "02 Breathe", "start": 91.0, "end": 254.0},
    ]

    regions = build_export_regions(layout, tracks, audacity_regions)

    assert len(regions) == 2
    assert regions[0].start_seconds == 1.0
    assert regions[0].end_seconds == 91.0
    assert regions[1].track_id == "track-2"


def test_build_track_metadata_includes_musicbrainz_ids() -> None:
    release = _sample_release()
    layout = LabelLayoutEngine().generate(release)
    region = build_export_regions(
        layout,
        list(release.media[0].tracks),
        [{"text": "01 Speak to Me", "start": 0.0, "end": 90.0}],
    )[0]

    metadata = build_track_metadata(release, region)

    assert metadata.artist == "Pink Floyd"
    assert metadata.album == "The Dark Side of the Moon"
    assert metadata.title == "Speak to Me"
    assert metadata.track_number == "01"
    assert metadata.release_id == "release-mbid-1"
    assert metadata.release_group_id == "release-group-1"
    assert metadata.artist_id == "artist-mbid-1"
    assert metadata.track_id == "track-1"