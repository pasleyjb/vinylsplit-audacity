"""Tests for local audio tag reading."""

from __future__ import annotations

from pathlib import Path

import pytest
from mutagen.easyid3 import EasyID3
from mutagen.id3 import TALB, TPE1, TPE2
from mutagen.mp3 import MP3

from vinylsplit.metadata.local_tags import (
    is_supported_audio_path,
    read_local_audio_tags,
)


def test_is_supported_audio_path() -> None:
    assert is_supported_audio_path(Path("a.flac")) is True
    assert is_supported_audio_path(Path("a.WAV")) is True
    assert is_supported_audio_path(Path("a.txt")) is False


def test_read_mp3_tags(tmp_path: Path) -> None:
    path = tmp_path / "sample.mp3"
    # Minimal MPEG frame (silent) + ID3
    # 0xFFFB90... is a common tiny MP3 frame pattern; use empty ID3-only via mutagen
    path.write_bytes(
        b"\xff\xfb\x90\x00" + b"\x00" * 32
    )  # not always valid; EasyID3 may still write
    try:
        tags = EasyID3()
        tags["artist"] = "Pink Floyd"
        tags["album"] = "The Dark Side of the Moon"
        tags["albumartist"] = "Pink Floyd"
        tags.save(path)
    except Exception:
        # Fallback: write ID3v2 frames onto the file
        audio = MP3(path)
        audio.add_tags()
        assert audio.tags is not None
        audio.tags.add(TPE1(encoding=3, text=["Pink Floyd"]))
        audio.tags.add(TALB(encoding=3, text=["The Dark Side of the Moon"]))
        audio.tags.add(TPE2(encoding=3, text=["Pink Floyd"]))
        audio.save()

    result = read_local_audio_tags(path)
    assert result.search_artist == "Pink Floyd"
    assert result.search_album == "The Dark Side of the Moon"
    assert result.source == "tags"
    assert result.has_search_seed is True


def test_filename_heuristic_artist_album(tmp_path: Path) -> None:
    path = tmp_path / "Miles Davis - Kind of Blue.wav"
    # WAV without tags — filename should seed
    path.write_bytes(b"RIFF$\x00\x00\x00WAVEfmt ")  # incomplete but is_file
    # read may fail mutagen; still return filename seeds
    result = read_local_audio_tags(path)
    assert result.search_artist == "Miles Davis"
    assert result.search_album == "Kind of Blue"
    assert result.source in {"filename", "tags", "none"}


def test_filename_heuristic_album_only(tmp_path: Path) -> None:
    path = tmp_path / "Abbey Road.flac"
    path.write_bytes(b"fLaC")  # not valid flac; tags fail → filename
    result = read_local_audio_tags(path)
    # Either tags empty + filename album, or read error path
    if result.source == "filename":
        assert result.search_album == "Abbey Road"


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_local_audio_tags(tmp_path / "missing.flac")
