"""Tests for WaveformWidget lattice drag and zoom."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent

from vinylsplit.labels.layout_engine import AlbumLayout, TrackRegion
from vinylsplit.waveform.peaks import PeakOverview
from vinylsplit.waveform.widget import WaveformWidget


def _layout_three() -> AlbumLayout:
    return AlbumLayout(
        release_id="r",
        artist_name="A",
        album_title="T",
        regions=(
            TrackRegion(0, "01", "One", "01 One", 0.0, 60.0),
            TrackRegion(1, "02", "Two", "02 Two", 60.0, 120.0),
            TrackRegion(2, "03", "Three", "03 Three", 120.0, 180.0),
        ),
    )


def _peaks(duration: float = 300.0) -> PeakOverview:
    n = 200
    return PeakOverview(
        path=Path("/tmp/x.wav"),
        duration_seconds=duration,
        sample_rate=8000,
        mins=tuple(-0.4 for _ in range(n)),
        maxs=tuple(0.4 for _ in range(n)),
        source="wave",
    )


def _mouse(w: WaveformWidget, etype, x: float, y: float = 100.0) -> None:
    local = QPointF(x, y)
    buttons = (
        Qt.MouseButton.LeftButton
        if etype != QEvent.Type.MouseButtonRelease
        else Qt.MouseButton.NoButton
    )
    event = QMouseEvent(
        etype,
        local,
        Qt.MouseButton.LeftButton,
        buttons,
        Qt.KeyboardModifier.NoModifier,
    )
    if etype == QEvent.Type.MouseButtonPress:
        w.mousePressEvent(event)
    elif etype == QEvent.Type.MouseMove:
        w.mouseMoveEvent(event)
    else:
        w.mouseReleaseEvent(event)


def test_hit_test_finds_marker(qtbot) -> None:
    w = WaveformWidget()
    qtbot.addWidget(w)
    w.resize(800, 220)
    w.show()
    w.set_peaks(_peaks())
    w.set_layout(_layout_three())
    qtbot.waitExposed(w)

    rect = w._content_rect()
    x = w._time_to_x(60.0, rect)
    assert w._hit_test_marker(x) == 1


def test_drag_track1_moves_all(qtbot) -> None:
    w = WaveformWidget()
    qtbot.addWidget(w)
    w.resize(900, 220)
    w.show()
    w.set_peaks(_peaks())
    w.set_layout(_layout_three())
    qtbot.waitExposed(w)

    received: list[AlbumLayout] = []
    w.layout_changed.connect(received.append)

    rect = w._content_rect()
    x0 = w._time_to_x(0.0, rect)
    x1 = w._time_to_x(10.0, rect)
    _mouse(w, QEvent.Type.MouseButtonPress, x0)
    _mouse(w, QEvent.Type.MouseMove, x1)
    _mouse(w, QEvent.Type.MouseButtonRelease, x1)

    assert received
    layout = received[-1]
    assert layout.regions[0].start_seconds == pytest.approx(10.0, abs=1.0)
    assert layout.regions[1].start_seconds == pytest.approx(70.0, abs=1.0)
    assert layout.regions[2].start_seconds == pytest.approx(130.0, abs=1.0)
    # Durations preserved for whole-lattice shift
    assert layout.regions[0].duration_seconds == pytest.approx(60.0, abs=0.5)


def test_drag_track2_keeps_track1(qtbot) -> None:
    w = WaveformWidget()
    qtbot.addWidget(w)
    w.resize(900, 220)
    w.show()
    w.set_peaks(_peaks())
    w.set_layout(_layout_three())
    qtbot.waitExposed(w)

    received: list[AlbumLayout] = []
    w.layout_changed.connect(received.append)

    rect = w._content_rect()
    x0 = w._time_to_x(60.0, rect)
    x1 = w._time_to_x(80.0, rect)
    _mouse(w, QEvent.Type.MouseButtonPress, x0)
    _mouse(w, QEvent.Type.MouseMove, x1)
    _mouse(w, QEvent.Type.MouseButtonRelease, x1)

    assert received
    layout = received[-1]
    assert layout.regions[0].start_seconds == pytest.approx(0.0, abs=0.5)
    assert layout.regions[0].end_seconds == pytest.approx(80.0, abs=1.5)
    assert layout.regions[1].start_seconds == pytest.approx(80.0, abs=1.5)
    assert layout.regions[2].start_seconds == pytest.approx(140.0, abs=1.5)


def test_nudge_all_moves_lattice(qtbot) -> None:
    w = WaveformWidget()
    qtbot.addWidget(w)
    w.set_layout(_layout_three())
    received: list[AlbumLayout] = []
    w.layout_changed.connect(received.append)

    w.nudge_all(5.0)

    assert received
    assert received[-1].regions[0].start_seconds == pytest.approx(5.0)
    assert received[-1].regions[1].start_seconds == pytest.approx(65.0)


def test_zoom_in_shortens_view(qtbot) -> None:
    w = WaveformWidget()
    qtbot.addWidget(w)
    w.set_peaks(_peaks(300.0))
    assert w.view_length == pytest.approx(300.0)
    w.zoom_in()
    assert w.view_length < 300.0
    w.zoom_fit()
    assert w.view_length == pytest.approx(300.0)
