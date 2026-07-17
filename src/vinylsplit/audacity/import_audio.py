"""Import audio into Audacity and probe open project track names."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vinylsplit.audacity.client import AudacityClient, AudacityError
from vinylsplit.audacity.responses import parse_json_response

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AudacityProjectProbe:
    """Lightweight snapshot of the open Audacity project."""

    track_names: tuple[str, ...] = ()
    track_count: int = 0

    @property
    def has_audio_tracks(self) -> bool:
        return self.track_count > 0


def import_audio_file(client: AudacityClient, path: Path | str) -> None:
    """Import *path* into the current Audacity project via ``Import2``.

    Args:
        client: Connected :class:`AudacityClient`.
        path: Audio file on disk.

    Raises:
        FileNotFoundError: When *path* does not exist.
        AudacityError: When Audacity rejects the import.
    """
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        msg = f"Audio file not found: {resolved}"
        raise FileNotFoundError(msg)

    escaped = _escape_command_value(str(resolved))
    _logger.info("Importing audio into Audacity: %s", resolved)
    client.execute(f'Import2: Filename="{escaped}"')


def probe_audacity_project(client: AudacityClient) -> AudacityProjectProbe:
    """Return track names/count from the open Audacity project.

    Uses ``GetInfo: Type=Tracks Format=JSON``. Empty when the project has no
    tracks or the response cannot be parsed.
    """
    try:
        response = client.execute("GetInfo: Type=Tracks Format=JSON")
        payload = parse_json_response(response)
    except (AudacityError, ValueError, TypeError) as exc:
        _logger.debug("Could not probe Audacity tracks: %s", exc)
        return AudacityProjectProbe()

    names = _extract_track_names(payload)
    return AudacityProjectProbe(track_names=tuple(names), track_count=len(names))


def seed_queries_from_track_names(track_names: tuple[str, ...] | list[str]) -> tuple[str, str]:
    """Best-effort artist/album seeds from Audacity track names.

    Vinyl captures often use a single long track named after the file
    (``Artist - Album``). Returns ``("", "")`` when nothing useful is found.
    """
    if not track_names:
        return "", ""

    primary = track_names[0].strip()
    if not primary:
        return "", ""

    # "Artist - Album" style
    for sep in (" - ", " – ", " — "):
        if sep in primary:
            left, right = primary.split(sep, 1)
            left, right = left.strip(), right.strip()
            if left and right:
                return left, right

    # Single name — treat as album only
    return "", primary


def _extract_track_names(payload: Any) -> list[str]:
    if not isinstance(payload, list):
        return []
    names: list[str] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("Name") or ""
        if isinstance(name, str) and name.strip():
            names.append(name.strip())
        else:
            names.append("")
    # Count non-empty + empty tracks that still represent audio slots
    if not names and payload:
        return [""] * len(payload)
    return names


def _escape_command_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
