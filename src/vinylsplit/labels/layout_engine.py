"""Album layout generation from MusicBrainz release metadata."""

from __future__ import annotations

from dataclasses import dataclass

from vinylsplit.metadata.models import Release, Track
from vinylsplit.metadata.tracks import flatten_tracks, format_numbered_track_line, format_track_number


@dataclass(frozen=True)
class TrackRegion:
    """One contiguous track region in the album layout."""

    track_index: int
    track_number: str
    title: str
    label_text: str
    start_seconds: float
    end_seconds: float

    @property
    def duration_seconds(self) -> float:
        """Return the region length in seconds."""
        return self.end_seconds - self.start_seconds


@dataclass(frozen=True)
class AlbumLayout:
    """Complete album region layout derived from a MusicBrainz release."""

    release_id: str
    artist_name: str
    album_title: str
    regions: tuple[TrackRegion, ...]

    @property
    def track_count(self) -> int:
        """Return how many track regions the layout contains."""
        return len(self.regions)

    @property
    def total_duration_seconds(self) -> float:
        """Return the summed duration across every region."""
        if not self.regions:
            return 0.0
        return self.regions[-1].end_seconds


class LabelLayoutEngine:
    """Generate contiguous album regions from MusicBrainz track durations."""

    def generate(self, release: Release) -> AlbumLayout:
        """Build an :class:`AlbumLayout` for *release*.

        The first region always starts at ``0.0`` seconds. Each subsequent
        region begins where the previous track ends. Region end times are
        calculated from cumulative MusicBrainz track durations.
        """
        tracks = flatten_tracks(release)
        regions: list[TrackRegion] = []
        cumulative_seconds = 0.0

        for index, track in enumerate(tracks):
            duration_seconds = _track_duration_seconds(track)
            start_seconds = cumulative_seconds
            end_seconds = cumulative_seconds + duration_seconds
            regions.append(
                TrackRegion(
                    track_index=index,
                    track_number=format_track_number(track),
                    title=track.title,
                    label_text=format_numbered_track_line(track),
                    start_seconds=start_seconds,
                    end_seconds=end_seconds,
                )
            )
            cumulative_seconds = end_seconds

        return AlbumLayout(
            release_id=release.id,
            artist_name=release.artist_name,
            album_title=release.title,
            regions=tuple(regions),
        )


def _track_duration_seconds(track: Track) -> float:
    if track.length_ms is None:
        return 0.0
    return track.length_ms / 1000.0