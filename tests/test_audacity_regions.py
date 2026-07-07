"""Tests for Audacity region label creation."""

from __future__ import annotations

import json
import re
from unittest.mock import MagicMock

from vinylsplit.labels.audacity_regions import (
    create_regions_from_layout,
    parse_labels_payload,
)
from vinylsplit.labels.layout_engine import AlbumLayout, LabelLayoutEngine, TrackRegion
from vinylsplit.metadata.models import (
    Artist,
    Medium,
    Release,
    Track,
)


def _sample_layout() -> AlbumLayout:
    release = Release(
        id="release-mbid-1",
        title="Test Album",
        artist=Artist(id="artist-mbid-1", name="Test Artist"),
        date="1973-03-01",
        country="GB",
        release_year="1973",
        release_type="Album",
        track_count=3,
        status="Official",
        media=(
            Medium(
                position=1,
                format="Vinyl",
                track_count=3,
                tracks=(
                    Track(
                        id="track-1",
                        title="Alpha",
                        position=1,
                        number="1",
                        length_ms=192_000,
                    ),
                    Track(
                        id="track-2",
                        title="Bravo",
                        position=2,
                        number="2",
                        length_ms=245_000,
                    ),
                    Track(
                        id="track-3",
                        title="Charlie",
                        position=3,
                        number="3",
                        length_ms=178_000,
                    ),
                ),
            ),
        ),
    )
    return LabelLayoutEngine().generate(release)


def test_parse_labels_payload_reads_audacity_nested_arrays() -> None:
    payload = [
        [
            1,
            [
                [0.0, 90.0, "01 Speak to Me"],
                [90.0, 253.0, "02 Breathe"],
            ],
        ]
    ]

    regions = parse_labels_payload(payload)

    assert regions == [
        {"text": "01 Speak to Me", "start": 0.0, "end": 90.0},
        {"text": "02 Breathe", "start": 90.0, "end": 253.0},
    ]


def test_parse_labels_payload_reads_object_entries() -> None:
    payload = [
        {"text": "01 Alpha", "start": 0.0, "end": 30.0},
    ]

    regions = parse_labels_payload(payload)

    assert regions == [
        {"text": "01 Alpha", "start": 0.0, "end": 30.0},
    ]


def test_create_regions_requires_connection() -> None:
    client = MagicMock()
    client.is_connected.return_value = False

    result = create_regions_from_layout(client, _sample_layout())

    assert result.success is False
    assert "not connected" in result.message.lower()


def test_create_regions_generates_every_region_label() -> None:
    layout = _sample_layout()
    label_tracks: list[list[object]] = []
    progress_updates: list[tuple[int, int]] = []

    def execute(command: str) -> str:
        if command.startswith("GetInfo:"):
            body = json.dumps(label_tracks)
            return f"{body}\nBatchCommand finished: OK\n\n"
        if command.startswith("SelectTime:"):
            return "BatchCommand finished: OK\n\n"
        if command == "AddLabel:":
            if not label_tracks:
                label_tracks.append([1, []])
            label_tracks[0][1].append([0.0, 0.0, ""])
            return "BatchCommand finished: OK\n\n"
        if command.startswith("SetLabel:"):
            match = re.search(
                r'SetLabel: Label=(\d+) Text="(.+)" Start=([\d.]+) End=([\d.]+)',
                command,
            )
            assert match is not None
            index = int(match.group(1))
            label_tracks[0][1][index] = [
                float(match.group(3)),
                float(match.group(4)),
                match.group(2),
            ]
            return "BatchCommand finished: OK\n\n"
        raise AssertionError(command)

    client = MagicMock()
    client.is_connected.return_value = True
    client.execute.side_effect = execute

    result = create_regions_from_layout(
        client,
        layout,
        progress_callback=lambda current, total: progress_updates.append(
            (current, total)
        ),
    )

    assert result.success is True
    assert result.regions_created == 3
    regions = parse_labels_payload(label_tracks)
    assert [region["text"] for region in regions] == [
        "01 Alpha",
        "02 Bravo",
        "03 Charlie",
    ]

    select_commands = [
        call.args[0]
        for call in client.execute.call_args_list
        if call.args and call.args[0].startswith("SelectTime:")
    ]
    assert select_commands == [
        "SelectTime: Start=0.0 End=192.0",
        "SelectTime: Start=192.0 End=437.0",
        "SelectTime: Start=437.0 End=615.0",
    ]
    assert progress_updates == [(1, 3), (2, 3), (3, 3)]


def test_track_region_duration_property() -> None:
    region = TrackRegion(
        track_index=0,
        track_number="01",
        title="Alpha",
        label_text="01 Alpha",
        start_seconds=0.0,
        end_seconds=192.0,
    )

    assert region.duration_seconds == 192.0