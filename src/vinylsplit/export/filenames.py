"""Safe export filenames for split tracks."""

from __future__ import annotations

import re

from vinylsplit.metadata.session import ExportFormat

_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WHITESPACE = re.compile(r"\s+")


def build_album_directory_name(album_title: str) -> str:
    """Return a filesystem-safe directory name for one album."""
    return _sanitize_filename_stem(album_title)


def build_track_filename(
    track_number: str,
    title: str,
    export_format: ExportFormat,
) -> str:
    """Return a filesystem-safe export filename for one track."""
    stem = f"{track_number} - {title}"
    safe_stem = _sanitize_filename_stem(stem)
    return f"{safe_stem}.{export_format.value}"


def _sanitize_filename_stem(value: str) -> str:
    cleaned = _INVALID_FILENAME_CHARS.sub("", value.strip())
    cleaned = _WHITESPACE.sub(" ", cleaned)
    return cleaned or "track"