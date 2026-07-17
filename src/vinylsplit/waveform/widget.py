"""Interactive waveform overview with linked lattice markers and zoom."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QWheelEvent,
)
from PySide6.QtWidgets import QSizePolicy, QWidget

from vinylsplit.labels.layout_engine import AlbumLayout
from vinylsplit.labels.time_format import format_position
from vinylsplit.waveform.peaks import PeakOverview

_MARKER_HIT_PX = 22
_HANDLE_RADIUS = 8
_MIN_HEIGHT = 180
_MIN_VIEW_SECONDS = 2.0


class WaveformWidget(QWidget):
    """Peak overview with draggable lattice markers.

    Drag semantics (contiguous lattice):

    - **Track 1 (index 0):** move the whole lattice (all tracks shift).
    - **Track N (index > 0):** tracks before N stay put; N and everything after
      shift together (track N-1 is stretched/shrunk to meet the new split).

    Nudge buttons / arrow keys always shift the whole lattice (index 0).
    """

    #: Emitted with an :class:`AlbumLayout` while dragging.
    layout_preview = Signal(object)
    #: Emitted with the final :class:`AlbumLayout` on release / nudge.
    layout_changed = Signal(object)
    view_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._peaks: PeakOverview | None = None
        # Working absolute lattice (source of truth for drawing + drag).
        self._layout: AlbumLayout | None = None

        self._full_duration = 1.0
        self._view_start = 0.0
        self._view_length = 1.0

        self._dragging = False
        self._drag_index = 0
        self._drag_press_x = 0.0
        self._drag_origin_layout: AlbumLayout | None = None

        self._panning = False
        self._pan_start_x = 0.0
        self._pan_origin_start = 0.0

        self._message = (
            "Open a source audio file on the Welcome page to see the waveform."
        )
        self._hover_index: int | None = None

        self.setMinimumHeight(_MIN_HEIGHT)
        self.setMaximumHeight(300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    # -- Public API ----------------------------------------------------------

    def set_message(self, message: str) -> None:
        self._message = message
        self.update()

    def set_peaks(self, peaks: PeakOverview | None) -> None:
        self._peaks = peaks
        if peaks is not None and peaks.duration_seconds > 0:
            self._full_duration = max(self._full_duration, peaks.duration_seconds)
            if self._view_start == 0.0 and (
                self._view_length <= 1.0
                or abs(self._view_length - peaks.duration_seconds) < 0.01
            ):
                self._view_start = 0.0
                self._view_length = peaks.duration_seconds
        self.update()
        self.view_changed.emit()

    def set_layout(self, layout: AlbumLayout | None) -> None:
        """Set the working absolute lattice (ignored while dragging)."""
        if self._dragging:
            return
        self._layout = layout
        self._sync_full_duration()
        self.update()

    def nudge_all(self, delta_seconds: float) -> None:
        """Shift the entire lattice (same as dragging track 1)."""
        if self._layout is None:
            return
        self._layout = self._layout.shift_from_index(0, float(delta_seconds))
        self.update()
        self.layout_preview.emit(self._layout)
        self.layout_changed.emit(self._layout)

    def set_view_window(self, start: float, length: float) -> None:
        self._view_start, self._view_length = self._clamp_view(start, length)
        self.update()
        self.view_changed.emit()

    def zoom_in(self, *, factor: float = 1.6) -> None:
        self._zoom_at(self._view_start + self._view_length / 2.0, factor)

    def zoom_out(self, *, factor: float = 1.6) -> None:
        self._zoom_at(self._view_start + self._view_length / 2.0, 1.0 / factor)

    def zoom_fit(self) -> None:
        self._view_start = 0.0
        self._view_length = max(_MIN_VIEW_SECONDS, self._full_duration)
        self.update()
        self.view_changed.emit()

    def zoom_to_markers(self) -> None:
        layout = self._layout
        if layout is None or not layout.regions:
            self.zoom_fit()
            return
        start = layout.regions[0].start_seconds
        end = max(layout.regions[-1].end_seconds, start + _MIN_VIEW_SECONDS)
        span = max(_MIN_VIEW_SECONDS, end - start)
        pad = span * 0.1
        self.set_view_window(max(0.0, start - pad), span + 2 * pad)

    @property
    def view_start(self) -> float:
        return self._view_start

    @property
    def view_length(self) -> float:
        return self._view_length

    @property
    def full_duration(self) -> float:
        return self._full_duration

    @property
    def current_layout(self) -> AlbumLayout | None:
        return self._layout

    def _sync_full_duration(self) -> None:
        if self._layout is not None and self._layout.total_duration_seconds > 0:
            self._full_duration = max(
                self._full_duration,
                self._layout.total_duration_seconds + 1.0,
            )
            if self._peaks is None and self._view_length <= 1.0:
                self._view_start = 0.0
                self._view_length = self._full_duration

    # -- Painting ------------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self._content_rect()
        if rect.width() < 4 or rect.height() < 4:
            return

        painter.fillRect(self.rect(), QColor(28, 28, 32))
        painter.fillRect(rect, QColor(16, 16, 20))

        if self._peaks is not None and not self._peaks.is_empty:
            self._draw_waveform(painter, rect)
        else:
            painter.setPen(QColor(190, 190, 200))
            painter.drawText(
                rect.toRect(),
                int(Qt.AlignmentFlag.AlignCenter),
                self._message or "No waveform — drag markers or use nudge buttons.",
            )

        self._draw_hit_hints(painter, rect)
        self._draw_markers(painter, rect)
        self._draw_time_axis(painter, rect)
        self._draw_view_caption(painter)

    def _draw_hit_hints(self, painter: QPainter, rect: QRectF) -> None:
        layout = self._layout
        if layout is None:
            return
        for region in layout.regions:
            x = self._time_to_x(region.start_seconds, rect)
            if x < rect.left() - 2 or x > rect.right() + 2:
                continue
            strip = QRectF(
                x - _MARKER_HIT_PX / 2, rect.top(), _MARKER_HIT_PX, rect.height()
            )
            painter.fillRect(strip, QColor(255, 200, 80, 28))

    def _draw_waveform(self, painter: QPainter, rect: QRectF) -> None:
        assert self._peaks is not None
        peaks = self._peaks
        n = peaks.bucket_count
        if n == 0 or self._view_length <= 0:
            return

        mid_y = rect.center().y()
        half_h = rect.height() / 2.0 * 0.90
        full = max(peaks.duration_seconds, 1e-6)
        peak_amp = max(
            1e-6,
            max(abs(v) for v in peaks.mins),
            max(abs(v) for v in peaks.maxs),
        )
        peak_amp = peak_amp**0.85

        t0 = self._view_start
        t1 = self._view_start + self._view_length
        i0 = max(0, int(t0 / full * n))
        i1 = min(n, int(t1 / full * n) + 1)
        if i1 <= i0:
            i1 = min(n, i0 + 1)

        path = QPainterPath()
        xs: list[float] = []
        tops: list[float] = []
        bots: list[float] = []
        first = True
        for i in range(i0, i1):
            bt = (i + 0.5) / n * full
            x = self._time_to_x(bt, rect)
            amp = max(abs(peaks.mins[i]), abs(peaks.maxs[i])) / peak_amp
            amp = min(1.0, amp**0.65)
            y_top = mid_y - amp * half_h
            y_bot = mid_y + amp * half_h
            xs.append(x)
            tops.append(y_top)
            bots.append(y_bot)
            if first:
                path.moveTo(x, y_top)
                first = False
            else:
                path.lineTo(x, y_top)
        for x, y_bot in zip(reversed(xs), reversed(bots), strict=True):
            path.lineTo(x, y_bot)
        path.closeSubpath()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(64, 160, 255, 175))
        painter.drawPath(path)
        pen = QPen(QColor(160, 210, 255, 230))
        pen.setWidth(1)
        painter.setPen(pen)
        for x, y_top, y_bot in zip(xs, tops, bots, strict=True):
            painter.drawLine(QPointF(x, y_top), QPointF(x, y_bot))
        painter.setPen(QPen(QColor(70, 70, 80)))
        painter.drawLine(int(rect.left()), int(mid_y), int(rect.right()), int(mid_y))

    def _draw_markers(self, painter: QPainter, rect: QRectF) -> None:
        layout = self._layout
        if layout is None or not layout.regions:
            return

        font = QFont(self.font())
        font.setBold(True)
        font.setPointSize(max(9, font.pointSize()))
        painter.setFont(font)

        for index, region in enumerate(layout.regions):
            x = self._time_to_x(region.start_seconds, rect)
            if x < rect.left() - 24 or x > rect.right() + 24:
                continue

            is_active = index == self._hover_index or (
                self._dragging and index == self._drag_index
            )
            is_first = index == 0
            color = QColor(255, 200, 50) if is_first else QColor(255, 100, 85)
            if is_active or (self._dragging and index >= self._drag_index):
                # Highlight the moving segment of the lattice
                color = QColor(255, 255, 140) if is_first else QColor(255, 170, 150)

            pen = QPen(color)
            pen.setWidth(4 if is_active or self._dragging else 3)
            painter.setPen(pen)
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))

            r = _HANDLE_RADIUS + (3 if is_active else 0)
            painter.setBrush(color)
            painter.setPen(QPen(QColor(10, 10, 12), 2))
            painter.drawEllipse(QPointF(x, rect.top() + r + 4), r, r)

            painter.setPen(QColor(255, 255, 255))
            painter.drawText(int(x) + 10, int(rect.top()) + 16, region.track_number)

        last = layout.regions[-1]
        x_end = self._time_to_x(last.end_seconds, rect)
        if rect.left() - 5 <= x_end <= rect.right() + 5:
            pen = QPen(QColor(170, 170, 190))
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(int(x_end), int(rect.top()), int(x_end), int(rect.bottom()))

    def _draw_time_axis(self, painter: QPainter, rect: QRectF) -> None:
        if self._view_length <= 0:
            return
        painter.setPen(QColor(165, 165, 175))
        font = QFont(self.font())
        font.setPointSize(max(8, font.pointSize() - 1))
        painter.setFont(font)
        steps = 8
        for i in range(steps + 1):
            t = self._view_start + self._view_length * i / steps
            x = self._time_to_x(t, rect)
            painter.drawLine(int(x), int(rect.bottom()), int(x), int(rect.bottom()) + 5)
            painter.drawText(int(x) - 18, int(rect.bottom()) + 18, format_position(t))

    def _draw_view_caption(self, painter: QPainter) -> None:
        painter.setPen(QColor(155, 155, 165))
        font = QFont(self.font())
        font.setPointSize(max(8, font.pointSize() - 1))
        painter.setFont(font)
        t1 = 0.0
        if self._layout and self._layout.regions:
            t1 = self._layout.regions[0].start_seconds
        text = (
            f"T1 @ {format_position(t1)} · "
            f"{format_position(self._view_start)}–"
            f"{format_position(self._view_start + self._view_length)} · "
            "drag handle: T1=all · TN=from N on · wheel=zoom"
        )
        painter.drawText(12, self.height() - 4, text)

    # -- Geometry ------------------------------------------------------------

    def _content_rect(self) -> QRectF:
        return QRectF(self.rect().adjusted(10, 12, -10, -28))

    def _time_to_x(self, seconds: float, rect: QRectF) -> float:
        if self._view_length <= 0:
            return float(rect.left())
        ratio = (seconds - self._view_start) / self._view_length
        return float(rect.left() + ratio * rect.width())

    def _x_to_time(self, x: float, rect: QRectF) -> float:
        if rect.width() <= 0 or self._view_length <= 0:
            return self._view_start
        ratio = (x - rect.left()) / rect.width()
        return self._view_start + ratio * self._view_length

    def _event_x(self, event: QMouseEvent) -> float:
        if hasattr(event, "position"):
            return float(event.position().x())
        return float(event.localPos().x())

    def _event_y(self, event: QMouseEvent) -> float:
        if hasattr(event, "position"):
            return float(event.position().y())
        return float(event.localPos().y())

    def _hit_test_marker(self, x: float) -> int | None:
        layout = self._layout
        if layout is None:
            return None
        rect = self._content_rect()
        best: int | None = None
        best_dist = float(_MARKER_HIT_PX)
        for index, region in enumerate(layout.regions):
            mx = self._time_to_x(region.start_seconds, rect)
            if mx < rect.left() - _MARKER_HIT_PX or mx > rect.right() + _MARKER_HIT_PX:
                continue
            dist = abs(mx - x)
            if dist <= best_dist:
                best_dist = dist
                best = index
        return best

    def _clamp_view(self, start: float, length: float) -> tuple[float, float]:
        full = max(self._full_duration, _MIN_VIEW_SECONDS)
        length = min(max(length, _MIN_VIEW_SECONDS), full)
        start = max(0.0, min(start, max(0.0, full - length)))
        return start, length

    def _zoom_at(self, anchor_time: float, factor: float) -> None:
        new_length = self._view_length / factor
        if self._view_length > 0:
            rel = (anchor_time - self._view_start) / self._view_length
        else:
            rel = 0.5
        new_start = anchor_time - rel * new_length
        self._view_start, self._view_length = self._clamp_view(new_start, new_length)
        self.update()
        self.view_changed.emit()

    def _apply_drag_to(self, x: float) -> None:
        if self._drag_origin_layout is None:
            return
        rect = self._content_rect()
        t0 = self._x_to_time(self._drag_press_x, rect)
        t1 = self._x_to_time(x, rect)
        delta = t1 - t0
        self._layout = self._drag_origin_layout.shift_from_index(self._drag_index, delta)
        self.update()
        self.layout_preview.emit(self._layout)

    def _end_drag(self, x: float) -> None:
        if not self._dragging:
            return
        self._apply_drag_to(x)
        final = self._layout
        self._dragging = False
        self._drag_origin_layout = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()
        if final is not None:
            self.layout_changed.emit(final)

    # -- Mouse / wheel / keys ------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        x = self._event_x(event)
        button = event.button()

        if button == Qt.MouseButton.MiddleButton or (
            button == Qt.MouseButton.LeftButton
            and bool(event.modifiers() & Qt.KeyboardModifier.AltModifier)
        ):
            self._panning = True
            self._pan_start_x = x
            self._pan_origin_start = self._view_start
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        if button != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        idx = self._hit_test_marker(x)
        if idx is None or self._layout is None:
            super().mousePressEvent(event)
            return

        self._dragging = True
        self._drag_index = idx
        self._drag_press_x = x
        self._drag_origin_layout = self._layout
        self._hover_index = idx
        self.setCursor(Qt.CursorShape.SizeHorCursor)
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        self.update()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        x = self._event_x(event)
        rect = self._content_rect()
        buttons = event.buttons()

        if self._panning and buttons & (
            Qt.MouseButton.MiddleButton | Qt.MouseButton.LeftButton
        ):
            dx = x - self._pan_start_x
            if rect.width() > 0:
                dt = -dx / rect.width() * self._view_length
                self._view_start, self._view_length = self._clamp_view(
                    self._pan_origin_start + dt,
                    self._view_length,
                )
                self.update()
                self.view_changed.emit()
            event.accept()
            return

        if self._dragging and buttons & Qt.MouseButton.LeftButton:
            self._apply_drag_to(x)
            event.accept()
            return

        if self._dragging and not (buttons & Qt.MouseButton.LeftButton):
            self._end_drag(x)
            event.accept()
            return

        idx = self._hit_test_marker(x)
        if idx != self._hover_index:
            self._hover_index = idx
            self.update()
        self.setCursor(
            Qt.CursorShape.SizeHorCursor
            if idx is not None
            else Qt.CursorShape.ArrowCursor
        )
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        x = self._event_x(event)

        if self._panning and event.button() in {
            Qt.MouseButton.MiddleButton,
            Qt.MouseButton.LeftButton,
        }:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._end_drag(x)
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        key = event.key()
        step = 1.0
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            step = 0.1
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            step = 5.0
        if key == Qt.Key.Key_Left:
            self.nudge_all(-step)
            event.accept()
            return
        if key == Qt.Key.Key_Right:
            self.nudge_all(step)
            event.accept()
            return
        super().keyPressEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        delta = event.angleDelta().y()
        if delta == 0:
            super().wheelEvent(event)
            return
        rect = self._content_rect()
        x = float(event.position().x()) if hasattr(event, "position") else 0.0
        anchor = self._x_to_time(x, rect)
        factor = 1.25 if delta > 0 else 1.0 / 1.25
        self._zoom_at(anchor, factor)
        event.accept()

    def leaveEvent(self, event) -> None:  # noqa: N802
        del event
        if not self._dragging and not self._panning:
            self._hover_index = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()
