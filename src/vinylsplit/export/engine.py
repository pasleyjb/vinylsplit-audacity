"""Orchestrate album export from Audacity regions."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from vinylsplit.audacity.client import AudacityClient, AudacityError
from vinylsplit.export.artwork import fetch_release_artwork
from vinylsplit.export.audacity_exporter import export_region_to_file
from vinylsplit.export.filenames import build_track_filename
from vinylsplit.export.metadata import build_export_regions, build_track_metadata
from vinylsplit.export.models import AlbumExportResult, ExportSettings, TrackExportResult
from vinylsplit.export.tagger import embed_track_metadata
from vinylsplit.labels.audacity_regions import fetch_audacity_regions
from vinylsplit.metadata.models import Release
from vinylsplit.metadata.session import AlbumArtwork, ExportFormat
from vinylsplit.metadata.tracks import flatten_tracks

_logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int], None]


class ExportEngine:
    """Export every matched Audacity region with embedded metadata."""

    def __init__(self, client: AudacityClient) -> None:
        self._client = client

    def export_album(
        self,
        release: Release,
        *,
        settings: ExportSettings,
        artwork: AlbumArtwork | None = None,
        fetch_artwork_if_missing: bool = True,
        progress_callback: ProgressCallback | None = None,
    ) -> AlbumExportResult:
        """Export all labeled regions for *release* into *settings.output_directory*."""
        if not self._client.is_connected():
            return AlbumExportResult(
                success=False,
                message="Audacity client is not connected.",
            )

        from vinylsplit.labels.layout_engine import LabelLayoutEngine

        layout = LabelLayoutEngine().generate(release)
        tracks = flatten_tracks(release)

        try:
            audacity_regions = fetch_audacity_regions(self._client)
        except AudacityError as exc:
            return AlbumExportResult(success=False, message=str(exc))

        export_regions = build_export_regions(layout, tracks, audacity_regions)
        if not export_regions:
            return AlbumExportResult(
                success=False,
                message="No Audacity regions matched the album layout.",
            )

        resolved_artwork = artwork
        if fetch_artwork_if_missing and (
            resolved_artwork is None or not resolved_artwork.is_available
        ):
            artwork_result = fetch_release_artwork(release.id)
            resolved_artwork = artwork_result.artwork
            if resolved_artwork is None:
                _logger.info("Continuing export without artwork: %s", artwork_result.message)

        settings.output_directory.mkdir(parents=True, exist_ok=True)
        track_results: list[TrackExportResult] = []
        exported = 0
        total = len(export_regions)

        for index, region in enumerate(export_regions, start=1):
            metadata = build_track_metadata(release, region)
            filename = build_track_filename(
                region.track_number,
                region.title,
                settings.export_format,
            )
            output_path = settings.output_directory / filename

            export_result = export_region_to_file(
                self._client,
                region,
                output_path,
            )
            if not export_result.success:
                track_results.append(export_result)
                return AlbumExportResult(
                    success=False,
                    message=export_result.message,
                    tracks_exported=exported,
                    output_directory=settings.output_directory,
                    track_results=tuple(track_results),
                )

            try:
                embed_track_metadata(
                    output_path,
                    metadata,
                    export_format=settings.export_format,
                    artwork=resolved_artwork,
                )
            except (OSError, ValueError) as exc:
                track_results.append(
                    TrackExportResult(
                        label_text=region.label_text,
                        output_path=output_path,
                        success=False,
                        message=f"Metadata embedding failed: {exc}",
                    )
                )
                return AlbumExportResult(
                    success=False,
                    message=str(exc),
                    tracks_exported=exported,
                    output_directory=settings.output_directory,
                    track_results=tuple(track_results),
                )

            exported += 1
            track_results.append(export_result)
            if progress_callback is not None:
                progress_callback(index, total)

        return AlbumExportResult(
            success=True,
            message=f"Exported {exported} track(s) to {settings.output_directory}.",
            tracks_exported=exported,
            output_directory=settings.output_directory,
            track_results=tuple(track_results),
        )


def export_album(
    client: AudacityClient,
    release: Release,
    *,
    settings: ExportSettings,
    artwork: AlbumArtwork | None = None,
    progress_callback: ProgressCallback | None = None,
) -> AlbumExportResult:
    """Convenience wrapper around :class:`ExportEngine`."""
    return ExportEngine(client).export_album(
        release,
        settings=settings,
        artwork=artwork,
        progress_callback=progress_callback,
    )