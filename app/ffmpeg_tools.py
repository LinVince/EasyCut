"""Thin wrappers around ffmpeg / ffprobe with progress reporting."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
from pathlib import Path


class CancelledError(Exception):
    pass


class FFmpegError(RuntimeError):
    pass


def find_ffmpeg() -> str:
    exe = os.environ.get("FFMPEG_PATH") or shutil.which("ffmpeg")
    if exe and Path(exe).exists():
        return exe
    raise FFmpegError(
        "ffmpeg not found. Install it (https://ffmpeg.org) and add it to PATH, "
        "or set the FFMPEG_PATH environment variable."
    )


def find_ffprobe() -> str:
    exe = os.environ.get("FFPROBE_PATH") or shutil.which("ffprobe")
    if exe and Path(exe).exists():
        return exe
    raise FFmpegError("ffprobe not found. It ships together with ffmpeg.")


def probe(path: str | Path) -> dict:
    cmd = [find_ffprobe(), "-v", "quiet", "-print_format", "json",
           "-show_format", "-show_streams", str(path)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise FFmpegError(r.stderr.strip() or "ffprobe failed")
    data = json.loads(r.stdout or "{}")
    streams = data.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)

    duration = 0.0
    try:
        duration = float(data.get("format", {}).get("duration") or 0.0)
    except (TypeError, ValueError):
        duration = 0.0
    if duration <= 0 and v:
        try:
            duration = float(v.get("duration") or 0.0)
        except (TypeError, ValueError):
            duration = 0.0

    fps = 0.0
    if v:
        fr = v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/1"
        try:
            n, d = fr.split("/")
            if float(d):
                fps = float(n) / float(d)
        except (ValueError, ZeroDivisionError):
            fps = 0.0

    return {
        "duration": duration,
        "width": int(v.get("width") or 0) if v else 0,
        "height": int(v.get("height") or 0) if v else 0,
        "fps": fps,
        "has_video": v is not None,
        "has_audio": a is not None,
        "vcodec": (v or {}).get("codec_name", ""),
        "acodec": (a or {}).get("codec_name", ""),
    }


def run(
    args: list[str],
    duration: float | None = None,
    progress_cb=None,
    cancel=None,
    stderr_cb=None,
) -> subprocess.CompletedProcess:
    """Run ffmpeg. If progress_cb given, parse `-progress pipe:1` output.

    progress_cb(percent: float)  -- 0..100
    stderr_cb(line: str)         -- raw log lines
    cancel()                     -- callable returning True to abort
    """
    cmd = [find_ffmpeg(), "-y", "-nostdin", "-hide_banner", "-loglevel", "info"]
    cmd += args
    if progress_cb:
        cmd += ["-progress", "pipe:1", "-nostats"]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE if progress_cb else subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    cancel_flag = {"stop": False}

    def _watch_cancel():
        while proc.poll() is None:
            try:
                if cancel and cancel():
                    cancel_flag["stop"] = True
                    proc.terminate()
                threading.Event().wait(0.15)
            except Exception:
                return

    if cancel:
        t = threading.Thread(target=_watch_cancel, daemon=True)
        t.start()

    stderr_lines: list[str] = []

    def _read_stderr():
        assert proc.stderr is not None
        for line in proc.stderr:
            line = line.rstrip("\n")
            stderr_lines.append(line)
            if stderr_cb:
                stderr_cb(line)

    stderr_thread = threading.Thread(target=_read_stderr, daemon=True)
    stderr_thread.start()

    _time_re = re.compile(r"out_time=(\d+):(\d+):([\d.]+)")
    _ms_re = re.compile(r"out_time_ms=(\d+)")

    if progress_cb and proc.stdout:
        for raw in proc.stdout:
            line = raw.strip()
            m = _ms_re.search(line)
            if m:
                secs = int(m.group(1)) / 1_000_000.0
            else:
                m = _time_re.search(line)
                if not m:
                    continue
                h, mi, s = m.groups()
                secs = int(h) * 3600 + int(mi) * 60 + float(s)
            if duration and duration > 0:
                progress_cb(max(0.0, min(100.0, secs / duration * 100.0)))

    proc.wait()
    stderr_thread.join(timeout=5)

    if cancel_flag["stop"]:
        raise CancelledError("Operation cancelled")

    if proc.returncode != 0:
        _ERR = ("error", "invalid", "failed", "cannot", "no space", "permission",
                "denied", "exception", "does not", "not found")
        err = [ln for ln in stderr_lines if any(k in ln.lower() for k in _ERR)]
        tail = "\n".join((err or stderr_lines)[-8:])
        raise FFmpegError(f"ffmpeg exited with code {proc.returncode}\n{tail}")

    return subprocess.CompletedProcess(cmd, 0)


def extract_audio(path: str | Path, out_wav: str | Path, progress_cb=None, cancel=None) -> None:
    run(["-i", str(path), "-vn", "-ac", "1", "-ar", "16000", "-y", str(out_wav)],
        progress_cb=progress_cb, cancel=cancel)


def _esc_srt_path(p: str | Path) -> str:
    return str(p).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def burn_subtitles(path: str | Path, srt: str | Path, out: str | Path,
                   font_size: int = 18, progress_cb=None, cancel=None,
                   stderr_cb=None) -> None:
    vf = f"subtitles='{_esc_srt_path(srt)}':force_style='FontName=Calibri,FontSize={font_size},Outline=1,Shadow=1,Alignment=2'"
    run(["-i", str(path), "-vf", vf,
         "-c:v", "libx264", "-crf", "20", "-preset", "medium",
         "-c:a", "aac", "-movflags", "+faststart", str(out)],
        progress_cb=progress_cb, cancel=cancel, stderr_cb=stderr_cb)


def merge_srt(path: str | Path, srt: str | Path, out: str | Path,
              progress_cb=None, cancel=None, stderr_cb=None) -> None:
    run(["-i", str(path), "-i", str(srt),
         "-map", "0", "-map", "1:0", "-c", "copy",
         "-c:s", "mov_text", "-disposition:s:0", "default", str(out)],
        progress_cb=progress_cb, cancel=cancel, stderr_cb=stderr_cb)
