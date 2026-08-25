"""QThread workers so long-running jobs never block the UI."""

from __future__ import annotations

import traceback

from PySide6.QtCore import QThread, Signal

from .ffmpeg_tools import CancelledError


class TaskWorker(QThread):
    progress = Signal(float)
    log = Signal(str)
    done = Signal(str)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, fn, *args, parent=None):
        super().__init__(parent)
        self._fn = fn
        self._args = args
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            result = self._fn(
                *self._args,
                progress_cb=self.progress.emit,
                cancel=lambda: self._cancelled,
            )
        except CancelledError:
            self.cancelled.emit()
            return
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}")
            return
        self.done.emit(result or "")
