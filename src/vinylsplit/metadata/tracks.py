"""Track formatting and release track helpers."""

from __future__ import annotations

from vinylsplit.metadata.models import Release, Track


def flatten_tracks(release: Release) -> list[Track]:
    """Return all tracks across every medium in playback order."""
    tracks: list[Track] = []
    for medium in release.media:
        tracks.extend(medium.tracks)
    return tracks


def format_track_number(track: Track) -> str:
    """Format a track number for display (e.g. ``01``)."""
    if track.number.isdigit():
        return track.number.zfill(2)
    if track.position > 0:
        return f"{track.position:02d}"
    return track.number


def format_track_length(length_ms: int | None) -> str:
    """Format a track length in ``m:ss`` form."""
    if length_ms is None:
        return "—"
    total_seconds = length_ms // 1000
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


def format_numbered_track_line(track: Track) -> str:
    """Format one track as ``01 Track Name``."""
    return f"{format_track_number(track)} {track.title}"


def format_numbered_track_list(release: Release) -> str:
    """Format all tracks as a numbered list."""
    lines = [format_numbered_track_line(track) for track in flatten_tracks(release)]
    return "\n".join(lines)
