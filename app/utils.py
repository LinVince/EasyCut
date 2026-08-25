"""Small shared helpers."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def format_time(sec: float) -> str:
    sec = max(0.0, sec)
    h = int(sec // 3600)
    m = int(sec % 3600 // 60)
    s = int(sec % 60)
    ms = int((sec - int(sec)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def extract_frame(path: str | Path, time_sec: float) -> np.ndarray:
    """Grab a BGR frame at the given time."""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video: {path}")
    try:
        cap.set(cv2.CAP_PROP_POS_MSEC, time_sec * 1000.0)
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError("could not read frame")
        return frame
    finally:
        cap.release()


def bgr_to_qimage(bgr: np.ndarray) -> "QImage":
    from PySide6.QtGui import QImage

    h, w = bgr.shape[:2]
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    qimg = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format.Format_RGB888).copy()
    return qimg
