"""Face detection and skin-smoothing video retouching."""

from __future__ import annotations

import subprocess
from pathlib import Path

import cv2
import numpy as np

from . import ffmpeg_tools as ff
from .background import _ffmpeg_stream


def retouch_video(
    path: str | Path,
    out: str | Path,
    strength: int = 45,
    scale_factor: float = 1.1,
    progress_cb=None,
    cancel=None,
) -> str:
    info = ff.probe(path)
    w, h = info["width"], info["height"]
    if not w or not h or not info["has_video"]:
        raise ff.FFmpegError("no video stream found")
    fps = info["fps"] or 30.0
    total = max(1, int(info["duration"] * fps + 0.5))
    detector = cv2.CascadeClassifier(
        str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml")
    )
    if detector.empty():
        raise ff.FFmpegError("OpenCV face detector could not be loaded")

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(".tmp.mp4")
    cmd = [
        ff.find_ffmpeg(), "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
        "-i", str(path), "-map", "0:v:0", "-map", "1:a:0?",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(tmp_path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    stream = _ffmpeg_stream(path, w, h)
    try:
        if proc.stdin is None:
            raise ff.FFmpegError("could not start video encoder")
        frame_no = 0
        while True:
            if cancel and cancel():
                raise ff.CancelledError("Operation cancelled")
            ok, frame = stream.read()
            if not ok:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(
                gray, scaleFactor=scale_factor, minNeighbors=5,
                minSize=(max(32, w // 12), max(32, h // 12)),
            )
            for x, y, face_w, face_h in faces:
                pad_x, pad_y = int(face_w * 0.12), int(face_h * 0.16)
                x0, y0 = max(0, x - pad_x), max(0, y - pad_y)
                x1, y1 = min(w, x + face_w + pad_x), min(h, y + face_h + pad_y)
                roi = frame[y0:y1, x0:x1]
                diameter = 5 + 2 * int(strength / 20)
                smoothed = cv2.bilateralFilter(roi, diameter, 35 + strength, 25 + strength)
                mask = np.zeros(roi.shape[:2], dtype=np.uint8)
                cv2.ellipse(
                    mask, (roi.shape[1] // 2, roi.shape[0] // 2),
                    (max(1, int(roi.shape[1] * 0.43)), max(1, int(roi.shape[0] * 0.47))),
                    0, 0, 360, 255, -1,
                )
                mask = cv2.GaussianBlur(mask, (0, 0), max(1.0, face_w * 0.05))
                mask = (mask.astype(np.float32) * (strength / 100.0))[..., None]
                frame[y0:y1, x0:x1] = (
                    roi.astype(np.float32) * (1.0 - mask / 255.0)
                    + smoothed.astype(np.float32) * (mask / 255.0)
                ).astype(np.uint8)
            proc.stdin.write(frame.tobytes())
            frame_no += 1
            if progress_cb:
                progress_cb(min(99.0, frame_no / total * 100.0))
        proc.stdin.close()
        return_code = proc.wait()
        if return_code != 0:
            error = proc.stderr.read().decode("utf-8", "replace") if proc.stderr else ""
            raise ff.FFmpegError(f"ffmpeg exited with code {return_code}\n{error[-2000:]}")
        tmp_path.replace(out_path)
        if progress_cb:
            progress_cb(100.0)
        return str(out_path)
    except Exception:
        if proc.poll() is None:
            proc.terminate()
        proc.wait()
        tmp_path.unlink(missing_ok=True)
        raise
    finally:
        stream.close()