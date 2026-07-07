"""Audacity communication for creating and reading region labels."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass

from vinylsplit.audacity.client import AudacityClient, AudacityError
from vinylsplit.audacity.responses import parse_json_response
from vinylsplit.labels.layout_engine import AlbumLayout, TrackRegion

_logger = logging.getLogger(__name__)

_LABEL_GETINFO_COMMAND = "GetInfo: Type=Labels Format=JSON"
ProgressCallback = Callable[[int, int], None]


@dataclass(frozen=True)
class RegionGenerationResult:
    """Outcome of generating every region in an :class:`AlbumLayout`."""

    success: bool
    message: str
    regions_created: int = 0


class AudacityRegionWriter:
    """Write :class:`AlbumLayout` regions into a running Audacity project."""

    def __init__(self, client: AudacityClient) -> None:
        self._client = client

    def create_regions(
        self,
        layout: AlbumLayout,
        *,
        progress_callback: ProgressCallback | None = None,
    ) -> RegionGenerationResult:
        """Create every region label defined by *layout*."""
        if not self._client.is_connected():
            msg = "Audacity client is not connected. Connect to Audacity first."
            return RegionGenerationResult(success=False, message=msg)

        if not layout.regions:
            return RegionGenerationResult(success=False, message="No regions to create.")

        total = len(layout.regions)
        created = 0

        try:
            for index, region in enumerate(layout.regions, start=1):
                self._create_region_label(region)
                created += 1
                if progress_callback is not None:
                    progress_callback(index, total)
        except AudacityError as exc:
            _logger.warning("Failed while creating Audacity regions: %s", exc)
            return RegionGenerationResult(
                success=False,
                message=str(exc),
                regions_created=created,
            )
        except (ValueError, json.JSONDecodeError) as exc:
            _logger.warning("Invalid Audacity response while creating regions: %s", exc)
            return RegionGenerationResult(
                success=False,
                message=str(exc),
                regions_created=created,
            )

        return RegionGenerationResult(
            success=True,
            message=f"Created {created} track region(s) in Audacity.",
            regions_created=created,
        )

    def _create_region_label(self, region: TrackRegion) -> None:
        """Create one named region label in Audacity."""
        labels_before = fetch_audacity_regions(self._client)
        label_index = len(labels_before)

        self._client.execute(
            f"SelectTime: Start={region.start_seconds} End={region.end_seconds}"
        )
        self._client.execute("AddLabel:")

        escaped_text = _escape_command_value(region.label_text)
        self._client.execute(
            f'SetLabel: Label={label_index} Text="{escaped_text}" '
            f"Start={region.start_seconds} End={region.end_seconds}"
        )
        _logger.debug(
            "Created region %r (%.3fs → %.3fs) at label index %d",
            region.label_text,
            region.start_seconds,
            region.end_seconds,
            label_index,
        )


def create_regions_from_layout(
    client: AudacityClient,
    layout: AlbumLayout,
    *,
    progress_callback: ProgressCallback | None = None,
) -> RegionGenerationResult:
    """Convenience wrapper around :class:`AudacityRegionWriter`."""
    return AudacityRegionWriter(client).create_regions(
        layout,
        progress_callback=progress_callback,
    )


def fetch_audacity_regions(client: AudacityClient) -> list[dict[str, object]]:
    """Return the current region labels from Audacity."""
    response = client.execute(_LABEL_GETINFO_COMMAND)
    payload = parse_json_response(response)
    return parse_labels_payload(payload)


def parse_labels_payload(payload: object) -> list[dict[str, object]]:
    """Normalize Audacity ``GetInfo: Type=Labels`` JSON into region dicts.

    Audacity returns label tracks as nested arrays::

        [[track_id, [[start, end, text], ...]], ...]

    Some responses may instead use object entries with ``start``, ``end``,
    and ``text`` keys. Both shapes are converted to a flat list of regions.
    """
    regions: list[dict[str, object]] = []

    if not isinstance(payload, list):
        return regions

    for item in payload:
        if isinstance(item, dict):
            regions.extend(_dict_label_entries(item))
            continue

        if not isinstance(item, list) or len(item) < 2:
            continue

        label_entries = item[1]
        if not isinstance(label_entries, list):
            continue

        for entry in label_entries:
            parsed = _array_label_entry(entry)
            if parsed is not None:
                regions.append(parsed)

    return regions


def _dict_label_entries(label: dict[str, object]) -> list[dict[str, object]]:
    text = label.get("text")
    start = label.get("start")
    end = label.get("end")
    if (
        isinstance(text, str)
        and isinstance(start, (int, float))
        and isinstance(end, (int, float))
    ):
        return [
            {
                "text": text,
                "start": float(start),
                "end": float(end),
            }
        ]
    return []


def _array_label_entry(entry: object) -> dict[str, object] | None:
    if not isinstance(entry, list) or len(entry) < 3:
        return None

    start = entry[0]
    end = entry[1]
    text = entry[2]
    if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
        return None

    return {
        "text": text if isinstance(text, str) else str(text),
        "start": float(start),
        "end": float(end),
    }


def _escape_command_value(value: str) -> str:
    """Escape a string for use inside Audacity command quotes."""
    return value.replace("\\", "\\\\").replace('"', '\\"')