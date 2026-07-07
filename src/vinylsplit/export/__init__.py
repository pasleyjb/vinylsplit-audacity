"""Track export workflows."""

from vinylsplit.export.artwork import ArtworkFetchResult, fetch_release_artwork
from vinylsplit.export.engine import ExportEngine, export_album
from vinylsplit.export.models import (
    AlbumExportResult,
    ExportRegion,
    ExportSettings,
    TrackExportMetadata,
    TrackExportResult,
)
from vinylsplit.export.tagger import embed_track_metadata

__all__ = [
    "AlbumExportResult",
    "ArtworkFetchResult",
    "ExportEngine",
    "ExportRegion",
    "ExportSettings",
    "TrackExportMetadata",
    "TrackExportResult",
    "embed_track_metadata",
    "export_album",
    "fetch_release_artwork",
]