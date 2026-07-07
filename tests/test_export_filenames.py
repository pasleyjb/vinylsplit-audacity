"""Tests for export filename generation."""

from __future__ import annotations

from vinylsplit.export.filenames import build_album_directory_name, build_track_filename
from vinylsplit.metadata.session import ExportFormat


def test_build_album_directory_name_sanitizes_invalid_characters() -> None:
    assert build_album_directory_name('No Control: Special?/Edition') == (
        "No Control SpecialEdition"
    )


def test_build_track_filename_sanitizes_invalid_characters() -> None:
    filename = build_track_filename("01", 'Speak: To Me?/', ExportFormat.FLAC)

    assert filename == "01 - Speak To Me.flac"