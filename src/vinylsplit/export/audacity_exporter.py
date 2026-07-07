"""Export selected Audacity regions to individual audio files."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from vinylsplit.audacity.client import AudacityClient, AudacityError
from vinylsplit.export.models import ExportRegion, TrackExportResult

_logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int], None]


def export_region_to_file(
    client: AudacityClient,
    region: ExportRegion,
    output_path: Path,
) -> TrackExportResult:
    """Export one Audacity time selection to *output_path*."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    try:
        client.execute(
            f"SelectTime: Start={region.start_seconds} End={region.end_seconds}"
        )
        escaped_path = _escape_command_value(str(output_path))
        client.execute(f'Export2: Filename="{escaped_path}"')
    except AudacityError as exc:
        _logger.warning(
            "Failed exporting %r to %s: %s",
            region.label_text,
            output_path,
            exc,
        )
        return TrackExportResult(
            label_text=region.label_text,
            output_path=output_path,
            success=False,
            message=str(exc),
        )

    if not output_path.exists() or output_path.stat().st_size == 0:
        return TrackExportResult(
            label_text=region.label_text,
            output_path=output_path,
            success=False,
            message="Audacity did not create the export file.",
        )

    return TrackExportResult(
        label_text=region.label_text,
        output_path=output_path,
        success=True,
        message=f"Exported {region.label_text}",
    )


def export_regions_to_files(
    client: AudacityClient,
    regions: list[ExportRegion],
    output_paths: list[Path],
    *,
    progress_callback: ProgressCallback | None = None,
) -> list[TrackExportResult]:
    """Export every region to its corresponding output path."""
    if len(regions) != len(output_paths):
        msg = "Region and output path counts must match."
        raise ValueError(msg)

    results: list[TrackExportResult] = []
    total = len(regions)

    for index, (region, output_path) in enumerate(
        zip(regions, output_paths, strict=True),
        start=1,
    ):
        results.append(export_region_to_file(client, region, output_path))
        if progress_callback is not None:
            progress_callback(index, total)

    return results


def _escape_command_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')