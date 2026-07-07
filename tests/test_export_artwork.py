"""Tests for album artwork helpers."""

from __future__ import annotations

from pathlib import Path

from vinylsplit.export.artwork import artwork_file_extension, write_album_folder_artwork
from vinylsplit.metadata.session import AlbumArtwork


def test_artwork_file_extension_maps_mime_type() -> None:
    assert artwork_file_extension("image/png") == ".png"
    assert artwork_file_extension("image/jpeg") == ".jpg"
    assert artwork_file_extension(None) == ".jpg"


def test_write_album_folder_artwork_writes_cover_and_folder_files(
    tmp_path: Path,
) -> None:
    artwork = AlbumArtwork(data=b"jpeg-bytes", mime_type="image/jpeg")
    cover_path = write_album_folder_artwork(tmp_path, artwork)

    assert cover_path == tmp_path / "cover.jpg"
    assert cover_path.read_bytes() == b"jpeg-bytes"
    assert (tmp_path / "folder.jpg").read_bytes() == b"jpeg-bytes"
    assert "Icon=cover.jpg" in (tmp_path / ".directory").read_text(encoding="utf-8")


def test_write_album_folder_artwork_returns_none_without_data(tmp_path: Path) -> None:
    artwork = AlbumArtwork(data=None, mime_type="image/jpeg")

    assert write_album_folder_artwork(tmp_path, artwork) is None
    assert not (tmp_path / "cover.jpg").exists()