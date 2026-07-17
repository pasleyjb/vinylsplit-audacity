"""Tests for Audacity import helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from vinylsplit.audacity.import_audio import (
    import_audio_file,
    seed_queries_from_track_names,
)


def test_import_audio_file_sends_import2(tmp_path: Path) -> None:
    path = tmp_path / "side-a.wav"
    path.write_bytes(b"RIFF")
    client = MagicMock()
    import_audio_file(client, path)
    client.execute.assert_called_once()
    cmd = client.execute.call_args[0][0]
    assert cmd.startswith("Import2: Filename=")
    assert "side-a.wav" in cmd


def test_import_missing_file_raises(tmp_path: Path) -> None:
    client = MagicMock()
    with pytest.raises(FileNotFoundError):
        import_audio_file(client, tmp_path / "nope.wav")
    client.execute.assert_not_called()


def test_seed_queries_from_track_names_split() -> None:
    artist, album = seed_queries_from_track_names(["Pink Floyd - Dark Side"])
    assert artist == "Pink Floyd"
    assert album == "Dark Side"


def test_seed_queries_from_track_names_album_only() -> None:
    artist, album = seed_queries_from_track_names(["Vinyl Capture Side A"])
    assert artist == ""
    assert album == "Vinyl Capture Side A"


def test_seed_queries_empty() -> None:
    assert seed_queries_from_track_names([]) == ("", "")
