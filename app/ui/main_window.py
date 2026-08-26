"""Main application window with preview and the four tool tabs."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTime
from PySide6.QtGui import QIcon
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from ..timeline import Clip, Timeline
from ..utils import format_time
from ..workers import TaskWorker
from .theme import RES
from .timeline_widget import TimelineWidget
from .widgets import ChromaKeyPickDialog, ColorPickButton, FilePickerRow


def default_output(input_path: str, suffix: str, ext: str = ".mp4") -> str:
    p = Path(input_path)
    return str(p.with_name(p.stem + suffix + ext))


class TabPanel(QWidget):
    """Base tab: run button + progress + log + worker management."""

    def __init__(self, win: "MainWindow", title: str):
        super().__init__()
        self.win = win
        self.title = title
        self.worker: TaskWorker | None = None
        self._build_base()

    def _build_base(self) -> None:
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(2000)
        self.run_btn = QPushButton(f"Run {self.title}")
        self.run_btn.setProperty("accent", True)
        self.run_btn.clicked.connect(self._on_run_clicked)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setProperty("flat", True)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.cancel_btn.setEnabled(False)
        self._msg = QLabel("")
        self._msg.setObjectName("StatusMsg")
        self._msg.setWordWrap(True)

        bottom = QGroupBox("Progress / log")
        bl = QVBoxLayout(bottom)
        row = QHBoxLayout()
        row.addWidget(self._msg, 1)
        row.addWidget(self.cancel_btn)
        row.addWidget(self.run_btn)
        bl.addLayout(row)
        bl.addWidget(self.progress)
        bl.addWidget(self.log)
        bl.setStretchFactor(self.log, 1)

        outer = QVBoxLayout(self)
        outer.addLayout(self.controls_layout())
        outer.addWidget(bottom, 1)

    def controls_layout(self) -> QVBoxLayout:
        raise NotImplementedError

    def build_job(self, progress_cb, cancel):
        raise NotImplementedError

    def result_message(self, result: str) -> str:
        return result or "Done"

    def _on_run_clicked(self) -> None:
        self.log.clear()
        self.progress.setValue(0)
        self._msg.setText("Working...")
        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        try:
            p = self.win.preview.player
            if p.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
                p.pause()
        except Exception:
            pass

        def runner(progress_cb, cancel):
            job = self.build_job(progress_cb, cancel)
            return job()

        self.worker = TaskWorker(runner, parent=self)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.done.connect(self._on_done)
        self.worker.failed.connect(self._on_failed)
        self.worker.cancelled.connect(self._on_cancelled)
        self.worker.start()

    def _on_cancel(self) -> None:
        if self.worker:
            self.worker.cancel()
            self._msg.setText("Cancelling...")

    def _on_done(self, result: str) -> None:
        self.progress.setValue(100)
        self._msg.setText("Finished")
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.log.appendPlainText(f"OK: {self.result_message(result)}")
        self.worker = None

    def _on_failed(self, msg: str) -> None:
        self._msg.setText("Failed - see log")
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.log.appendPlainText(f"ERROR:\n{msg}")
        self.worker = None

    def _on_cancelled(self) -> None:
        self._msg.setText("Cancelled")
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.log.appendPlainText("Cancelled by user.")
        self.worker = None


class OutputRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pick = FilePickerRow("Output file", filter="All files (*)", parent=self)
        self.pick._browse_btn.setText("...")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.pick)

    def path(self) -> str:
        return self.pick.path()

    def set_path(self, p: str) -> None:
        self.pick.set_path(p)

    def set_default(self, inp: str, suffix: str, ext: str = ".mp4") -> None:
        if not self.pick.path():
            self.pick.set_path(default_output(inp, suffix, ext))


class SilenceTab(TabPanel):
    def __init__(self, win):
        self.input = FilePickerRow("Video", preview=True)
        self.output = OutputRow()
        self.thresh = QSlider(Qt.Orientation.Horizontal)
        self.thresh.setRange(-60, -15)
        self.thresh.setValue(-30)
        self.thresh_lbl = QLabel("-30 dB")
        self.thresh.valueChanged.connect(lambda v: self.thresh_lbl.setText(f"{v} dB"))
        self.min_sil = QDoubleSpinBox()
        self.min_sil.setRange(0.1, 3.0)
        self.min_sil.setSingleStep(0.1)
        self.min_sil.setValue(0.5)
        self.pad = QDoubleSpinBox()
        self.pad.setRange(0.0, 1.5)
        self.pad.setSingleStep(0.05)
        self.pad.setValue(0.5)
        super().__init__(win, "Silence Cut")

    def controls_layout(self) -> QVBoxLayout:
        lay = QVBoxLayout()
        lay.addWidget(self.input)
        lay.addWidget(self.output)

        g = QGroupBox("Detection parameters")
        gl = QVBoxLayout(g)
        th = QHBoxLayout()
        th.addWidget(QLabel("Threshold"))
        th.addWidget(self.thresh, 1)
        th.addWidget(self.thresh_lbl)
        gl.addLayout(th)
        ms = QHBoxLayout()
        ms.addWidget(QLabel("Min silence (s)"))
        ms.addWidget(self.min_sil)
        ms.addStretch(1)
        ms.addWidget(QLabel("Padding (s)"))
        ms.addWidget(self.pad)
        gl.addLayout(ms)
        tip = QLabel("A silence louder than the threshold that lasts at least the minimum duration is removed. "
                     "Padding is kept around each remaining clip so speech is never clipped. "
                     "If your last word is cut off, increase the Padding or lower the Threshold.")
        tip.setObjectName("hint")
        tip.setWordWrap(True)
        gl.addWidget(tip)
        lay.addWidget(g)
        lay.addStretch(1)
        return lay

    def build_job(self, progress_cb, cancel):
        from ..silence import cut_silence
        src = self.input.path()
        if not src:
            raise ValueError("select a video first")
        self.output.set_default(src, "_cut")
        from .. import ffmpeg_tools as ff
        ff.probe(src)
        th = self.thresh.value()

        def job():
            out, keep = cut_silence(
                src, self.output.path(), threshold_db=th,
                min_silence=self.min_sil.value(), padding=self.pad.value(),
                progress_cb=progress_cb, cancel=cancel)
            self._last_keep = keep
            return out
        return job

    def _on_done(self, result: str) -> None:
        super()._on_done(result)
        self.win.send_to_editor(self, result, "keep")


class BackgroundTab(TabPanel):
    def __init__(self, win):
        self.input = FilePickerRow("Video / Image", preview=True,
                                   filter="Video/Image (*.mp4 *.mov *.mkv *.avi *.webm *.png *.jpg *.jpeg *.webp *.bmp);;All files (*)")
        self.output = OutputRow()
        self.mode = QComboBox()
        for key, label in [
            ("color", "Solid color background"),
            ("transparent", "Transparent (ProRes .mov)"),
            ("media", "Over image/video background"),
        ]:
            self.mode.addItem(label, key)
        self.model = QComboBox()
        for key, label in [
            ("u2net_human_seg", "Human (face/hair/body) - best for people"),
            ("u2net", "u2net (balanced general)"),
            ("isnet-general-use", "isnet (quality general)"),
            ("u2netp", "u2netp (fast)"),
        ]:
            self.model.addItem(label, key)
        self.model.setCurrentIndex(0)
        self.max_size = QComboBox()
        for val in [512, 640, 720, 960, 0]:
            self.max_size.addItem("Full" if val == 0 else f"Max {val}px", val)
        self.max_size.setCurrentIndex(2)
        self.color = ColorPickButton("Background color", (0, 255, 0))
        self.bg = FilePickerRow("Background", filter="Video/Image (*.mp4 *.mov *.mkv *.avi *.webm *.png *.jpg *.jpeg)")
        super().__init__(win, "Background Removal")

    def controls_layout(self) -> QVBoxLayout:
        lay = QVBoxLayout()
        lay.addWidget(self.input)
        lay.addWidget(self.output)

        g = QGroupBox("Settings")
        gl = QVBoxLayout(g)
        r1 = QHBoxLayout(); r1.addWidget(QLabel("Output mode")); r1.addWidget(self.mode, 1); gl.addLayout(r1)
        r2 = QHBoxLayout(); r2.addWidget(QLabel("Model")); r2.addWidget(self.model, 1); gl.addLayout(r2)
        r3 = QHBoxLayout(); r3.addWidget(QLabel("Quality")); r3.addWidget(self.max_size, 1); gl.addLayout(r3)
        gl.addWidget(self.color)
        gl.addWidget(self.bg)
        tip = QLabel("Works on videos OR single images (output becomes a PNG). "
                     "AI mode detects the subject in every frame - expect it to be slow on CPU. "
                     "'Human' uses a model trained specifically on people (face, hair, body) for clean edges. "
                     "Transparent output writes a ProRes 4444 .mov (alpha channel). Media mode composites onto a background video/image.")
        tip.setObjectName("hint")
        tip.setWordWrap(True)
        gl.addWidget(tip)
        lay.addWidget(g)
        lay.addStretch(1)
        return lay

    def build_job(self, progress_cb, cancel):
        from ..background import ai_remove_video
        src = self.input.path()
        if not src:
            raise ValueError("select a video first")
        mode = self.mode.currentData()
        if mode == "media" and not self.bg.path():
            raise ValueError("choose a background image/video for media mode")
        self.output.set_default(src, "_nobg", ".png" if Path(src).suffix.lower() in
                                (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")
                                else (".mp4" if mode != "transparent" else ".mov"))
        return lambda: ai_remove_video(
            src, self.output.path(), model=self.model.currentData(),
            max_size=self.max_size.currentData(), output_mode=mode,
            color=self.color.color(), bg_path=self.bg.path() or None,
            progress_cb=progress_cb, cancel=cancel)

    def _on_done(self, result: str) -> None:
        super()._on_done(result)
        self.win.send_to_editor(self, result, "nobg")


class RetouchTab(TabPanel):
    def __init__(self, win):
        self.input = FilePickerRow("Video", preview=True)
        self.output = OutputRow()
        self.strength = QSlider(Qt.Orientation.Horizontal)
        self.strength.setRange(0, 100)
        self.strength.setValue(45)
        self.strength_lbl = QLabel("45%")
        self.strength.valueChanged.connect(lambda v: self.strength_lbl.setText(f"{v}%"))
        self.scale = QComboBox()
        for value, label in [(1.05, "More faces / slower"), (1.1, "Balanced"), (1.2, "Faster")]:
            self.scale.addItem(label, value)
        self.scale.setCurrentIndex(1)
        super().__init__(win, "Face Retouch")

    def controls_layout(self) -> QVBoxLayout:
        lay = QVBoxLayout()
        lay.addWidget(self.input)
        lay.addWidget(self.output)
        group = QGroupBox("Retouch settings")
        layout = QVBoxLayout(group)
        strength = QHBoxLayout()
        strength.addWidget(QLabel("Smoothing strength"))
        strength.addWidget(self.strength, 1)
        strength.addWidget(self.strength_lbl)
        layout.addLayout(strength)
        detection = QHBoxLayout()
        detection.addWidget(QLabel("Face detection"))
        detection.addWidget(self.scale, 1)
        layout.addLayout(detection)
        tip = QLabel("Detects frontal faces and softly smooths skin inside each face region. "
                     "Eyes, hair, and the area outside faces are preserved. Higher strength gives a "
                     "more noticeable result; use a lower value for a natural finish.")
        tip.setObjectName("hint")
        tip.setWordWrap(True)
        layout.addWidget(tip)
        lay.addWidget(group)
        lay.addStretch(1)
        return lay

    def build_job(self, progress_cb, cancel):
        from ..retouch import retouch_video

        src = self.input.path()
        if not src:
            raise ValueError("select a video first")
        self.output.set_default(src, "_retouched")
        return lambda: retouch_video(
            src, self.output.path(), strength=self.strength.value(),
            scale_factor=self.scale.currentData(),
            progress_cb=progress_cb, cancel=cancel)

    def _on_done(self, result: str) -> None:
        super()._on_done(result)
        self.win.send_to_editor(self, result, "retouched")


class SubtitleTab(TabPanel):
    def __init__(self, win):
        self.input = FilePickerRow("Video/Audio", filter="Media (*.mp4 *.mov *.mkv *.avi *.webm *.mp3 *.wav *.m4a);;All files (*)", preview=True)
        self.output = OutputRow()
        self.model = QComboBox()
        for key, label in [
            ("tiny", "tiny (fastest)"),
            ("base", "base (fast)"),
            ("small", "small (balanced)"),
            ("medium", "medium (accurate)"),
            ("large-v3", "large-v3 (most accurate)"),
        ]:
            self.model.addItem(label, key)
        self.model.setCurrentIndex(2)
        self.lang = QComboBox()
        for key, label in [
            ("", "Auto-detect"),
            ("en", "English"), ("zh", "Chinese"), ("ja", "Japanese"), ("ko", "Korean"),
            ("es", "Spanish"), ("fr", "French"), ("de", "German"), ("pt", "Portuguese"),
            ("ru", "Russian"), ("ar", "Arabic"), ("hi", "Hindi"), ("id", "Indonesian"),
            ("th", "Thai"), ("vi", "Vietnamese"), ("it", "Italian"), ("nl", "Dutch"),
        ]:
            self.lang.addItem(label, key)
        self.device = QComboBox()
        for key, label in [("auto", "Auto"), ("cpu", "CPU"), ("cuda", "CUDA GPU")]:
            self.device.addItem(label, key)
        self.burn = _BoolCbx("Burn subtitles into video")
        self.font = QSpinBox()
        self.font.setRange(8, 72)
        self.font.setValue(18)
        super().__init__(win, "Subtitles")

    def controls_layout(self) -> QVBoxLayout:
        lay = QVBoxLayout()
        lay.addWidget(self.input)
        lay.addWidget(self.output)
        g = QGroupBox("Transcription")
        gl = QVBoxLayout(g)
        r1 = QHBoxLayout(); r1.addWidget(QLabel("Whisper model")); r1.addWidget(self.model, 1); gl.addLayout(r1)
        r2 = QHBoxLayout(); r2.addWidget(QLabel("Language")); r2.addWidget(self.lang, 1); gl.addLayout(r2)
        r3 = QHBoxLayout(); r3.addWidget(QLabel("Device")); r3.addWidget(self.device, 1); gl.addLayout(r3)
        r4 = QHBoxLayout(); r4.addWidget(self.burn); r4.addStretch(1); r4.addWidget(QLabel("Font size")); r4.addWidget(self.font); gl.addLayout(r4)
        tip = QLabel("The model downloads to ~/.cache/huggingface on first use. Always produces an .srt file; "
                     "optionally burns it into the video.")
        tip.setObjectName("hint")
        tip.setWordWrap(True)
        gl.addWidget(tip)
        lay.addWidget(g)
        lay.addStretch(1)
        return lay

    def build_job(self, progress_cb, cancel):
        from ..subtitles import make_subtitles
        from ..ffmpeg_tools import burn_subtitles
        src = self.input.path()
        if not src:
            raise ValueError("select media first")
        p = Path(src)
        srt = str(p.with_name(p.stem + "_subs.srt"))
        do_burn = self.burn.isChecked()
        model = self.model.currentData()
        lang = self.lang.currentData()
        dev = self.device.currentData()

        def job():
            make_subtitles(src, srt, model_name=model, language=lang, device=dev,
                           progress_cb=progress_cb, cancel=cancel)
            self._last_srt = srt
            if do_burn:
                out = self.output.path() or default_output(src, "_subtitled")
                self.output.set_default(src, "_subtitled")
                progress_cb(96.0)
                burn_subtitles(src, srt, out, font_size=self.font.value(),
                               progress_cb=progress_cb, cancel=cancel)
                return out
            return srt
        return job

    def result_message(self, result: str) -> str:
        return result

    def _on_done(self, result: str) -> None:
        super()._on_done(result)
        srt = getattr(self, "_last_srt", None) or result
        if Path(srt).suffix.lower() in (".srt", ".ass", ".ssa"):
            self.win.subedit.load_srt(srt, self.input.path())
            self.win.tabs.setCurrentWidget(self.win.subedit)
            self.win.statusBar().showMessage("Subtitles ready - edit them in the Subtitle Editor", 5000)


class ChromaKeyTab(TabPanel):
    def __init__(self, win):
        self.input = FilePickerRow("Video", preview=True)
        self.output = OutputRow()
        self.mode = QComboBox()
        for key, label in [
            ("color", "Solid color background"),
            ("transparent", "Transparent (ProRes .mov)"),
            ("media", "Over image/video background"),
        ]:
            self.mode.addItem(label, key)
        self.pick_btn = QPushButton("Pick key color from frame...")
        self.pick_btn.clicked.connect(self._pick_color)
        self.color_info = QLabel("No color picked yet")
        self.color_info.setObjectName("KeyInfo")
        self.sim = QSlider(Qt.Orientation.Horizontal)
        self.sim.setRange(0, 1000)
        self.sim.setValue(100)
        self.sim_lbl = QLabel("0.10")
        self.sim.valueChanged.connect(lambda v: self.sim_lbl.setText(f"{v / 1000:.3f}"))
        self.blend = QSlider(Qt.Orientation.Horizontal)
        self.blend.setRange(0, 1000)
        self.blend.setValue(100)
        self.blend_lbl = QLabel("0.10")
        self.blend.valueChanged.connect(lambda v: self.blend_lbl.setText(f"{v / 1000:.3f}"))
        self.color = ColorPickButton("BG color", (255, 255, 255))
        self.bg = FilePickerRow("Background", filter="Video/Image (*.mp4 *.mov *.mkv *.avi *.webm *.png *.jpg *.jpeg)")
        self.maxsize = QComboBox()
        for label, val in [
            ("Original (up to 4K)", 4096),
            ("1080p (recommended, low memory)", 1920),
            ("720p (lowest memory)", 1280),
        ]:
            self.maxsize.addItem(label, val)
        self.maxsize.setCurrentIndex(1)
        self._key: tuple[int, int, int] | None = None
        super().__init__(win, "Chroma Key")

    def controls_layout(self) -> QVBoxLayout:
        lay = QVBoxLayout()
        lay.addWidget(self.input)
        lay.addWidget(self.output)
        g = QGroupBox("Key settings")
        gl = QVBoxLayout(g)
        r0 = QHBoxLayout(); r0.addWidget(QLabel("Output mode")); r0.addWidget(self.mode, 1); gl.addLayout(r0)
        r1 = QHBoxLayout(); r1.addWidget(QLabel("Max output size")); r1.addWidget(self.maxsize, 1); gl.addLayout(r1)
        gl.addWidget(self.pick_btn)
        gl.addWidget(self.color_info)
        s1 = QHBoxLayout(); s1.addWidget(QLabel("Similarity")); s1.addWidget(self.sim, 1); s1.addWidget(self.sim_lbl); gl.addLayout(s1)
        s2 = QHBoxLayout(); s2.addWidget(QLabel("Blend")); s2.addWidget(self.blend, 1); s2.addWidget(self.blend_lbl); gl.addLayout(s2)
        gl.addWidget(self.color)
        gl.addWidget(self.bg)
        tip = QLabel("Open the preview, move the playhead to a frame with the background, then 'Pick key color' and click it. "
                     "Green screen -> solid/composite output. Transparent gives a ProRes 4444 .mov with alpha for overlay work. "
                     "If it fails with 'Cannot allocate memory', lower the max output size.")
        tip.setObjectName("hint")
        tip.setWordWrap(True)
        gl.addWidget(tip)
        lay.addWidget(g)
        lay.addStretch(1)
        return lay

    def _pick_color(self) -> None:
        src = self.input.path()
        if not src:
            self.win.statusBar().showMessage("Open a video first", 4000)
            return
        time_sec = self.win.preview.go.value()
        try:
            dlg = ChromaKeyPickDialog(src, time_sec, self)
        except Exception as exc:
            self._msg.setText(f"Could not open frame: {exc}")
            return
        if dlg.exec():
            self._key, sim, bl = dlg.values()
            self.sim.setValue(int(sim * 1000))
            self.blend.setValue(int(bl * 1000))
            b, g, r = self._key
            self.color_info.setText(f"Key color RGB({r},{g},{b})  hex #{r:02X}{g:02X}{b:02X}")

    def build_job(self, progress_cb, cancel):
        from ..background import chroma_key_video
        src = self.input.path()
        if not src:
            raise ValueError("select a video first")
        if not self._key:
            raise ValueError("pick a key color first")
        mode = self.mode.currentData()
        if mode == "media" and not self.bg.path():
            raise ValueError("choose a background image/video for media mode")
        b, g, r = self._key
        key_hex = f"{r:02X}{g:02X}{b:02X}"
        self.output.set_default(src, "_keyed", ".mp4" if mode != "transparent" else ".mov")
        return lambda: chroma_key_video(
            src, self.output.path(), key_hex=key_hex,
            similarity=self.sim.value() / 1000.0, blend=self.blend.value() / 1000.0,
            output_mode=mode, color=self.color.color(), bg_path=self.bg.path() or None,
            max_size=self.maxsize.currentData(),
            progress_cb=progress_cb, cancel=cancel)

    def _on_done(self, result: str) -> None:
        super()._on_done(result)
        self.win.send_to_editor(self, result, "keyed")


class SilenceBGTab(TabPanel):
    """One-click pipeline: cut silence then remove background."""

    def __init__(self, win):
        self.input = FilePickerRow("Video", preview=True)
        self.output = OutputRow()

        # -- silence controls
        self.thresh = QSlider(Qt.Orientation.Horizontal)
        self.thresh.setRange(-60, -15)
        self.thresh.setValue(-30)
        self.thresh_lbl = QLabel("-30 dB")
        self.thresh.valueChanged.connect(lambda v: self.thresh_lbl.setText(f"{v} dB"))
        self.min_sil = QDoubleSpinBox()
        self.min_sil.setRange(0.1, 3.0)
        self.min_sil.setSingleStep(0.1)
        self.min_sil.setValue(0.5)
        self.pad = QDoubleSpinBox()
        self.pad.setRange(0.0, 1.5)
        self.pad.setSingleStep(0.05)
        self.pad.setValue(0.5)

        # -- background removal controls
        self.mode = QComboBox()
        for key, label in [
            ("color", "Solid color background"),
            ("transparent", "Transparent (ProRes .mov)"),
            ("media", "Over image/video background"),
        ]:
            self.mode.addItem(label, key)
        self.model = QComboBox()
        for key, label in [
            ("u2net_human_seg", "Human (face/hair/body)"),
            ("u2net", "u2net (general)"),
            ("isnet-general-use", "isnet (quality)"),
            ("u2netp", "u2netp (fast)"),
        ]:
            self.model.addItem(label, key)
        self.model.setCurrentIndex(0)
        self.max_size = QComboBox()
        for val in [512, 640, 720, 960, 0]:
            self.max_size.addItem("Full" if val == 0 else f"Max {val}px", val)
        self.max_size.setCurrentIndex(2)
        self.color = ColorPickButton("Background color", (0, 255, 0))
        self.bg = FilePickerRow("Background",
                                filter="Video/Image (*.mp4 *.mov *.mkv *.avi *.webm *.png *.jpg *.jpeg)")
        super().__init__(win, "Silence + BG")

    def controls_layout(self) -> QVBoxLayout:
        lay = QVBoxLayout()
        lay.addWidget(self.input)
        lay.addWidget(self.output)

        g1 = QGroupBox("Step 1 – Cut silence")
        g1l = QVBoxLayout(g1)
        th = QHBoxLayout()
        th.addWidget(QLabel("Threshold"))
        th.addWidget(self.thresh, 1)
        th.addWidget(self.thresh_lbl)
        g1l.addLayout(th)
        ms = QHBoxLayout()
        ms.addWidget(QLabel("Min silence (s)"))
        ms.addWidget(self.min_sil)
        ms.addStretch(1)
        ms.addWidget(QLabel("Padding (s)"))
        ms.addWidget(self.pad)
        g1l.addLayout(ms)
        lay.addWidget(g1)

        g2 = QGroupBox("Step 2 – Remove background")
        g2l = QVBoxLayout(g2)
        r1 = QHBoxLayout(); r1.addWidget(QLabel("Output mode")); r1.addWidget(self.mode, 1); g2l.addLayout(r1)
        r2 = QHBoxLayout(); r2.addWidget(QLabel("Model")); r2.addWidget(self.model, 1); g2l.addLayout(r2)
        r3 = QHBoxLayout(); r3.addWidget(QLabel("Quality")); r3.addWidget(self.max_size, 1); g2l.addLayout(r3)
        g2l.addWidget(self.color)
        g2l.addWidget(self.bg)
        lay.addWidget(g2)

        tip = QLabel("Runs both steps in sequence: first strips silence, then removes the background. "
                     "The final result is sent to the Editor. "
                     "If your last word is cut off, increase Padding or lower the Threshold.")
        tip.setObjectName("hint")
        tip.setWordWrap(True)
        lay.addWidget(tip)
        lay.addStretch(1)
        return lay

    def build_job(self, progress_cb, cancel):
        from ..silence import cut_silence
        from ..background import ai_remove_video

        src = self.input.path()
        if not src:
            raise ValueError("select a video first")
        mode = self.mode.currentData()
        if mode == "media" and not self.bg.path():
            raise ValueError("choose a background image/video for media mode")
        self.output.set_default(src, "_cut_nobg",
                                ".mov" if mode == "transparent" else ".mp4")

        from ..ffmpeg_tools import CancelledError

        def job():
            import tempfile, os
            tmpdir = tempfile.mkdtemp(prefix="ve_pipe_")
            tmp_video = os.path.join(tmpdir, "cut.mp4")
            try:
                # Step 1: cut silence
                cut_silence(src, tmp_video,
                            threshold_db=self.thresh.value(),
                            min_silence=self.min_sil.value(),
                            padding=self.pad.value(),
                            progress_cb=lambda p: progress_cb(p * 0.3),
                            cancel=cancel)
                # Step 2: remove background
                result = ai_remove_video(
                    tmp_video, self.output.path(),
                    model=self.model.currentData(),
                    max_size=self.max_size.currentData(),
                    output_mode=mode,
                    color=self.color.color(),
                    bg_path=self.bg.path() or None,
                    progress_cb=lambda p: progress_cb(30.0 + p * 0.7),
                    cancel=cancel)
                return result
            finally:
                import shutil
                shutil.rmtree(tmpdir, ignore_errors=True)
        return job

    def _on_done(self, result: str) -> None:
        super()._on_done(result)
        self.win.send_to_editor(self, result, "nobg")


class SubtitleEditTab(TabPanel):
    """Workspace to load, edit and re-burn subtitle files."""

    def __init__(self, win):
        self.video = FilePickerRow("Video", preview=True)
        self.input = self.video
        self.srt = FilePickerRow("Subtitle file", filter="Subtitles (*.srt *.ass *.ssa);;All files (*)")
        self.output = OutputRow()
        self.srt.pathChanged.connect(self._load_srt_file)
        self.font = QSpinBox()
        self.font.setRange(8, 72)
        self.font.setValue(18)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Start", "End", "Text"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._srt_path: str | None = None
        super().__init__(win, "Subtitle Editor")
        self.run_btn.setText("Burn into video")

    def controls_layout(self) -> QVBoxLayout:
        lay = QVBoxLayout()
        lay.addWidget(self.video)
        lay.addWidget(self.srt)
        lay.addWidget(self.output)
        g = QGroupBox("Edit subtitles")
        gl = QVBoxLayout(g)
        gl.addWidget(self.table, 1)
        row = QHBoxLayout()
        for text, cb in [
            ("Add row", self._add_row),
            ("Delete row", self._del_row),
            ("Move up", self._move_row_up),
            ("Move down", self._move_row_down),
            ("Preview at row", self._seek_row),
            ("Save .srt", self._save_srt),
        ]:
            b = QPushButton(text)
            b.clicked.connect(cb)
            row.addWidget(b)
        row.addStretch(1)
        row.addWidget(QLabel("Font size"))
        row.addWidget(self.font)
        gl.addLayout(row)
        tip = QLabel("Edit times and text in the table. 'Preview at row' jumps the player to that subtitle. "
                     "Burn writes the subtitles into the video (output goes to the Editor timeline).")
        tip.setObjectName("hint")
        tip.setWordWrap(True)
        gl.addWidget(tip)
        lay.addWidget(g)
        lay.addStretch(1)
        return lay

    def load_srt(self, srt_path: str, video_path: str | None = None) -> None:
        if not srt_path or not Path(srt_path).exists():
            return
        try:
            from ..subtitles import load_srt
            segs = load_srt(srt_path)
        except Exception:
            return
        self._populate(segs)
        self._srt_path = srt_path
        if video_path and not self.video.path():
            self.video.set_path(video_path)
        self.status(f"Loaded {len(segs)} subtitle lines from {Path(srt_path).name}")

    def status(self, text: str) -> None:
        self._msg.setText(text)

    def _load_srt_file(self, path: str) -> None:
        if path:
            self.load_srt(path)

    # ------------------------------------------------------------- rows

    def _populate(self, segs: list[dict]) -> None:
        self.table.setRowCount(0)
        for s in segs:
            self._append_row(s["start"], s["end"], s["text"])

    def _append_row(self, start: float, end: float, text: str) -> int:
        r = self.table.rowCount()
        self.table.insertRow(r)
        self._set_row(r, start, end, text)
        return r

    def _time_box(self, secs: float) -> QTimeEdit:
        box = QTimeEdit()
        box.setDisplayFormat("HH:mm:ss.zzz")
        box.setTime(QTime(0, 0).addMSecs(max(0, int(secs * 1000))))
        return box

    def _set_row(self, r: int, start: float, end: float, text: str) -> None:
        self.table.setCellWidget(r, 0, self._time_box(start))
        self.table.setCellWidget(r, 1, self._time_box(end))
        self.table.setItem(r, 2, QTableWidgetItem(text))

    def _row_data(self, r: int) -> tuple[float, float, str]:
        t0 = self.table.cellWidget(r, 0)
        t1 = self.table.cellWidget(r, 1)
        item = self.table.item(r, 2)
        start = t0.time().msecsSinceStartOfDay() / 1000.0 if t0 else 0.0
        end = t1.time().msecsSinceStartOfDay() / 1000.0 if t1 else 0.0
        return start, end, (item.text() if item else "")

    def _events(self) -> list[dict]:
        out = []
        for r in range(self.table.rowCount()):
            start, end, text = self._row_data(r)
            text = text.strip()
            if not text:
                continue
            out.append({"start": start, "end": end, "text": text})
        return out

    def _add_row(self) -> None:
        idx = self.table.currentRow() + 1 if self.table.currentRow() >= 0 else self.table.rowCount()
        start = end = 0.0
        if self.table.rowCount():
            _, _, last_end = self._row_data(self.table.rowCount() - 1)
            start = end = last_end
        self.table.insertRow(idx)
        self._set_row(idx, start, end, "New subtitle")
        self.table.setCurrentCell(idx, 0)

    def _del_row(self) -> None:
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)

    def _move_row(self, d: int) -> None:
        r = self.table.currentRow()
        t = r + d
        if r < 0 or t < 0 or t >= self.table.rowCount():
            return
        a, b = self._row_data(r), self._row_data(t)
        self._set_row(r, *b)
        self._set_row(t, *a)
        self.table.setCurrentCell(t, 0)

    def _move_row_up(self) -> None:
        self._move_row(-1)

    def _move_row_down(self) -> None:
        self._move_row(1)

    def _seek_row(self) -> None:
        r = self.table.currentRow()
        if r < 0:
            return
        t0 = self.table.cellWidget(r, 0)
        if not t0:
            return
        video = self.video.path()
        if not video:
            self.status("Select a video first")
            return
        p = self.win.preview.player
        if p.source().toLocalFile() != video:
            self.win.preview.load(video)
        p.pause()
        p.setPosition(t0.time().msecsSinceStartOfDay())

    def _save_srt(self) -> None:
        events = self._events()
        if not events:
            self.status("Nothing to save yet")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save subtitles",
                                              self._srt_path or "subtitles.srt",
                                              "SRT (*.srt);;ASS (*.ass)")
        if not path:
            return
        from ..subtitles import write_srt
        write_srt(events, path)
        self._srt_path = path
        self.status(f"Saved {path}")

    # ------------------------------------------------------------- burn

    def build_job(self, progress_cb, cancel):
        from ..ffmpeg_tools import burn_subtitles
        from ..subtitles import write_srt
        video = self.video.path()
        if not video:
            raise ValueError("select a video first")
        events = self._events()
        if not events:
            raise ValueError("add at least one subtitle row")
        self._srt_path = self._srt_path or str(Path(video).with_name(Path(video).stem + "_edited.srt"))
        srt = self._srt_path
        out = self.output.path() or default_output(video, "_subtitled")
        self.output.set_default(video, "_subtitled")

        def job():
            write_srt(events, srt)
            progress_cb(5.0)
            burn_subtitles(video, srt, out, font_size=self.font.value(),
                           progress_cb=progress_cb, cancel=cancel)
            return out
        return job

    def _on_done(self, result: str) -> None:
        super()._on_done(result)
        self.win.send_to_editor(self, result, "subs")


class _BoolCbx(QWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QCheckBox
        self._cb = QCheckBox(text)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._cb)

    def isChecked(self) -> bool:
        return self._cb.isChecked()


class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.video = QVideoWidget(self)
        self.video.setObjectName("VideoSurface")
        self.player.setVideoOutput(self.video)

        self.play_btn = QPushButton()
        self.play_btn.setObjectName("PlayButton")
        self.play_btn.setToolTip("Play / pause")
        self.play_btn.setIcon(QIcon(str(RES / "play.svg")))
        self.play_btn.setIconSize(QSize(16, 16))
        self.play_btn.setFixedSize(38, 38)
        self.play_btn.clicked.connect(self._toggle_play)

        self.pos = QSlider(Qt.Orientation.Horizontal)
        self.pos.setRange(0, 1000)
        self.pos_lbl = QLabel("00:00:00.000 / 00:00:00.000")
        self.pos_lbl.setObjectName("TimeLabel")

        self.go = QDoubleSpinBox()
        self.go.setRange(0, 1e9)
        self.go.setDecimals(3)
        self.go.setSuffix(" s")
        self.go_btn = QPushButton("Go")
        self.go_btn.setProperty("flat", True)
        self.go_btn.clicked.connect(lambda: self.player.setPosition(int(self.go.value() * 1000)))

        self.mute_btn = QPushButton("Mute")
        self.mute_btn.setProperty("flat", True)
        self.mute_btn.clicked.connect(self._toggle_mute)
        self.vol = QSlider(Qt.Orientation.Horizontal)
        self.vol.setRange(0, 100)
        self.vol.setValue(80)
        self.vol.setFixedWidth(110)
        self.vol_lbl = QLabel("80%")
        self.vol_lbl.setObjectName("TimeLabel")
        self.vol.valueChanged.connect(self._volume_changed)

        self.player.positionChanged.connect(self._pos_changed)
        self.player.durationChanged.connect(self._duration_changed)
        self.player.playbackStateChanged.connect(self._state_changed)
        self.pos.sliderPressed.connect(self._scrub_start)
        self.pos.sliderReleased.connect(self._scrub_end)
        self._scrubbing = False
        self._duration_ms = 0

        title = QLabel("Preview")
        title.setObjectName("PanelTitle")
        self.info_lbl = QLabel("No media loaded")
        self.info_lbl.setObjectName("MediaInfo")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 14)
        lay.setSpacing(10)
        hdr = QHBoxLayout()
        hdr.addWidget(title)
        hdr.addStretch(1)
        hdr.addWidget(self.info_lbl)
        lay.addLayout(hdr)
        lay.addWidget(self.video, 1)

        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(self.play_btn)
        row.addWidget(self.pos, 1)
        row.addWidget(self.pos_lbl)
        lay.addLayout(row)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        row2.addWidget(QLabel("Seek to"))
        row2.addWidget(self.go, 1)
        row2.addWidget(self.go_btn)
        row2.addStretch(2)
        row2.addWidget(self.mute_btn)
        row2.addWidget(self.vol)
        row2.addWidget(self.vol_lbl)
        lay.addLayout(row2)
        self.setMinimumWidth(440)

    def load(self, path: str) -> None:
        self.player.stop()
        self.player.setSource(_qurl(path))
        self.go.setMaximum(max(1.0, self.player.duration() / 1000.0))
        try:
            from ..ffmpeg_tools import probe
            info = probe(path)
            parts = []
            if info["width"] and info["height"]:
                parts.append(f"{info['width']}\u00d7{info['height']}")
            if info["fps"]:
                parts.append(f"{info['fps']:.0f} fps")
            if info["duration"]:
                parts.append(format_time(info["duration"]))
            self.info_lbl.setText("   \u2022   ".join(parts))
        except Exception:
            self.info_lbl.setText("")

    def _toggle_play(self) -> None:
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _toggle_mute(self) -> None:
        muted = not self.audio.isMuted()
        self.audio.setMuted(muted)
        self.mute_btn.setText("Unmute" if muted else "Mute")

    def _volume_changed(self, v: int) -> None:
        self.audio.setVolume(v / 100.0)
        self.vol_lbl.setText(f"{v}%")

    def _state_changed(self, state) -> None:
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.play_btn.setIcon(QIcon(str(RES / ("pause" if playing else "play") + ".svg")))

    def _scrub_start(self) -> None:
        self._scrubbing = True

    def _scrub_end(self) -> None:
        self._scrubbing = False
        if self._duration_ms:
            self.player.setPosition(int(self.pos.value() / 1000 * self._duration_ms))

    def _pos_changed(self, ms: int) -> None:
        self.pos_lbl.setText(f"{format_time(ms / 1000.0)} / {format_time(self._duration_ms / 1000.0)}")
        if not self._scrubbing and self._duration_ms:
            self.pos.setValue(int(ms / self._duration_ms * 1000))
        self.go.setValue(ms / 1000.0)

    def _duration_changed(self, ms: int) -> None:
        self._duration_ms = ms
        self.go.setMaximum(max(1.0, ms / 1000.0))


def _qurl(p: str):
    from PySide6.QtCore import QUrl
    from pathlib import Path as P
    return QUrl.fromLocalFile(str(P(p).resolve()))


class EditorTab(TabPanel):
    """Timeline workstation: load clips, split/trim/delete/reorder, then render."""

    def __init__(self, win):
        self.input = FilePickerRow("Add video", preview=True)
        self.add_btn = QPushButton("Add to timeline")
        self.add_btn.setProperty("accent", True)
        self.timeline = Timeline()
        self.tlw = TimelineWidget(self.timeline)
        self.play_btn = QPushButton()
        self.play_btn.setObjectName("PlayButton")
        self.play_btn.setToolTip("Play / pause timeline")
        self.play_btn.setIcon(QIcon(str(RES / "play.svg")))
        self.play_btn.setIconSize(QSize(16, 16))
        self.play_btn.setFixedSize(38, 38)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setProperty("flat", True)
        self.pos_lbl = QLabel("00:00:00.000 / 00:00:00.000")
        self.pos_lbl.setObjectName("TimeLabel")
        self.output = OutputRow()

        self.clip_info = QLabel("No clip selected")
        self.clip_info.setObjectName("hint")
        self.clip_start = QDoubleSpinBox()
        self.clip_start.setDecimals(3)
        self.clip_start.setRange(0, 1e9)
        self.clip_end = QDoubleSpinBox()
        self.clip_end.setDecimals(3)
        self.clip_end.setRange(0, 1e9)
        self.split_btn = QPushButton("Split at playhead")
        self.del_btn = QPushButton("Delete clip")
        self.left_btn = QPushButton("\u2190 Move left")
        self.right_btn = QPushButton("Move right \u2192")
        self.clear_btn = QPushButton("Clear timeline")

        super().__init__(win, "Render Timeline")

        self.add_btn.clicked.connect(self._add_input)
        self.clear_btn.clicked.connect(self._clear)
        self.play_btn.clicked.connect(self._toggle_play)
        self.stop_btn.clicked.connect(self._stop)
        self.split_btn.clicked.connect(self._split)
        self.del_btn.clicked.connect(self._delete)
        self.left_btn.clicked.connect(lambda: self._move(-1))
        self.right_btn.clicked.connect(lambda: self._move(1))
        self.clip_start.valueChanged.connect(self._apply_trim)
        self.clip_end.valueChanged.connect(self._apply_trim)
        self.tlw.positionChanged.connect(self._scrub)
        self.tlw.clipSelected.connect(self._select_clip)
        self.tlw.clipsChanged.connect(self._on_clips_changed)

        player = self.win.preview.player
        player.positionChanged.connect(self._on_player_pos)
        player.mediaStatusChanged.connect(self._on_media_status)

        self._playing = False
        self._current_idx = -1
        self._current_source: str | None = None
        self._pending = None  # (source_time, autoplay) awaiting media load
        self._loading_spins = False

    # ------------------------------------------------------------ layout

    def controls_layout(self) -> QVBoxLayout:
        lay = QVBoxLayout()
        inrow = QHBoxLayout()
        inrow.addWidget(self.input, 1)
        inrow.addWidget(self.add_btn)
        lay.addLayout(inrow)

        g = QGroupBox("Timeline")
        gl = QVBoxLayout(g)
        gl.addWidget(self.tlw)
        tr = QHBoxLayout()
        tr.addWidget(self.play_btn)
        tr.addWidget(self.stop_btn)
        tr.addWidget(self.pos_lbl, 1)
        gl.addLayout(tr)
        lay.addWidget(g)

        cg = QGroupBox("Selected clip")
        cgl = QVBoxLayout(cg)
        cgl.addWidget(self.clip_info)
        rr = QHBoxLayout()
        rr.addWidget(QLabel("Start"))
        rr.addWidget(self.clip_start, 1)
        rr.addSpacing(12)
        rr.addWidget(QLabel("End"))
        rr.addWidget(self.clip_end, 1)
        cgl.addLayout(rr)
        btns = QHBoxLayout()
        btns.addWidget(self.split_btn)
        btns.addWidget(self.del_btn)
        btns.addStretch(1)
        btns.addWidget(self.left_btn)
        btns.addWidget(self.right_btn)
        cgl.addLayout(btns)
        cgl.addWidget(self.clear_btn)
        lay.addWidget(cg)

        lay.addWidget(self.output)
        tip = QLabel("Tool results load here automatically. Click blocks to select, drag their edges to trim, "
                     "double-click to split, drag the playhead to scrub. Render exports the edited timeline.")
        tip.setObjectName("hint")
        tip.setWordWrap(True)
        lay.addWidget(tip)
        lay.addStretch(1)
        return lay

    # ------------------------------------------------------------ timeline ops

    def _add_input(self) -> None:
        src = self.input.path()
        if not src:
            self._msg.setText("Choose a video first")
            return
        try:
            self.add_source(src, Path(src).stem)
        except Exception as exc:
            self._msg.setText(f"Could not load: {exc}")

    def add_source(self, src: str, label: str) -> int:
        from ..ffmpeg_tools import probe
        info = probe(src)
        if not info["has_video"]:
            raise ValueError("file has no video stream")
        dur = info["duration"] or 1.0
        idx = self.timeline.add(Clip(src, 0.0, dur, label=label, src_dur=dur))
        self._after_change(select=idx, scrub_to=0.0)
        return idx

    def load_from_kept(self, src: str, segments, label: str = "keep") -> None:
        from ..ffmpeg_tools import probe
        info = probe(src)
        dur = info["duration"] or (segments[-1][1] if segments else 1.0)
        self.timeline.set_segments(src, segments, label=label, src_dur=dur)
        self._after_change(select=0, scrub_to=0.0)

    def _clear(self) -> None:
        self._stop()
        self.timeline.clear()
        self._after_change(select=-1, scrub_to=0.0)

    def _split(self) -> None:
        idx = self.timeline.split(self.tlw.position)
        if idx >= 0:
            self.tlw.set_selected(idx)
            self._on_clips_changed()

    def _delete(self) -> None:
        if 0 <= self.tlw.selected < len(self.timeline.clips):
            self.timeline.remove(self.tlw.selected)
            self.tlw.set_selected(-1)
            self._on_clips_changed()

    def _move(self, delta: int) -> None:
        if self.tlw.selected >= 0:
            new = self.timeline.move(self.tlw.selected, delta)
            self.tlw.set_selected(new)
            self._on_clips_changed()

    def _after_change(self, select: int, scrub_to: float) -> None:
        self._refresh_clip_ui()
        self.tlw.set_selected(select)
        self.tlw.refresh()
        if self.timeline.clips:
            self._scrub(scrub_to)

    def _on_clips_changed(self) -> None:
        self._refresh_clip_ui()
        self.tlw.refresh()

    def _select_clip(self, idx: int) -> None:
        self._refresh_clip_ui()
        if idx >= 0 and idx < len(self.timeline.clips):
            t = self.timeline.clip_start(idx)
            self._scrub(t)

    def _refresh_clip_ui(self) -> None:
        idx = self.tlw.selected
        n = len(self.timeline.clips)
        if not (0 <= idx < n):
            self.clip_info.setText("No clip selected" if n == 0 else "No clip selected")
            self.split_btn.setEnabled(n > 0)
            self.clear_btn.setEnabled(n > 0)
            self.del_btn.setEnabled(False)
            self.left_btn.setEnabled(False)
            self.right_btn.setEnabled(False)
            self.clip_start.setEnabled(False)
            self.clip_end.setEnabled(False)
            return
        c = self.timeline.clips[idx]
        self.clip_info.setText(
            f"Clip {idx + 1} of {n}   \u2022   {format_time(c.duration)}   \u2022   {Path(c.source).name}")
        self.split_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.del_btn.setEnabled(True)
        self.left_btn.setEnabled(idx > 0)
        self.right_btn.setEnabled(idx < n - 1)
        self.clip_start.setEnabled(True)
        self.clip_end.setEnabled(True)
        self._loading_spins = True
        self.clip_start.setValue(c.src_start)
        self.clip_end.setValue(c.src_end)
        self._loading_spins = False

    def _apply_trim(self) -> None:
        if self._loading_spins:
            return
        idx = self.tlw.selected
        if not (0 <= idx < len(self.timeline.clips)):
            return
        c = self.timeline.clips[idx]
        s = self.clip_start.value()
        e = self.clip_end.value()
        if s >= e:
            return
        hi = c.src_dur if c.src_dur else e
        c.src_start = max(0.0, min(s, hi - 0.2))
        c.src_end = min(hi, max(e, c.src_start + 0.2))
        self.tlw.set_selected(idx)
        self._on_clips_changed()
        self._scrub(self.timeline.clip_start(idx))

    # ------------------------------------------------------------ playback mapping

    def _toggle_play(self) -> None:
        if self._playing:
            self._pause()
        else:
            self._play_from(self.tlw.position)

    def _play_from(self, t: float) -> None:
        clips = self.timeline.clips
        if not clips:
            return
        idx, c, cs = self.timeline.locate(t)
        self._current_idx = idx
        self._playing = True
        self._play_icon(True)
        self._ensure_source(c, c.src_start + (t - cs), True)

    def _pause(self) -> None:
        self._playing = False
        self.win.preview.player.pause()
        self._play_icon(False)

    def _stop(self) -> None:
        self._playing = False
        self.win.preview.player.stop()
        self._pending = None
        self._play_icon(False)

    def _play_icon(self, playing: bool) -> None:
        self.play_btn.setIcon(QIcon(str(RES / ("pause" if playing else "play") + ".svg")))

    def _ensure_source(self, clip: Clip, src_time: float, autoplay: bool) -> None:
        player = self.win.preview.player
        if self._current_source != clip.source:
            self._current_source = clip.source
            player.stop()
            player.setSource(_qurl(clip.source))
            self._pending = (max(0.0, src_time), autoplay)
        else:
            player.setPosition(int(max(0.0, src_time) * 1000))
            if autoplay:
                player.play()

    def _on_media_status(self, st) -> None:
        from PySide6.QtMultimedia import QMediaPlayer
        if st == QMediaPlayer.MediaStatus.LoadedMedia and self._pending:
            t, autoplay = self._pending
            self._pending = None
            self.win.preview.player.setPosition(int(t * 1000))
            if autoplay:
                self.win.preview.player.play()
        elif st in (QMediaPlayer.MediaStatus.InvalidMedia, QMediaPlayer.MediaStatus.NoMedia):
            self._pending = None

    def _on_player_pos(self, ms: int) -> None:
        if not self._playing or self._pending:
            return
        clips = self.timeline.clips
        idx = self._current_idx
        if not (0 <= idx < len(clips)):
            return
        c = clips[idx]
        st = ms / 1000.0
        if st >= c.src_end - 0.04:
            if idx + 1 >= len(clips):
                self._stop()
                self.tlw.set_position(self.timeline.total())
                self.pos_lbl.setText(f"{format_time(self.timeline.total())} / {format_time(self.timeline.total())}")
                return
            nxt = clips[idx + 1]
            self._current_idx = idx + 1
            self._ensure_source(nxt, nxt.src_start, True)
            return
        t = self.timeline.clip_start(idx) + (st - c.src_start)
        self._sync_display(t)

    def _scrub(self, t: float) -> None:
        clips = self.timeline.clips
        if not clips:
            return
        idx, c, cs = self.timeline.locate(t)
        self._current_idx = idx
        self._ensure_source(c, c.src_start + (t - cs), False)
        self._sync_display(t)

    def _sync_display(self, t: float) -> None:
        t = max(0.0, min(t, self.timeline.total()))
        self.tlw.set_position(t)
        self.pos_lbl.setText(f"{format_time(t)} / {format_time(self.timeline.total())}")

    # ------------------------------------------------------------ render

    def build_job(self, progress_cb, cancel):
        clips = list(self.timeline.clips)
        if not clips:
            raise ValueError("timeline is empty - add a video or run a tool first")
        if not self.output.path():
            self.output.set_path(default_output(clips[0].source, "_edited"))

        def job():
            import tempfile
            from .. import ffmpeg_tools as ff
            out = self.output.path()
            tmpdir = Path(tempfile.mkdtemp(prefix="ve_render_"))
            try:
                segs: list[str] = []
                for i, c in enumerate(clips):
                    if cancel():
                        raise ff.CancelledError("Operation cancelled")
                    seg = str(tmpdir / f"seg{i:04d}.mp4")
                    ff.run(
                        ["-i", c.source, "-ss", f"{c.src_start:.3f}", "-to", f"{c.src_end:.3f}",
                         "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p",
                         "-c:a", "aac", "-b:a", "192k", seg],
                        progress_cb=lambda p, i=i: progress_cb((i + p / 100.0) / len(clips) * 100.0),
                        cancel=cancel)
                    segs.append(seg)
                listf = tmpdir / "list.txt"
                lines = "\n".join(f"file '{s.replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'"
                                  for s in segs)
                listf.write_text(lines, encoding="utf-8")
                ff.run(["-f", "concat", "-safe", "0", "-i", str(listf),
                        "-c", "copy", "-movflags", "+faststart", out],
                       progress_cb=progress_cb, cancel=cancel)
                return out
            finally:
                import shutil
                shutil.rmtree(tmpdir, ignore_errors=True)
        return job

    def result_message(self, result: str) -> str:
        return result


class HeaderBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AppHeader")
        title = QLabel("EasyCut")
        title.setObjectName("AppTitle")
        tag = QLabel("Cut silence   \u2022   Remove background   \u2022   Subtitles   \u2022   Chroma key overlay")
        tag.setObjectName("AppTagline")
        badge = QLabel("v1.0")
        badge.setObjectName("AppBadge")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(26, 14, 26, 14)
        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(title)
        col.addWidget(tag)
        lay.addLayout(col)
        lay.addStretch(1)
        lay.addWidget(badge)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EasyCut")
        self._workers: list[TaskWorker] = []
        self._build_ui()

    def _build_ui(self) -> None:
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.preview = PreviewPanel(self)
        self.editor = EditorTab(self)
        self.silence = SilenceTab(self)
        self.background = BackgroundTab(self)
        self.retouch = RetouchTab(self)
        self.subtitles = SubtitleTab(self)
        self.subedit = SubtitleEditTab(self)
        self.chroma = ChromaKeyTab(self)
        self.silence_bg = SilenceBGTab(self)
        for tab, name in [
            (self.editor, "Editor"),
            (self.silence, "Cut Silence"),
            (self.background, "Remove Background"),
            (self.retouch, "Face Retouch"),
            (self.subtitles, "Subtitles"),
            (self.subedit, "Subtitle Editor"),
            (self.chroma, "Chroma Key"),
            (self.silence_bg, "Silence + BG"),
        ]:
            self.tabs.addTab(tab, name)
            tab.input.pathChanged.connect(self._input_changed)
        self.tabs.currentChanged.connect(self._tab_changed)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.tabs)
        splitter.addWidget(self.preview)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([620, 560])
        splitter.setChildrenCollapsible(False)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(HeaderBar())
        root.addWidget(splitter, 1)
        self.setCentralWidget(central)
        self.statusBar().showMessage("Ready")

    def _input_changed(self, path: str) -> None:
        if Path(path).exists():
            self.preview.load(path)

    def _tab_changed(self, index: int) -> None:
        if self.tabs.currentWidget() is not self.editor:
            self.editor._pause()

    def send_to_editor(self, tab, result: str, kind: str) -> None:
        """Load a finished tool result into the editor timeline."""
        if not result or not Path(result).exists():
            return
        try:
            if kind == "keep" and hasattr(tab, "_last_keep") and tab._last_keep:
                self.editor.load_from_kept(tab.input.path(), tab._last_keep, label="keep")
            elif kind in ("nobg", "keyed", "retouched", "subs"):
                self.editor.add_source(result, kind)
            else:
                return
        except Exception:
            return
        self.tabs.setCurrentWidget(self.editor)
        self.statusBar().showMessage("Result loaded into the editor - keep editing", 5000)

    def closeEvent(self, ev) -> None:
        for w in self._workers:
            w.cancel()
        for w in self._workers:
            w.wait(3000)
        super().closeEvent(ev)
