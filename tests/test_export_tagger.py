"""Tests for metadata embedding."""

from __future__ import annotations

from pathlib import Path

import pytest
from mutagen.flac import FLAC

from vinylsplit.export.models import TrackExportMetadata
from vinylsplit.export.tagger import embed_track_metadata
from vinylsplit.metadata.session import AlbumArtwork, ExportFormat


@pytest.fixture
def sample_flac(tmp_path: Path) -> Path:
    source = Path("/tmp/vinylsplit-export-test/test-track.flac")
    if not source.exists():
        pytest.skip("Sample FLAC export file is unavailable.")
    target = tmp_path / "tagged.flac"
    target.write_bytes(source.read_bytes())
    return target


def test_embed_track_metadata_writes_flac_tags(sample_flac: Path) -> None:
    metadata = TrackExportMetadata(
        artist="Pink Floyd",
        album="The Dark Side of the Moon",
        title="Speak to Me",
        track_number="01",
        genre="Album",
        date="1973-03-01",
        release_id="release-mbid-1",
        release_group_id="release-group-1",
        artist_id="artist-mbid-1",
        track_id="track-1",
    )
    artwork = AlbumArtwork(
        data=b"fake-image-bytes",
        mime_type="image/jpeg",
    )

    embed_track_metadata(
        sample_flac,
        metadata,
        export_format=ExportFormat.FLAC,
        artwork=artwork,
    )

    audio = FLAC(sample_flac)
    assert audio["artist"] == ["Pink Floyd"]
    assert audio["album"] == ["The Dark Side of the Moon"]
    assert audio["title"] == ["Speak to Me"]
    assert audio["tracknumber"] == ["01"]
    assert audio["musicbrainz_albumid"] == ["release-mbid-1"]
    assert audio["musicbrainz_trackid"] == ["track-1"]
    assert len(audio.pictures) == 1