"""Wizard session state shared across pages."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from vinylsplit.metadata.models import Release, ReleaseSummary, Track
from vinylsplit.metadata.tracks import flatten_tracks

if TYPE_CHECKING:
    from vinylsplit.labels.layout_engine import AlbumLayout

_logger = logging.getLogger(__name__)


class ExportFormat(StrEnum):
    """Supported export formats for split tracks."""

    WAV = "wav"
    FLAC = "flac"
    MP3 = "mp3"
    OGG = "ogg"


@dataclass(frozen=True)
class AlbumArtwork:
    """Album cover art associated with the selected release."""

    data: bytes | None = None
    mime_type: str | None = None
    source_url: str | None = None

    @property
    def is_available(self) -> bool:
        """Return True when binary artwork data is present."""
        return self.data is not None and len(self.data) > 0


@dataclass
class WizardSession:
    """Strongly typed, cross-page state for the digitization workflow.

    Pages read and write workflow data exclusively through a
    :class:`WizardSession` instance injected by the dependency container.
    No page should reference another page directly.
    """

    audacity_connected: bool = False
    selected_release: Release | None = None
    album_artwork: AlbumArtwork | None = None
    track_list: list[Track] = field(default_factory=list)
    album_layout: AlbumLayout | None = None
    initial_regions_generated: bool = False
    layout_review_refreshed: bool = False
    regions_created_count: int = 0
    export_format: ExportFormat | None = None
    output_directory: Path | None = None
    export_completed: bool = False
    exported_track_count: int = 0
    recording_already_completed: bool = False
    validation_errors: list[str] = field(default_factory=list)
    layout_generation_started_at: float | None = None
    layout_generation_finished_at: float | None = None

    # MusicBrainz search workflow data gathered before release review.
    search_results: list[ReleaseSummary] = field(default_factory=list)
    last_artist_query: str = ""
    last_album_query: str = ""

    def set_audacity_connected(self, connected: bool) -> None:
        """Record whether Audacity communication is available."""
        self.audacity_connected = connected

    def set_selected_release(self, release: Release) -> None:
        """Store the chosen release and refresh derived session fields."""
        from vinylsplit.labels.layout_engine import LabelLayoutEngine

        self.selected_release = release
        self.track_list = flatten_tracks(release)
        self.album_layout = LabelLayoutEngine().generate(release)
        self._reset_layout_workflow_state()

    def clear_selected_release(self) -> None:
        """Remove the selected release and derived track metadata."""
        self.selected_release = None
        self.album_artwork = None
        self.track_list = []
        self.album_layout = None
        self._reset_layout_workflow_state()

    def _reset_layout_workflow_state(self) -> None:
        self.initial_regions_generated = False
        self.layout_review_refreshed = False
        self.regions_created_count = 0
        self.layout_generation_started_at = None
        self.layout_generation_finished_at = None

    def set_album_artwork(self, artwork: AlbumArtwork | None) -> None:
        """Store album artwork for the selected release."""
        self.album_artwork = artwork

    def set_export_format(self, export_format: ExportFormat | None) -> None:
        """Store the export format chosen for output files."""
        self.export_format = export_format

    def set_output_directory(self, directory: Path | None) -> None:
        """Store the destination directory for exported tracks."""
        self.output_directory = directory

    def mark_export_completed(self, count: int) -> None:
        """Record a successful album export."""
        self.export_completed = True
        self.exported_track_count = count
        _logger.debug("export_completed=True exported_track_count=%d", count)

    def set_recording_already_completed(self, completed: bool) -> None:
        """Record whether the vinyl recording step is already finished."""
        self.recording_already_completed = completed

    def add_validation_error(self, message: str) -> None:
        """Append a user-facing validation message."""
        if message and message not in self.validation_errors:
            self.validation_errors.append(message)

    def clear_validation_errors(self) -> None:
        """Remove all validation messages."""
        self.validation_errors.clear()

    def mark_initial_regions_generated(self, count: int) -> None:
        """Record that all initial track regions were created in Audacity."""
        self.initial_regions_generated = True
        self.regions_created_count = count
        self.layout_review_refreshed = False
        self.finish_layout_generation()
        _logger.debug(
            "initial_regions_generated=True regions_created_count=%d",
            count,
        )

    def mark_layout_review_refreshed(self) -> None:
        """Record that the user refreshed the region layout from Audacity."""
        self.layout_review_refreshed = True
        _logger.debug("layout_review_refreshed=True")

    def has_selected_release(self) -> bool:
        """Return True when a release has been chosen."""
        return self.selected_release is not None

    def has_validation_errors(self) -> bool:
        """Return True when one or more validation errors are present."""
        return bool(self.validation_errors)

    def start_layout_generation(self) -> None:
        """Record the start of album layout generation."""
        if self.layout_generation_started_at is None:
            self.layout_generation_started_at = time.monotonic()

    def finish_layout_generation(self) -> None:
        """Record when initial regions have been generated."""
        if self.layout_generation_finished_at is None:
            self.layout_generation_finished_at = time.monotonic()

    def layout_generation_elapsed_seconds(self) -> float | None:
        """Return elapsed layout generation time in seconds."""
        if self.layout_generation_started_at is None:
            return None
        end = self.layout_generation_finished_at
        if end is None:
            return time.monotonic() - self.layout_generation_started_at
        return end - self.layout_generation_started_at

    def ready_for_export(self) -> bool:
        """Return True when regions were generated and reviewed."""
        return self.initial_regions_generated and self.layout_review_refreshed