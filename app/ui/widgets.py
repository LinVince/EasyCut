"""Reusable UI widgets."""

from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ..utils import bgr_to_qimage, extract_frame


class FilePickerRow(QWidget):
    """Line edit + browse button (+ optional preview button)."""

    pathChanged = Signal(str)

    def __init__(self, title: str, filter: str = "Video files (*.mp4 *.mov *.mkv *.avi *.webm);;All files (*)",
                 preview: bool = False, parent=None):
        super().__init__(parent)
        self._filter = filter
        self._browse_btn = QPushButton("Browse...")
        self._browse_btn.clicked.connect(self._browse)
        self._edit = QLineEdit()
        self._edit.textChanged.connect(self.pathChanged)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lab = QLabel(title)
        lab.setMinimumWidth(90)
        lay.addWidget(lab)
        lay.addWidget(self._edit, 1)
        lay.addWidget(self._browse_btn)
        if preview:
            self._preview_btn = QPushButton("Preview")
            lay.addWidget(self._preview_btn)
        else:
            self._preview_btn = None

    def _browse(self) -> None:
        p, _ = QFileDialog.getOpenFileName(self, "Select file", "", self._filter)
        if p:
            self._edit.setText(p)

    def path(self) -> str:
        return self._edit.text().strip()

    def set_path(self, p: str) -> None:
        self._edit.setText(p)


class ColorPickButton(QWidget):
    colorChanged = Signal(tuple)

    def __init__(self, label: str, initial: tuple[int, int, int] = (0, 255, 0), parent=None):
        super().__init__(parent)
        self._color = tuple(initial)
        self._btn = QPushButton()
        self._btn.setFixedSize(56, 26)
        self._btn.clicked.connect(self._pick)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(QLabel(label))
        lay.addWidget(self._btn, 1)
        self._refresh()

    def _refresh(self) -> None:
        r, g, b = self._color
        self._btn.setStyleSheet(
            f"background-color: rgb({r},{g},{b}); border:2px solid #45475a;"
            f"border-radius:6px; min-height:20px;"
        )
        self._btn.setToolTip(f"RGB({r},{g},{b})  hex #{r:02X}{g:02X}{b:02X}")

    def _pick(self) -> None:
        col = QColorDialog.getColor(QColor(*self._color), self, "Pick background color")
        if col.isValid():
            self._color = (col.red(), col.green(), col.blue())
            self._refresh()
            self.colorChanged.emit(self._color)

    def color(self) -> tuple[int, int, int]:
        return self._color

    def set_color(self, c: tuple[int, int, int]) -> None:
        self._color = tuple(c)
        self._refresh()
        self.colorChanged.emit(self._color)


def _key_preview(frame: np.ndarray, bgr: tuple[int, int, int],
                 similarity: float, blend: float) -> np.ndarray:
    """Rough chroma-key preview using cv2.inRange (approx. of ffmpeg chromakey).

    Keyed (removed) pixels are filled with gray so you can see what will be cut.
    """
    out = frame.copy()
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    b, g, r = int(bgr[0]), int(bgr[1]), int(bgr[2])
    key_hsv = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0][0]
    tol = int(similarity * 180)
    htol = min(int(similarity * 60), 180)
    s_low = max(0, int(key_hsv[1]) - tol)
    s_high = min(255, int(key_hsv[1]) + tol)
    v_low = max(0, int(key_hsv[2]) - tol)
    v_high = min(255, int(key_hsv[2]) + tol)
    h_low = (int(key_hsv[0]) - htol) % 180
    h_high = (int(key_hsv[0]) + htol) % 180
    if h_low <= h_high:
        lower = np.array([h_low, s_low, v_low], dtype=np.uint8)
        upper = np.array([h_high, s_high, v_high], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)
    else:
        m1 = cv2.inRange(hsv, np.array([h_low, s_low, v_low], dtype=np.uint8), np.array([180, s_high, v_high], dtype=np.uint8))
        m2 = cv2.inRange(hsv, np.array([0, s_low, v_low], dtype=np.uint8), np.array([h_high, s_high, v_high], dtype=np.uint8))
        mask = cv2.bitwise_or(m1, m2)
    out[mask > 0] = (128, 128, 128)
    return out


def border_median(frame: np.ndarray) -> tuple[int, int, int]:
    """Median color of the frame edges (typical background). Returns (b, g, r)."""
    h, w = frame.shape[:2]
    th = max(2, h // 24)
    tw = max(2, w // 24)
    strips = np.concatenate([
        frame[0:th, :, :].reshape(-1, 3),
        frame[-th:, :, :].reshape(-1, 3),
        frame[:, 0:tw, :].reshape(-1, 3),
        frame[:, -tw:, :].reshape(-1, 3),
    ])
    med = np.median(strips, axis=0)
    return tuple(int(v) for v in med)


class ChromaKeyPickDialog(QDialog):
    """Pick key color by clicking a frame; preview keyed result live."""

    def __init__(self, path: str, time_sec: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pick chroma key color")
        self.resize(820, 560)
        self._frame = extract_frame(path, time_sec)
        self._key_color: tuple[int, int, int] = border_median(self._frame)
        self._similarity = 0.10
        self._blend = 0.1

        lay = QVBoxLayout(self)
        row = QHBoxLayout()
        self._orig_lbl = QLabel("Click the image to pick the key color")
        self._keyed_lbl = QLabel()
        row.addWidget(self._orig_lbl, 1)
        row.addWidget(self._keyed_lbl, 1)
        lay.addLayout(row)

        self._info = QLabel()
        lay.addWidget(self._info)

        sim_row = QHBoxLayout()
        sim_row.addWidget(QLabel("Similarity"))
        self._sim = QSlider(Qt.Orientation.Horizontal)
        self._sim.setRange(0, 100)
        self._sim.setValue(int(self._similarity * 100))
        self._sim.valueChanged.connect(self._repreview)
        sim_row.addWidget(self._sim, 1)
        lay.addLayout(sim_row)

        bl_row = QHBoxLayout()
        bl_row.addWidget(QLabel("Blend"))
        self._blend_sl = QSlider(Qt.Orientation.Horizontal)
        self._blend_sl.setRange(0, 100)
        self._blend_sl.setValue(int(self._blend * 100))
        self._blend_sl.valueChanged.connect(self._repreview)
        bl_row.addWidget(self._blend_sl, 1)
        lay.addLayout(bl_row)

        btns = QHBoxLayout()
        auto = QPushButton("Auto-detect background")
        auto.clicked.connect(self._auto_detect)
        btns.addWidget(auto)
        btns.addStretch(1)
        ok = QPushButton("Apply")
        ok.setProperty("accent", True)
        ok.clicked.connect(self.accept)
        btns.addWidget(ok)
        lay.addLayout(btns)

        self._show_frames()

    def _auto_detect(self) -> None:
        self._key_color = border_median(self._frame)
        self._show_frames()

    def _show_frames(self) -> None:
        pix = self._pixmap_for(self._frame)
        self._orig_lbl.setPixmap(pix)
        self._keyed_lbl.setPixmap(self._pixmap_for(_key_preview(
            self._frame, self._key_color, self._similarity, self._blend)))
        b, g, r = self._key_color
        self._info.setText(
            f"Key color RGB({r},{g},{b}) hex #{r:02X}{g:02X}{b:02X}   "
            f"similarity {self._similarity:.2f}  blend {self._blend:.2f}\n"
            "Click the background in the left image to pick it, "
            "then check the right preview shows it turning gray. "
            "If the subject turns gray too, lower Similarity.")

    def _pixmap_for(self, frame: np.ndarray) -> QPixmap:
        qimg = bgr_to_qimage(frame)
        return QPixmap.fromImage(qimg).scaled(
            380, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def _repreview(self) -> None:
        self._similarity = self._sim.value() / 100.0
        self._blend = self._blend_sl.value() / 100.0
        self._show_frames()

    def mousePressEvent(self, ev):
        if self._orig_lbl.geometry().contains(ev.position().toPoint()):
            pos = ev.position().toPoint() - self._orig_lbl.geometry().topLeft()
            pm = self._orig_lbl.pixmap()
            if pm:
                scale = pm.width() / self._frame.shape[1]
                x = min(self._frame.shape[1] - 1, max(0, int(pos.x() / scale)))
                y = min(self._frame.shape[0] - 1, max(0, int(pos.y() / scale)))
                b, g, r = (int(v) for v in self._frame[y, x])
                self._key_color = (b, g, r)
                self._repreview()
        super().mousePressEvent(ev)

    def values(self) -> tuple[tuple[int, int, int], float, float]:
        return self._key_color, self._similarity, self._blend
