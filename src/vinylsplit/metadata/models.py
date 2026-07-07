"""Domain models for MusicBrainz release metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ExportFormat(StrEnum):
    """Supported audio export formats."""

    WAV = "wav"
    FLAC = "flac"
    MP3 = "mp3"


@dataclass(frozen=True)
class AlbumArtwork:
    """Album cover art associated with the selected release."""

    data: bytes | None = None
    mime_type: str | None = None
    source_url: str | None = None

    @property
    def is_available(self) -> bool:
        """Return True when binary artwork data is present."""
        return bool(self.data)


@dataclass(frozen=True)
class Artist:
    """MusicBrainz artist reference."""

    id: str | None
    name: str


@dataclass(frozen=True)
class Track:
    """Track on a release medium."""

    id: str | None
    title: str
    position: int
    number: str
    length_ms: int | None = None


@dataclass(frozen=True)
class Medium:
    """Physical or logical medium within a release."""

    position: int
    format: str | None
    track_count: int
    tracks: tuple[Track, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ReleaseSummary:
    """Compact release data for search result tables."""

    id: str
    artist: str
    album: str
    release_year: str
    country: str
    track_count: int
    release_type: str


@dataclass(frozen=True)
class Release:
    """Complete MusicBrainz release with media and tracks."""

    id: str
    title: str
    artist: Artist
    date: str | None
    country: str | None
    release_year: str
    release_type: str
    track_count: int
    status: str | None
    release_group_id: str | None = None
    genre: str | None = None
    media: tuple[Medium, ...] = field(default_factory=tuple)

    @property
    def artist_name(self) -> str:
        """Convenience accessor for the credited artist name."""
        return self.artist.name