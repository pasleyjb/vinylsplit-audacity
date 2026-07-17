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
    from vinylsplit.metadata.local_tags import LocalAudioTags

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
    # Base layout from MusicBrainz (before offset/scale); used to recompute.
    base_album_layout: AlbumLayout | None = None
    layout_offset_seconds: float = 0.0
    layout_scale: float = 1.0
    initial_regions_generated: bool = False
    layout_review_refreshed: bool = False
    skipped_region_generation: bool = False
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

    # Source audio chosen in VinylSplit (or detected from Audacity).
    source_audio_path: Path | None = None
    local_tags: LocalAudioTags | None = None
    audio_imported_to_audacity: bool = False
    metadata_seed_source: str = ""  # file | audacity | manual | ""

    def set_audacity_connected(self, connected: bool) -> None:
        """Record whether Audacity communication is available."""
        self.audacity_connected = connected

    def set_source_audio(
        self,
        path: Path | None,
        tags: LocalAudioTags | None = None,
        *,
        seed_source: str = "file",
    ) -> None:
        """Store the source capture file and optional parsed tags.

        When *tags* include artist/album values, also seed the MusicBrainz
        search fields so the next wizard page can prefill and search.
        """
        self.source_audio_path = path
        self.local_tags = tags
        self.audio_imported_to_audacity = False
        if path is None:
            self.metadata_seed_source = ""
            return

        self.metadata_seed_source = seed_source
        if tags is not None and tags.has_search_seed:
            if tags.search_artist:
                self.last_artist_query = tags.search_artist
            if tags.search_album:
                self.last_album_query = tags.search_album
            _logger.debug(
                "Seeded search from %s: artist=%r album=%r",
                seed_source,
                self.last_artist_query,
                self.last_album_query,
            )

    def clear_source_audio(self) -> None:
        """Remove the chosen source file and tag seed."""
        self.source_audio_path = None
        self.local_tags = None
        self.audio_imported_to_audacity = False
        # Keep last_* search queries so the user does not lose typed text.

    def set_search_seed(
        self,
        *,
        artist: str = "",
        album: str = "",
        seed_source: str = "manual",
    ) -> None:
        """Seed MusicBrainz search fields without changing the source file."""
        if artist.strip():
            self.last_artist_query = artist.strip()
        if album.strip():
            self.last_album_query = album.strip()
        if artist.strip() or album.strip():
            self.metadata_seed_source = seed_source

    def mark_audio_imported(self) -> None:
        """Record that the source file was imported into Audacity."""
        self.audio_imported_to_audacity = True

    def set_selected_release(self, release: Release) -> None:
        """Store the chosen release and refresh derived session fields."""
        from vinylsplit.labels.layout_engine import LabelLayoutEngine

        self.selected_release = release
        self.track_list = flatten_tracks(release)
        base = LabelLayoutEngine().generate(release)
        self.base_album_layout = base
        self.layout_offset_seconds = 0.0
        self.layout_scale = 1.0
        self.album_layout = base
        self._reset_layout_workflow_state()

    def clear_selected_release(self) -> None:
        """Remove the selected release and derived track metadata."""
        self.selected_release = None
        self.album_artwork = None
        self.track_list = []
        self.album_layout = None
        self.base_album_layout = None
        self.layout_offset_seconds = 0.0
        self.layout_scale = 1.0
        self._reset_layout_workflow_state()

    def _reset_layout_workflow_state(self) -> None:
        self.initial_regions_generated = False
        self.layout_review_refreshed = False
        self.skipped_region_generation = False
        self.regions_created_count = 0
        self.layout_generation_started_at = None
        self.layout_generation_finished_at = None

    def set_layout_transform(
        self,
        *,
        offset_seconds: float | None = None,
        scale: float | None = None,
    ) -> None:
        """Update offset/scale and recompute :attr:`album_layout` from the base."""
        if offset_seconds is not None:
            self.layout_offset_seconds = float(offset_seconds)
        if scale is not None:
            self.layout_scale = float(scale) if float(scale) > 0 else 1.0

        base = self.base_album_layout
        if base is None and self.selected_release is not None:
            from vinylsplit.labels.layout_engine import LabelLayoutEngine

            base = LabelLayoutEngine().generate(self.selected_release)
            self.base_album_layout = base

        if base is None:
            self.album_layout = None
            return

        self.album_layout = base.transformed(
            offset_seconds=self.layout_offset_seconds,
            scale=self.layout_scale,
        )
        self._invalidate_written_regions()

    def set_edited_layout(self, layout: AlbumLayout | None) -> None:
        """Store a user-edited absolute lattice (from waveform drag)."""
        self.album_layout = layout
        if layout is not None and layout.regions:
            self.layout_offset_seconds = layout.regions[0].start_seconds
        self._invalidate_written_regions()

    def _invalidate_written_regions(self) -> None:
        """Changing the lattice invalidates prior Audacity writes / skip state."""
        self.initial_regions_generated = False
        self.layout_review_refreshed = False
        self.skipped_region_generation = False
        self.regions_created_count = 0

    def mark_using_existing_regions(self, count: int) -> None:
        """Record that existing Audacity labels will be used (no overwrite)."""
        self.skipped_region_generation = True
        self.initial_regions_generated = True
        self.layout_review_refreshed = True
        self.regions_created_count = count
        self.finish_layout_generation()
        _logger.debug(
            "skipped_region_generation=True regions_created_count=%d",
            count,
        )

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
        # No separate review page in the streamlined wizard.
        self.layout_review_refreshed = True
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
        """Return True when Audacity regions are ready (written or skipped)."""
        # Streamlined wizard no longer requires a separate review step.
        return self.initial_regions_generated

    def reset(self) -> None:
        """Clear workflow state so the user can start a new album."""
        self.audacity_connected = False
        self.selected_release = None
        self.album_artwork = None
        self.track_list = []
        self.album_layout = None
        self.base_album_layout = None
        self.layout_offset_seconds = 0.0
        self.layout_scale = 1.0
        self.initial_regions_generated = False
        self.layout_review_refreshed = False
        self.skipped_region_generation = False
        self.regions_created_count = 0
        self.export_format = None
        self.output_directory = None
        self.export_completed = False
        self.exported_track_count = 0
        self.recording_already_completed = False
        self.validation_errors.clear()
        self.layout_generation_started_at = None
        self.layout_generation_finished_at = None
        self.search_results = []
        self.last_artist_query = ""
        self.last_album_query = ""
        self.source_audio_path = None
        self.local_tags = None
        self.audio_imported_to_audacity = False
        self.metadata_seed_source = ""
        _logger.info("Wizard session reset for a new album")