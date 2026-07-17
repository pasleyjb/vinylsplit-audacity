"""Build a lightweight peak overview of an audio file for drawing."""

from __future__ import annotations

import logging
import struct
import subprocess
import wave
from array import array
from dataclasses import dataclass
from pathlib import Path

_logger = logging.getLogger(__name__)

# Target number of peak columns for a full-file overview.
DEFAULT_BUCKET_COUNT = 4000
# Downsampled rate when decoding via ffmpeg (enough for overview).
_FFMPEG_RATE = 12000


@dataclass(frozen=True)
class PeakOverview:
    """Min/max amplitude columns for a mono overview of an audio file."""

    path: Path
    duration_seconds: float
    sample_rate: int
    mins: tuple[float, ...]
    maxs: tuple[float, ...]
    source: str  # wave | ffmpeg | empty

    @property
    def bucket_count(self) -> int:
        return len(self.mins)

    @property
    def is_empty(self) -> bool:
        return self.bucket_count == 0 or self.duration_seconds <= 0


def load_peak_overview(
    path: Path | str,
    *,
    bucket_count: int = DEFAULT_BUCKET_COUNT,
) -> PeakOverview:
    """Load peak mins/maxes for *path*.

    Prefers the stdlib ``wave`` module for ``.wav`` files. Falls back to
    ``ffmpeg`` (if installed) for other formats or when wave fails.
    """
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        msg = f"Audio file not found: {resolved}"
        raise FileNotFoundError(msg)

    buckets = max(16, int(bucket_count))

    if resolved.suffix.lower() == ".wav":
        try:
            return _load_via_wave(resolved, buckets)
        except Exception as exc:  # noqa: BLE001
            _logger.info("wave decode failed for %s (%s); trying ffmpeg", resolved, exc)

    try:
        return _load_via_ffmpeg(resolved, buckets)
    except Exception as exc:  # noqa: BLE001
        _logger.warning("Could not build waveform for %s: %s", resolved, exc)
        return PeakOverview(
            path=resolved,
            duration_seconds=0.0,
            sample_rate=0,
            mins=(),
            maxs=(),
            source="empty",
        )


def _load_via_wave(path: Path, bucket_count: int) -> PeakOverview:
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        sample_width = handle.getsampwidth()
        sample_rate = handle.getframerate()
        frame_count = handle.getnframes()
        if sample_rate <= 0 or frame_count <= 0:
            msg = "WAV file has no audio frames"
            raise ValueError(msg)

        duration = frame_count / float(sample_rate)
        # Read in chunks to limit memory on long vinyl captures.
        frames_per_bucket = max(1, frame_count // bucket_count)
        mins: list[float] = []
        maxs: list[float] = []
        frames_read = 0

        while frames_read < frame_count and len(mins) < bucket_count:
            to_read = min(frames_per_bucket, frame_count - frames_read)
            raw = handle.readframes(to_read)
            if not raw:
                break
            samples = _pcm_to_mono_floats(raw, sample_width, channels)
            if samples:
                mins.append(min(samples))
                maxs.append(max(samples))
            else:
                mins.append(0.0)
                maxs.append(0.0)
            frames_read += to_read

        # Pad if short
        while len(mins) < bucket_count:
            mins.append(0.0)
            maxs.append(0.0)

        return PeakOverview(
            path=path,
            duration_seconds=duration,
            sample_rate=sample_rate,
            mins=tuple(mins[:bucket_count]),
            maxs=tuple(maxs[:bucket_count]),
            source="wave",
        )


def _load_via_ffmpeg(path: Path, bucket_count: int) -> PeakOverview:
    """Decode mono f32le via ffmpeg and bucket peaks."""
    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        str(path),
        "-ac",
        "1",
        "-ar",
        str(_FFMPEG_RATE),
        "-f",
        "f32le",
        "-acodec",
        "pcm_f32le",
        "pipe:1",
    ]
    try:
        proc = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            timeout=120,
        )
    except FileNotFoundError as exc:
        msg = "ffmpeg is not installed; cannot decode this audio format"
        raise RuntimeError(msg) from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or b"").decode("utf-8", errors="replace")[:200]
        msg = f"ffmpeg failed to decode audio: {detail}"
        raise RuntimeError(msg) from exc

    raw = proc.stdout
    if len(raw) < 4:
        msg = "ffmpeg returned no audio samples"
        raise ValueError(msg)

    sample_count = len(raw) // 4
    samples = struct.unpack(f"<{sample_count}f", raw[: sample_count * 4])
    duration = sample_count / float(_FFMPEG_RATE)
    mins, maxs = _bucket_samples(samples, bucket_count)

    return PeakOverview(
        path=path,
        duration_seconds=duration,
        sample_rate=_FFMPEG_RATE,
        mins=tuple(mins),
        maxs=tuple(maxs),
        source="ffmpeg",
    )


def _pcm_to_mono_floats(raw: bytes, sample_width: int, channels: int) -> list[float]:
    if sample_width == 1:
        # Unsigned 8-bit
        values = array("B")
        values.frombytes(raw)
        signed = [(v - 128) / 128.0 for v in values]
    elif sample_width == 2:
        values = array("h")
        values.frombytes(raw)
        signed = [v / 32768.0 for v in values]
    elif sample_width == 3:
        signed = []
        for i in range(0, len(raw) - 2, 3):
            b0, b1, b2 = raw[i], raw[i + 1], raw[i + 2]
            val = b0 | (b1 << 8) | (b2 << 16)
            if val & 0x800000:
                val -= 0x1000000
            signed.append(val / 8388608.0)
    elif sample_width == 4:
        values = array("i")
        values.frombytes(raw)
        signed = [v / 2147483648.0 for v in values]
    else:
        return []

    if channels <= 1:
        return signed

    mono: list[float] = []
    for i in range(0, len(signed) - channels + 1, channels):
        chunk = signed[i : i + channels]
        mono.append(sum(chunk) / channels)
    return mono


def _bucket_samples(
    samples: tuple[float, ...] | list[float],
    bucket_count: int,
) -> tuple[list[float], list[float]]:
    if not samples:
        return [0.0] * bucket_count, [0.0] * bucket_count

    n = len(samples)
    per = max(1, n // bucket_count)
    mins: list[float] = []
    maxs: list[float] = []
    for i in range(bucket_count):
        start = i * per
        end = n if i == bucket_count - 1 else min(n, start + per)
        if start >= n:
            mins.append(0.0)
            maxs.append(0.0)
            continue
        window = samples[start:end]
        mins.append(min(window))
        maxs.append(max(window))
    return mins, maxs
