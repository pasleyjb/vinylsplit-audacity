"""Build export metadata from MusicBrainz release data."""

from __future__ import annotations

from vinylsplit.export.models import ExportRegion, TrackExportMetadata
from vinylsplit.labels.layout_engine import AlbumLayout
from vinylsplit.metadata.models import Release, Track


def build_export_regions(
    layout: AlbumLayout,
    tracks: list[Track],
    audacity_regions: list[dict[str, object]],
) -> list[ExportRegion]:
    """Match layout regions to Audacity labels and use edited boundaries."""
    regions_by_text = _regions_indexed_by_text(audacity_regions)
    export_regions: list[ExportRegion] = []

    for region in layout.regions:
        matched = regions_by_text.get(region.label_text)
        start = _region_boundary_seconds(matched, "start")
        end = _region_boundary_seconds(matched, "end")
        if start is None or end is None:
            continue

        track = (
            tracks[region.track_index]
            if 0 <= region.track_index < len(tracks)
            else None
        )
        export_regions.append(
            ExportRegion(
                track_number=region.track_number,
                title=region.title,
                label_text=region.label_text,
                start_seconds=start,
                end_seconds=end,
                track_id=track.id if track is not None else None,
            )
        )

    return export_regions


def build_track_metadata(
    release: Release,
    region: ExportRegion,
) -> TrackExportMetadata:
    """Build tag metadata for one exported track."""
    return TrackExportMetadata(
        artist=release.artist_name,
        album=release.title,
        title=region.title,
        track_number=region.track_number,
        genre=release.genre,
        date=release.date,
        release_id=release.id,
        release_group_id=release.release_group_id,
        artist_id=release.artist.id,
        track_id=region.track_id,
    )


def _regions_indexed_by_text(
    regions: list[dict[str, object]],
) -> dict[str, dict[str, object]]:
    indexed: dict[str, dict[str, object]] = {}
    for region in regions:
        text = region.get("text")
        if isinstance(text, str) and text:
            indexed[text] = region
    return indexed


def _region_boundary_seconds(
    region: dict[str, object] | None,
    key: str,
) -> float | None:
    if region is None:
        return None
    value = region.get(key)
    if isinstance(value, (int, float)):
        return float(value)
    return None