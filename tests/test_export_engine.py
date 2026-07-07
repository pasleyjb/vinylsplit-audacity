"""Tests for album export orchestration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from vinylsplit.export.engine import ExportEngine
from vinylsplit.export.models import ExportSettings, TrackExportResult
from vinylsplit.metadata.models import (
    Artist,
    Medium,
    Release,
    Track,
)
from vinylsplit.metadata.session import AlbumArtwork, ExportFormat


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


def _audacity_regions_payload() -> str:
    return (
        '[["track-1", [[0.0, 30.0, "01 Alpha"]]]]\n'
        "BatchCommand finished: OK\n\n"
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


def test_export_album_writes_tracks_and_artwork_to_album_subdirectory(
    tmp_path: Path,
) -> None:
    client = MagicMock()
    client.is_connected.return_value = True
    client.execute.return_value = _audacity_regions_payload()

    artwork = AlbumArtwork(data=b"cover-image", mime_type="image/jpeg")

    def fake_export(_client, region, output_path: Path) -> TrackExportResult:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"audio")
        return TrackExportResult(
            label_text=region.label_text,
            output_path=output_path,
            success=True,
            message="ok",
        )

    with (
        patch(
            "vinylsplit.export.engine.export_region_to_file",
            side_effect=fake_export,
        ),
        patch("vinylsplit.export.engine.embed_track_metadata"),
    ):
        result = ExportEngine(client).export_album(
            _sample_release(),
            settings=ExportSettings(
                output_directory=tmp_path,
                export_format=ExportFormat.FLAC,
            ),
            artwork=artwork,
            fetch_artwork_if_missing=False,
        )

    album_directory = tmp_path / "Test Album"
    assert result.success is True
    assert result.output_directory == album_directory
    assert (album_directory / "01 - Alpha.flac").exists()
    assert (album_directory / "cover.jpg").read_bytes() == b"cover-image"
    assert (album_directory / "folder.jpg").exists()
    assert "Test Album" in result.message