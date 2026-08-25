"""Silence detection and removal."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from . import ffmpeg_tools as ff
from .ffmpeg_tools import CancelledError, FFmpegError


def detect_silence(
    path: str | Path,
    threshold_db: float = -30.0,
    min_silence: float = 0.5,
) -> list[tuple[float, float]]:
    """Return silence windows [(start, end)] in seconds using ffmpeg silencedetect."""
    cmd = [
        ff.find_ffmpeg(), "-nostdin", "-hide_banner", "-i", str(path),
        "-af", f"silencedetect=noise={threshold_db}dB:d={min_silence}",
        "-f", "null", "-",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise FFmpegError(r.stderr.strip() or "silence detection failed")

    start_re = re.compile(r"silence_start:\s*([\d.]+)")
    end_re = re.compile(r"silence_end:\s*([\d.]+)")
    starts = [float(x) for x in start_re.findall(r.stderr)]
    ends = [float(x) for x in end_re.findall(r.stderr)]

    if not starts:
        return []

    windows: list[tuple[float, float]] = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else s + min_silence
        windows.append((s, max(e, s + min_silence * 0.5)))

    merged: list[tuple[float, float]] = []
    for w in windows:
        if merged and w[0] - merged[-1][1] < min_silence * 0.5:
            merged[-1] = (merged[-1][0], max(merged[-1][1], w[1]))
        else:
            merged.append(w)
    return merged


def cut_silence(
    path: str | Path,
    out: str | Path,
    threshold_db: float = -30.0,
    min_silence: float = 0.5,
    padding: float = 0.5,
    progress_cb=None,
    cancel=None,
    stderr_cb=None,
) -> tuple[str, list[tuple[float, float]]]:
    """Remove silence windows. Returns (output path, kept segments [(s, e)])."""
    info = ff.probe(path)
    if not info["has_video"] and not info["has_audio"]:
        raise FFmpegError("no playable streams found")

    silences = detect_silence(path, threshold_db, min_silence)
    if not silences:
        raise FFmpegError("No silence detected. Lower the threshold or min silence duration.")

    duration = info["duration"] or 0.0
    keep: list[tuple[float, float]] = []
    cursor = 0.0
    for s, e in silences:
        if s > cursor:
            keep.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < duration:
        keep.append((cursor, duration))

    keep = [
        (max(0.0, s - padding), min(duration, e + padding))
        for s, e in keep
        if e - s > 0.05
    ]

    if not keep:
        raise FFmpegError("Everything would be removed. Adjust parameters.")

    sel = "+".join(f"between(t,{s:.4f},{e:.4f})" for s, e in keep)
    has_video = info["has_video"]
    has_audio = info["has_audio"]

    args = ["-i", str(path)]
    vf = f"select='{sel}',setpts=N/({max(info['fps'], 1)}*TB)"
    af = f"aselect='{sel}',asetpts=N/SR/TB"

    args += ["-map", "0:v:0"] if has_video else []
    args += ["-map", "0:a:0"] if has_audio else []
    if has_video:
        args += ["-vf", vf]
    if has_audio:
        args += ["-af", af]
    if has_video:
        args += ["-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p"]
    if has_audio:
        args += ["-c:a", "aac", "-b:a", "192k"]
    args += ["-movflags", "+faststart", str(out)]

    ff.run(args, duration=duration, progress_cb=progress_cb, cancel=cancel, stderr_cb=stderr_cb)
    return str(out), keep
