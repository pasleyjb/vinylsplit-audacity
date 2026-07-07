"""Tests for album export orchestration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from vinylsplit.export.engine import ExportEngine
from vinylsplit.export.models import ExportSettings
from vinylsplit.metadata.models import (
    Artist,
    Medium,
    Release,
    Track,
)
from vinylsplit.metadata.session import ExportFormat


def _sample_release() -> Release:
    return Release(
        id="release-mbid-1",
        title="Test Album",
        artist=Artist(id="artist-mbid-1", name="Test Artist"),
        date="1973-03-01",
        country="GB",
        release_year="1973",
        release_type="Album",
        track_count=1,
        status="Official",
        release_group_id="release-group-1",
        genre="Album",
        media=(
            Medium(
                position=1,
                format="Vinyl",
                track_count=1,
                tracks=(
                    Track(
                        id="track-1",
                        title="Alpha",
                        position=1,
                        number="1",
                        length_ms=30_000,
                    ),
                ),
            ),
        ),
    )


def test_export_album_reports_missing_regions(tmp_path: Path) -> None:
    client = MagicMock()
    client.is_connected.return_value = True
    client.execute.return_value = '[  ]\nBatchCommand finished: OK\n\n'

    result = ExportEngine(client).export_album(
        _sample_release(),
        settings=ExportSettings(
            output_directory=tmp_path,
            export_format=ExportFormat.FLAC,
        ),
        fetch_artwork_if_missing=False,
    )

    assert result.success is False
    assert "No Audacity regions matched" in result.message