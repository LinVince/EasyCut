"""Custom-painted timeline strip: select, scrub, and trim clips with the mouse."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ..timeline import Clip, Timeline

PALETTE = [
    "#a78bfa", "#7dd3fc", "#f9a8d4", "#86efac",
    "#fcd34d", "#fda4af", "#93c5fd", "#c4b5fd", "#6ee7b7",
]

PLAYHEAD_COLOR = "#f9a8d4"
BG = "#11111b"
BORDER = "#313244"


class TimelineWidget(QWidget):
    positionChanged = Signal(float)   # timeline seconds
    clipSelected = Signal(int)
    clipsChanged = Signal()

    def __init__(self, timeline: Timeline, parent=None):
        super().__init__(parent)
        self.timeline = timeline
        self.position = 0.0
        self.selected = -1
        self.setMinimumHeight(92)
        self.setMouseTracking(True)
        self._drag: str | None = None
        self._last_x = 0
        self.setToolTip(
            "Click a block to select it  -  drag its edges to trim  -  "
            "double-click to split  -  drag the playhead to scrub")

    # ------------------------------------------------------------ geometry

    def _geometry(self) -> tuple[dict, float, float, float]:
        w = self.width() - 16
        total = self.timeline.total()
        scale = (w / total) if total > 0 else 1.0
        rects: dict[int, QRectF] = {}
        y = 12
        h = max(40, self.height() - 26)
        acc = 0.0
        for i, c in enumerate(self.timeline.clips):
            x = 8 + acc * scale
            rw = max(6.0, c.duration * scale - 2)
            rects[i] = QRectF(x, y, rw, h)
            acc += c.duration
        return rects, scale, 8.0, 8.0 + w

    def _playhead_x(self) -> float:
        _, scale, x0, _ = self._geometry()
        total = self.timeline.total()
        if total <= 0:
            return x0
        return x0 + self.position * scale

    # ------------------------------------------------------------ paint

    def paintEvent(self, _ev) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rects, scale, x0, x1 = self._geometry()

        p.setPen(QPen(QColor(BORDER)))
        p.setBrush(QColor(BG))
        p.drawRoundedRect(QRectF(0, 0, self.width() - 1, self.height() - 1), 10, 10)

        if not self.timeline.clips:
            p.setPen(QColor("#565b73"))
            fm = QFontMetrics(p.font())
            p.drawText(QRectF(0, 0, self.width(), self.height()),
                       Qt.AlignmentFlag.AlignCenter,
                       "Timeline empty - load a video or run a tool to add clips")
            p.end()
            return

        y = rects[0].y()
        h = rects[0].height()
        for i, c in enumerate(self.timeline.clips):
            r = rects[i]
            color = QColor(PALETTE[i % len(PALETTE)])
            fill = QColor(color)
            fill.setAlpha(90 if i != self.selected else 160)
            p.setPen(Qt.PenStyle.NoPen if i != self.selected else QPen(color, 2))
            p.setBrush(fill)
            p.drawRoundedRect(r, 5, 5)
            if i == self.selected:
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor("#cdd6f4"), 2))
                p.drawRoundedRect(r.adjusted(0.5, 0.5, -0.5, -0.5), 5, 5)

            label = c.label or f"clip {i + 1}"
            if r.width() > 34:
                p.setPen(QColor("#1b1b2f"))
                p.setFont(self.font())
                p.drawText(r.adjusted(4, 0, -4, 0), Qt.AlignmentFlag.AlignCenter, label)

        px = self._playhead_x()
        if x0 <= px <= x1:
            p.setPen(QPen(QColor(PLAYHEAD_COLOR), 2))
            p.setBrush(QColor(PLAYHEAD_COLOR))
            tri = QRectF(px - 5, 0, 10, 6)
            p.drawPolygon([QPointF(tri.left(), tri.bottom()),
                           QPointF(tri.right(), tri.bottom()),
                           QPointF(tri.center().x(), tri.top())])
            p.drawLine(int(px), 6, int(px), int(y + h))
        p.end()

    # ------------------------------------------------------------ mouse

    def _hit_clip(self, x: float) -> int:
        rects, *_ = self._geometry()
        for i, r in rects.items():
            if r.adjusted(-2, 0, 2, 0).contains(QPointF(x, r.center().y())):
                return i
        return -1

    def _trim_target(self, x: float) -> str | None:
        if self.selected < 0:
            return None
        rects, *_ = self._geometry()
        r = rects.get(self.selected)
        if not r:
            return None
        if abs(x - r.left()) <= 7:
            return "trim-left"
        if abs(x - r.right()) <= 7:
            return "trim-right"
        return None

    def mousePressEvent(self, ev) -> None:
        x = ev.position().x()
        px = self._playhead_x()
        if abs(x - px) <= 7:
            self._drag = "playhead"
            self._last_x = x
            return
        tgt = self._trim_target(x)
        if tgt:
            self._drag = tgt
            _, scale, x0, _ = self._geometry()
            self._last_t = (x - x0) / scale if scale > 0 else 0.0
            return
        idx = self._hit_clip(x)
        if idx >= 0:
            self.set_selected(idx)
            self._drag = "select"
        else:
            self.set_selected(-1)
            self._scrub_from_x(x)
            self._drag = "select"
        self._last_x = x

    def mouseMoveEvent(self, ev) -> None:
        x = ev.position().x()
        if self._drag == "playhead":
            self._scrub_from_x(x)
        elif self._drag == "trim-left" or self._drag == "trim-right":
            self._trim_at_x(x)
        elif self._drag == "select":
            self._scrub_from_x(x)

    def mouseReleaseEvent(self, _ev) -> None:
        self._drag = None

    def mouseDoubleClickEvent(self, ev) -> None:
        x = ev.position().x()
        idx = self._hit_clip(x)
        if idx >= 0:
            self.set_selected(idx)
            self._scrub_from_x(x)
            idx2 = self.timeline.split(self.position)
            if idx2 >= 0:
                self.set_selected(idx2)
                self.clipsChanged.emit()

    # ------------------------------------------------------------ helpers

    def set_selected(self, idx: int) -> None:
        self.selected = idx
        self.update()
        self.clipSelected.emit(idx)

    def _scrub_from_x(self, x: float) -> None:
        _, scale, x0, _ = self._geometry()
        total = self.timeline.total()
        if total <= 0 or scale <= 0:
            return
        t = (x - x0) / scale
        t = max(0.0, min(total, t))
        self.set_position(t)
        self.positionChanged.emit(t)

    def _trim_at_x(self, x: float) -> None:
        if self.selected < 0:
            return
        c = self.timeline.clips[self.selected]
        _, scale, x0, _ = self._geometry()
        if scale <= 0:
            return
        t = (x - x0) / scale
        delta = t - self._last_t
        self._last_t = t
        if self._drag == "trim-left":
            hi = c.src_end - 0.2
            c.src_start = max(0.0, min(hi, c.src_start + delta))
        else:
            hi = c.src_dur if c.src_dur and c.src_dur > c.src_start else c.src_end + 10000
            c.src_end = max(c.src_start + 0.2, min(hi, c.src_end + delta))
        self.clipsChanged.emit()
        self.update()

    def set_position(self, t: float) -> None:
        self.position = max(0.0, t)
        self.update()

    def refresh(self) -> None:
        self.update()
