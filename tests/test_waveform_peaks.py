"""Tests for waveform peak extraction."""

from __future__ import annotations

import struct
import wave
from pathlib import Path

from vinylsplit.waveform.peaks import load_peak_overview


def _write_sine_wav(path: Path, *, seconds: float = 1.0, rate: int = 8000) -> None:
    import math

    n = int(seconds * rate)
    frames = bytearray()
    for i in range(n):
        # Simple square-ish pattern for non-zero peaks
        sample = 10000 if (i // 40) % 2 == 0 else -10000
        frames += struct.pack("<h", sample)
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(bytes(frames))


def test_load_peak_overview_from_wav(tmp_path: Path) -> None:
    path = tmp_path / "tone.wav"
    _write_sine_wav(path, seconds=2.0)

    peaks = load_peak_overview(path, bucket_count=100)

    assert peaks.source == "wave"
    assert peaks.duration_seconds == 2.0
    assert peaks.bucket_count == 100
    assert not peaks.is_empty
    assert max(abs(v) for v in peaks.maxs) > 0


def test_missing_file_raises(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(FileNotFoundError):
        load_peak_overview(tmp_path / "nope.wav")
