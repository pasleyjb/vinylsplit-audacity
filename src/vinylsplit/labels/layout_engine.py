"""Album layout generation from MusicBrainz release metadata."""

from __future__ import annotations

from dataclasses import dataclass, replace

from vinylsplit.metadata.models import Release, Track
from vinylsplit.metadata.tracks import flatten_tracks, format_numbered_track_line, format_track_number

# Minimum allowed track length when stretching/shrinking a split (seconds).
_MIN_TRACK_DURATION = 0.05


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

    def with_offset(self, offset_seconds: float) -> AlbumLayout:
        """Return a copy with every boundary shifted by *offset_seconds*.

        Durations are preserved. Negative offsets that would push a start
        below zero are clamped so the first region starts at 0.0 and later
        regions stay contiguous with the same durations.
        """
        return self.transformed(offset_seconds=offset_seconds, scale=1.0)

    def transformed(
        self,
        *,
        offset_seconds: float = 0.0,
        scale: float = 1.0,
    ) -> AlbumLayout:
        """Shift and/or scale region durations from the first track start.

        *scale* multiplies each track's duration (1.0 = MusicBrainz lengths).
        *offset_seconds* is added to the first start (and thus the whole chain).
        If the first start would be negative, it is clamped to 0.0.
        """
        if not self.regions:
            return self

        safe_scale = scale if scale > 0 else 1.0
        durations = [max(0.0, region.duration_seconds * safe_scale) for region in self.regions]
        cursor = max(0.0, float(offset_seconds))
        new_regions: list[TrackRegion] = []

        for region, duration in zip(self.regions, durations, strict=True):
            start = cursor
            end = cursor + duration
            new_regions.append(
                TrackRegion(
                    track_index=region.track_index,
                    track_number=region.track_number,
                    title=region.title,
                    label_text=region.label_text,
                    start_seconds=start,
                    end_seconds=end,
                )
            )
            cursor = end

        return AlbumLayout(
            release_id=self.release_id,
            artist_name=self.artist_name,
            album_title=self.album_title,
            regions=tuple(new_regions),
        )

    def shift_from_index(
        self,
        index: int,
        delta_seconds: float,
        *,
        min_track_duration: float = _MIN_TRACK_DURATION,
    ) -> AlbumLayout:
        """Move marker *index* and everything after it by *delta_seconds*.

        Lattice editing semantics (contiguous regions):

        - **index 0 (track 1):** shift the **entire** lattice. All durations stay
          the same; every start/end moves by the same amount (clamped so the
          first start is never negative).
        - **index > 0:** tracks **before** *index* keep their starts. Track
          ``index - 1`` is resized so its end meets the new start of *index*.
          Track *index* and all later tracks keep their durations and shift
          together.

        This matches: move track 2 → only 2…N move; move track 3 → 1–2 stay,
        3…N move.
        """
        if not self.regions or abs(delta_seconds) < 1e-12:
            return self

        index = max(0, min(int(index), len(self.regions) - 1))
        regions = self.regions

        if index == 0:
            first_start = max(0.0, regions[0].start_seconds + delta_seconds)
            actual = first_start - regions[0].start_seconds
            if abs(actual) < 1e-12:
                return self
            new_regions = tuple(
                replace(
                    region,
                    start_seconds=region.start_seconds + actual,
                    end_seconds=region.end_seconds + actual,
                )
                for region in regions
            )
            return AlbumLayout(
                release_id=self.release_id,
                artist_name=self.artist_name,
                album_title=self.album_title,
                regions=new_regions,
            )

        prev = regions[index - 1]
        cur = regions[index]
        new_start = cur.start_seconds + delta_seconds
        min_start = prev.start_seconds + max(min_track_duration, 0.0)
        new_start = max(min_start, new_start)
        actual = new_start - cur.start_seconds
        if abs(actual) < 1e-12:
            return self

        new_regions: list[TrackRegion] = []
        for i, region in enumerate(regions):
            if i < index - 1:
                new_regions.append(region)
            elif i == index - 1:
                new_regions.append(replace(region, end_seconds=new_start))
            else:
                new_regions.append(
                    replace(
                        region,
                        start_seconds=region.start_seconds + actual,
                        end_seconds=region.end_seconds + actual,
                    )
                )

        return AlbumLayout(
            release_id=self.release_id,
            artist_name=self.artist_name,
            album_title=self.album_title,
            regions=tuple(new_regions),
        )


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

    def generate_transformed(
        self,
        release: Release,
        *,
        offset_seconds: float = 0.0,
        scale: float = 1.0,
    ) -> AlbumLayout:
        """Generate a layout then apply offset/scale transforms."""
        return self.generate(release).transformed(
            offset_seconds=offset_seconds,
            scale=scale,
        )


def _track_duration_seconds(track: Track) -> float:
    if track.length_ms is None:
        return 0.0
    return track.length_ms / 1000.0