"""Dark modern theme (QSS) for the whole application."""

from __future__ import annotations

from pathlib import Path

RES = Path(__file__).resolve().parent / "resources"

_STYLE = """
/* =========================== base =========================== */
* {
    outline: none;
    font-family: "Segoe UI";
    font-size: 13px;
    color: #cdd6f4;
}

QMainWindow, QDialog, QMessageBox {
    background-color: #181825;
}

/* =========================== header =========================== */
QWidget#AppHeader {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0   #1a1040,
        stop:0.3 #2d1b69,
        stop:0.6 #4c1d95,
        stop:1   #1a1040);
    border-bottom: 1px solid #5b21b6;
}
QLabel#AppTitle {
    font-size: 26px;
    font-weight: 800;
    letter-spacing: 2px;
    color: #e9d5ff;
    background: transparent;
}
QLabel#AppTagline {
    font-size: 12px;
    color: #a78bfa;
    background: transparent;
}
QLabel#AppBadge {
    color: #1a1040; font-weight: 800; font-size: 11px;
    border: none; border-radius: 11px;
    padding: 4px 14px;
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #c084fc, stop:1 #818cf8);
}

/* =========================== tabs =========================== */
QTabWidget::pane {
    border: 1px solid #2a2a3c;
    background-color: #1e1e2e;
    border-radius: 14px;
    top: -1px;
    padding: 12px;
}
QTabBar {
    background: transparent;
}
QTabBar::tab {
    background: transparent;
    color: #6272a4;
    padding: 10px 20px;
    margin-right: 4px;
    font-weight: 700;
    font-size: 12px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    border-bottom: 2px solid transparent;
}
QTabBar::tab:hover:!selected {
    color: #c4b5fd;
    background-color: rgba(139, 92, 246, 0.06);
}
QTabBar::tab:selected {
    color: #f5f3ff;
    background-color: #1e1e2e;
    border-bottom: 3px solid #a78bfa;
}

/* =========================== buttons =========================== */
QPushButton {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #2d2d42, stop:1 #24243a);
    color: #cdd6f4;
    border: 1px solid #3b3b58;
    border-radius: 8px;
    padding: 7px 16px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #3d3d58, stop:1 #333350);
    border-color: #6d6d96;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #3b3b58;
    color: #ffffff;
}
QPushButton:disabled {
    color: #4a4a66;
    background-color: #1e1e2e;
    border-color: #2a2a3c;
}

QPushButton[accent="true"] {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #a855f7, stop:0.5 #8b5cf6, stop:1 #7c3aed);
    color: #ffffff;
    border: none;
    padding: 9px 24px;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
QPushButton[accent="true"]:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #c084fc, stop:0.5 #a78bfa, stop:1 #8b5cf6);
    color: #ffffff;
}
QPushButton[accent="true"]:pressed {
    background-color: #7c3aed;
    color: #ffffff;
}
QPushButton[accent="true"]:disabled {
    background-color: #2d2244;
    color: #5a4a72;
}

QPushButton[flat="true"] {
    background: transparent;
    border: none;
}
QPushButton[flat="true"]:hover {
    background-color: rgba(167, 139, 250, 0.08);
    border: none;
}

QPushButton#PlayButton {
    border: none;
    border-radius: 20px;
    min-width: 40px; max-width: 40px;
    min-height: 40px; max-height: 40px;
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #a855f7, stop:1 #7c3aed);
    color: #ffffff;
    font-size: 16px;
}
QPushButton#PlayButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #c084fc, stop:1 #8b5cf6);
}
QPushButton#PlayButton:pressed {
    background-color: #6d28d9;
}

/* =========================== inputs =========================== */
QLineEdit {
    background-color: #13131f;
    border: 1px solid #2d2d44;
    border-radius: 8px;
    padding: 7px 12px;
    selection-background-color: #5b21b6;
    color: #e2e8f0;
}
QLineEdit:hover {
    border-color: #5b21b6;
}
QLineEdit:focus {
    border-color: #a78bfa;
    background-color: #16162a;
}

QComboBox {
    background-color: #13131f;
    border: 1px solid #2d2d44;
    border-radius: 8px;
    padding: 7px 12px;
    color: #e2e8f0;
}
QComboBox:hover {
    border-color: #5b21b6;
}
QComboBox:focus {
    border-color: #a78bfa;
}
QComboBox::drop-down {
    border: none;
    width: 28px;
}
QComboBox::down-arrow {
    image: url(__RES__/chevron.svg);
    width: 10px;
    height: 6px;
}
QComboBox QAbstractItemView {
    background-color: #1e1e2e;
    border: 1px solid #3b3b58;
    border-radius: 8px;
    padding: 6px;
    selection-background-color: #5b21b6;
    selection-color: #f5f3ff;
    outline: 0;
}

QSpinBox, QDoubleSpinBox {
    background-color: #13131f;
    border: 1px solid #2d2d44;
    border-radius: 8px;
    padding: 6px 10px;
    color: #e2e8f0;
}
QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #5b21b6;
}
QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #a78bfa;
    background-color: #16162a;
}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background: transparent;
    border: none;
    width: 18px;
}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow,
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    background: none;
}

/* =========================== sliders =========================== */
QSlider::groove:horizontal {
    height: 8px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #313244, stop:1 #3b3b58);
    border-radius: 4px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c3aed, stop:1 #a78bfa);
    border-radius: 4px;
}
QSlider::add-page:horizontal {
    background: #24243a;
    border-radius: 4px;
}
QSlider::handle:horizontal {
    width: 18px; height: 18px;
    margin: -5px 0;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #e9d5ff, stop:1 #c084fc);
    border-radius: 9px;
    border: 2px solid #7c3aed;
}
QSlider::handle:horizontal:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #ffffff, stop:1 #e9d5ff);
    border-color: #a855f7;
}

/* =========================== checkbox =========================== */
QCheckBox {
    spacing: 8px;
    color: #cdd6f4;
}
QCheckBox::indicator {
    width: 18px; height: 18px;
    border: 2px solid #3b3b58;
    border-radius: 6px;
    background-color: #13131f;
}
QCheckBox::indicator:hover {
    border-color: #a78bfa;
}
QCheckBox::indicator:checked {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #a855f7, stop:1 #7c3aed);
    border-color: #a855f7;
    image: url(__RES__/check.svg);
}

/* =========================== progress =========================== */
QProgressBar {
    background-color: #24243a;
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0   #7c3aed,
        stop:0.4 #a78bfa,
        stop:0.6 #c084fc,
        stop:1   #7c3aed);
    border-radius: 6px;
}

/* =========================== group box =========================== */
QGroupBox {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #22223a, stop:1 #1e1e30);
    border: 1px solid #2d2d4a;
    border-radius: 12px;
    margin-top: 16px;
    padding: 14px 10px 10px 10px;
    font-weight: 700;
    font-size: 13px;
    color: #c4b5fd;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    color: #c4b5fd;
    background: transparent;
}

/* =========================== labels =========================== */
QLabel#PanelTitle {
    font-size: 16px;
    font-weight: 800;
    color: #f5f3ff;
    letter-spacing: 0.5px;
}
QLabel#MediaInfo {
    font-size: 11px;
    color: #5b5b78;
}
QLabel#TimeLabel {
    font-family: "Cascadia Mono", "Consolas", monospace;
    font-size: 11px;
    color: #a78bfa;
}
QLabel#hint {
    color: #6272a4;
    font-size: 12px;
    padding: 6px 0;
}
QLabel#StatusMsg {
    color: #a78bfa;
    font-size: 12px;
}
QLabel#KeyInfo {
    color: #c084fc;
    font-weight: 700;
    font-size: 12px;
}

/* =========================== log / text edit =========================== */
QPlainTextEdit {
    background-color: #13131f;
    border: 1px solid #2d2d44;
    border-radius: 8px;
    padding: 8px;
    font-family: "Cascadia Mono", "Consolas", monospace;
    font-size: 12px;
    color: #a78bfa;
    selection-background-color: #5b21b6;
}

/* =========================== preview =========================== */
QVideoWidget#VideoSurface {
    background-color: #0a0a14;
    border: 1px solid #2d2d44;
    border-radius: 14px;
}

/* =========================== scrollbar =========================== */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #3b3b58;
    border-radius: 4px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover {
    background: #6d6d96;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

/* =========================== splitter =========================== */
QSplitter::handle {
    background-color: transparent;
}
QSplitter::handle:horizontal {
    width: 1px;
    background-color: #2d2d44;
}
QSplitter::handle:horizontal:hover {
    background-color: #a78bfa;
}

/* =========================== status bar =========================== */
QStatusBar {
    background-color: #13131f;
    color: #6272a4;
    border-top: 1px solid #2d2d44;
    font-size: 11px;
}
QStatusBar::item {
    border: none;
}

/* =========================== tooltip =========================== */
QToolTip {
    background-color: #2d2d4a;
    color: #e2e8f0;
    border: 1px solid #5b21b6;
    padding: 8px 10px;
    border-radius: 8px;
    font-size: 12px;
}
"""


def apply_theme(app) -> None:
    """Apply the global dark theme (QSS + font + Fusion base style)."""
    from PySide6.QtGui import QFont

    app.setStyle("Fusion")
    qss = _STYLE.replace("__RES__", RES.as_posix())
    app.setStyleSheet(qss)
    app.setFont(QFont("Segoe UI", 10))
