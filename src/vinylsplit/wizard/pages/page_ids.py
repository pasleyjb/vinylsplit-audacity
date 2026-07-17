"""Stable identifiers for wizard pages."""

from __future__ import annotations

from enum import IntEnum


class PageId(IntEnum):
    """Streamlined wizard page identifiers (0 → 3).

    Flow:
      Open album → Find release → Align & hand off → Export
    """

    OPEN = 0
    RELEASE = 1
    ALIGN = 2
    EXPORT = 3

    # Backward-compatible aliases used by older page modules/tests.
    WELCOME = OPEN
    ARTIST_SEARCH = RELEASE
    GENERATE_ALBUM_LAYOUT = ALIGN
    FINISH = EXPORT

    # Standalone/legacy pages (not registered in the main wizard).
    RELEASE_SELECTION = 10
    TRACK_LIST = 11
    REVIEW = 12
