"""Export workflow data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from vinylsplit.metadata.session import ExportFormat


@dataclass(frozen=True)
class TrackExportMetadata:
    """Metadata embedded into one exported track file."""

    artist: str
    album: str
    title: str
    track_number: str
    genre: str | None
    date: str | None
    release_id: str
    release_group_id: str | None
    artist_id: str | None
    track_id: str | None


@dataclass(frozen=True)
class ExportRegion:
    """One Audacity region ready for export."""

    track_number: str
    title: str
    label_text: str
    start_seconds: float
    end_seconds: float
    track_id: str | None


@dataclass(frozen=True)
class TrackExportItem:
    """One track export plan with destination path and metadata."""

    region: ExportRegion
    metadata: TrackExportMetadata
    output_path: Path


@dataclass(frozen=True)
class TrackExportResult:
    """Outcome of exporting a single track."""

    label_text: str
    output_path: Path
    success: bool
    message: str


@dataclass(frozen=True)
class AlbumExportResult:
    """Outcome of exporting every matched track region."""

    success: bool
    message: str
    tracks_exported: int = 0
    output_directory: Path | None = None
    track_results: tuple[TrackExportResult, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ExportSettings:
    """User-selected export options."""

    output_directory: Path
    export_format: ExportFormat