"""Stable identifiers for wizard pages."""

from __future__ import annotations

from enum import IntEnum


class PageId(IntEnum):
    """Ordered wizard page identifiers."""

    WELCOME = 0
    ARTIST_SEARCH = 1
    RELEASE_SELECTION = 2
    TRACK_LIST = 3
    GENERATE_ALBUM_LAYOUT = 4
    REVIEW = 5
    FINISH = 6