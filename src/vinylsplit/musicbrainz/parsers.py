"""Parse MusicBrainz JSON payloads into domain models."""

from __future__ import annotations

from typing import Any

from vinylsplit.metadata.models import (
    Artist,
    Medium,
    Release,
    ReleaseSummary,
    Track,
)


def parse_release_summaries(payload: dict[str, Any]) -> list[ReleaseSummary]:
    """Parse a release search response into table rows."""
    releases = payload.get("releases", [])
    summaries: list[ReleaseSummary] = []

    for release in releases:
        if not isinstance(release, dict):
            continue
        release_id = release.get("id")
        title = release.get("title")
        if not release_id or not title:
            continue

        summaries.append(
            ReleaseSummary(
                id=release_id,
                artist=_artist_name(release.get("artist-credit", [])),
                album=title,
                release_year=_release_year(release.get("date")),
                country=release.get("country") or "—",
                track_count=_track_count(release),
                release_type=_release_type(release.get("release-group", {})),
            )
        )

    return summaries


def parse_release(payload: dict[str, Any]) -> Release:
    """Parse a full release lookup response."""
    release_id = payload.get("id")
    title = payload.get("title")
    if not release_id or not title:
        msg = "MusicBrainz release payload is missing required fields."
        raise ValueError(msg)

    artist_credit = payload.get("artist-credit", [])
    artist = _parse_artist(artist_credit)
    release_group = payload.get("release-group", {})
    media = tuple(_parse_medium(item) for item in payload.get("media", []))
    track_count = sum(medium.track_count for medium in media)

    return Release(
        id=release_id,
        title=title,
        artist=artist,
        date=payload.get("date"),
        country=payload.get("country"),
        release_year=_release_year(payload.get("date")),
        release_type=_release_type(release_group),
        track_count=track_count,
        status=payload.get("status"),
        release_group_id=_release_group_id(release_group),
        genre=_genre(release_group),
        media=media,
    )


def _parse_artist(artist_credit: list[Any]) -> Artist:
    name = _artist_name(artist_credit)
    artist_id = None
    if artist_credit:
        first = artist_credit[0]
        if isinstance(first, dict):
            artist_obj = first.get("artist")
            if isinstance(artist_obj, dict):
                artist_id = artist_obj.get("id")
    return Artist(id=artist_id, name=name)


def _parse_medium(payload: dict[str, Any]) -> Medium:
    tracks = tuple(_parse_track(track) for track in payload.get("tracks", []))
    declared_count = payload.get("track-count")
    track_count = (
        int(declared_count) if isinstance(declared_count, int) else len(tracks)
    )
    return Medium(
        position=int(payload.get("position", 1)),
        format=payload.get("format"),
        track_count=track_count,
        tracks=tracks,
    )


def _parse_track(payload: dict[str, Any]) -> Track:
    position = int(payload.get("position", 0))
    return Track(
        id=payload.get("id"),
        title=str(payload.get("title", "Unknown Track")),
        position=position,
        number=str(payload.get("number", position)),
        length_ms=_coerce_length(payload.get("length")),
    )


def _artist_name(artist_credit: list[Any]) -> str:
    parts: list[str] = []
    for credit in artist_credit:
        if isinstance(credit, dict):
            parts.append(str(credit.get("name", "")))
    name = "".join(parts).strip()
    return name or "Unknown Artist"


def _release_year(date_value: str | None) -> str:
    if not date_value:
        return "—"
    return date_value[:4] if len(date_value) >= 4 else date_value


def _track_count(release: dict[str, Any]) -> int:
    media = release.get("media", [])
    total = 0
    for medium in media:
        if isinstance(medium, dict):
            count = medium.get("track-count")
            if isinstance(count, int):
                total += count
    return total


def _release_group_id(release_group: Any) -> str | None:
    if isinstance(release_group, dict):
        group_id = release_group.get("id")
        if isinstance(group_id, str) and group_id:
            return group_id
    return None


def _genre(release_group: Any) -> str | None:
    if not isinstance(release_group, dict):
        return None
    primary = release_group.get("primary-type")
    if isinstance(primary, str) and primary:
        return primary
    return None


def _release_type(release_group: Any) -> str:
    if not isinstance(release_group, dict):
        return "Unknown"

    primary = release_group.get("primary-type") or "Unknown"
    secondary = release_group.get("secondary-types", [])
    if isinstance(secondary, list) and secondary:
        joined = ", ".join(str(item) for item in secondary)
        return f"{primary} ({joined})"
    return str(primary)


def _coerce_length(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    return None
