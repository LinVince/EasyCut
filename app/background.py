"""Background removal: AI (rembg) and chroma-key modes."""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
from pathlib import Path

import cv2
import numpy as np

from . import ffmpeg_tools as ff
from .ffmpeg_tools import CancelledError, FFmpegError

BACKGROUND_MODELS = ["u2net", "u2netp", "isnet-general-use"]

AI_OUTPUT_MODES = [
    ("color", "Solid color background"),
    ("transparent", "Transparent (ProRes 4444 .mov)"),
    ("media", "Composite over image/video background"),
]

KEY_OUTPUT_MODES = [
    ("color", "Solid color background"),
    ("transparent", "Transparent (ProRes 4444 .mov)"),
    ("media", "Composite over image/video background"),
]


# ---------------------------------------------------------------- helpers

def _resize_for_mask(frame: np.ndarray, max_size: int) -> tuple[np.ndarray, float]:
    h, w = frame.shape[:2]
    scale = min(1.0, max_size / max(h, w)) if max_size > 0 else 1.0
    if scale >= 1.0:
        return frame, 1.0
    return cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA), scale


def _composite(rgba: np.ndarray, bg_bgr: np.ndarray) -> np.ndarray:
    """Alpha-composite rgba (HxWx4, RGB order) over bg_bgr (HxWx3, BGR)."""
    alpha = (rgba[..., 3:4].astype(np.float32) / 255.0)
    fg = cv2.cvtColor(rgba[..., :3], cv2.COLOR_RGB2BGR).astype(np.float32)
    bg = bg_bgr.astype(np.float32)
    return (fg * alpha + bg * (1.0 - alpha)).astype(np.uint8)


def _color_frame(h: int, w: int, color: tuple[int, int, int]) -> np.ndarray:
    return np.zeros((h, w, 3), dtype=np.uint8)
def _fill_color(frame: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    frame[:] = color
    return frame


_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


class _FfmpegStream:
    """Reads frames from any file ffmpeg can decode (BGR numpy frames).

    cv2.VideoCapture is limited to a few codecs (no HEVC/ProRes/etc.),
    so we pipe raw frames out of ffmpeg instead.
    """

    def __init__(self, path: str | Path, w: int, h: int):
        self.w, self.h = w, h
        self._size = w * h * 3
        self._stderr: list[str] = []
        self._proc = subprocess.Popen(
            [ff.find_ffmpeg(), "-v", "error", "-nostdin", "-i", str(path),
             "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if self._proc.stdout is None:
            raise FFmpegError(f"cannot read: {path}")
        self._err_thread = threading.Thread(target=self._drain, daemon=True)
        self._err_thread.start()

    def _drain(self) -> None:
        assert self._proc.stderr is not None
        for raw in self._proc.stderr:
            line = raw.rstrip(b"\n").decode("utf-8", "replace")
            if line:
                self._stderr.append(line)

    def read(self) -> tuple[bool, np.ndarray | None]:
        data = self._proc.stdout.read(self._size)
        if len(data) != self._size:
            return False, None
        return True, np.frombuffer(data, np.uint8).reshape(self.h, self.w, 3)

    def error_tail(self) -> str:
        return "\n".join(self._stderr[-12:])

    def close(self) -> None:
        try:
            self._proc.stdout.close()
        except Exception:
            pass
        try:
            self._proc.terminate()
            self._proc.wait(timeout=3)
        except Exception:
            pass
        self._err_thread.join(timeout=2)


def _ffmpeg_stream(path: str | Path, w: int, h: int) -> _FfmpegStream:
    return _FfmpegStream(path, w, h)


def _ensure_audio(path: str | Path, audio: bool) -> list[str]:
    return ["-map", "1:a:0?"] if audio else []


# ---------------------------------------------------------------- AI (rembg)

def _png_out(out: Path) -> Path:
    return out.with_suffix(".png") if out.suffix.lower() in {".mp4", ".mov", ".mkv", ".avi", ".webm"} else out


def _ai_remove_image(path, out_path, session, post_mask, w, h,
                     max_size, output_mode, color, bg_path, progress_cb) -> str:
    """Remove background from a single image. Output is always a PNG."""
    import rembg
    frame = cv2.imread(str(path))
    if frame is None:
        raise FFmpegError(f"cannot open image: {path}")
    if progress_cb:
        progress_cb(30.0)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    small, scale = _resize_for_mask(rgb, max_size)
    rgba_small = rembg.remove(small, session=session, post_process_mask=post_mask)
    rgba = cv2.resize(rgba_small, (w, h), interpolation=cv2.INTER_LINEAR) if scale < 1.0 else rgba_small
    if progress_cb:
        progress_cb(90.0)

    out = _png_out(out_path)
    if output_mode == "transparent":
        cv2.imwrite(str(out), cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
    elif output_mode == "media":
        if not bg_path:
            raise FFmpegError("a background image/video is required for media mode")
        bg = cv2.imread(str(bg_path))
        if bg is None:
            raise FFmpegError("could not read background image")
        bg = cv2.resize(bg, (w, h), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(out), _composite(rgba, bg))
    else:
        bg = _color_frame(h, w, color)
        _fill_color(bg, color)
        cv2.imwrite(str(out), _composite(rgba, bg))
    if progress_cb:
        progress_cb(100.0)
    return str(out)


def ai_remove_video(
    path: str | Path,
    out: str | Path,
    model: str = "u2net_human_seg",
    max_size: int = 720,
    output_mode: str = "color",
    color: tuple[int, int, int] = (0, 255, 0),
    bg_path: str | Path | None = None,
    progress_cb=None,
    cancel=None,
) -> str:
    from rembg import new_session, remove

    # The human-segmentation model benefits from mask cleanup (removes stray
    # specks, tightens hair edges).
    post_mask = model == "u2net_human_seg"
    info = ff.probe(path)
    w, h = info["width"], info["height"]
    if not w or not h:
        raise FFmpegError("no video stream found")
    fps = info["fps"] or 30.0
    is_image = info["duration"] <= 0 and Path(path).suffix.lower() in _IMAGE_EXTS
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    session = new_session(model)

    if is_image:
        return _ai_remove_image(path, out_path, session, post_mask, w, h,
                                max_size, output_mode, color, bg_path, progress_cb)

    cap = _ffmpeg_stream(path, w, h)
    total = max(1, int(info["duration"] * (info["fps"] or 30.0) + 0.5))

    # Encode by piping raw frames straight into ffmpeg stdin. No temp PNGs on
    # disk (a nearly-full drive made the old approach fail), and cv2's "mp4v"
    # shifts colors - so ffmpeg does all encoding here.
    if output_mode == "transparent":
        frame_fmt = "rgba"
        vcodec = ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le"]
        tmp_video = out_path.with_suffix(".tmp.mov")
    else:
        frame_fmt = "bgr24"
        vcodec = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p"]
        tmp_video = out_path.with_suffix(".tmp.mp4")

    cmd = [ff.find_ffmpeg(), "-y", "-nostdin", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", frame_fmt, "-s", f"{w}x{h}", "-r", f"{fps}", "-i", "-",
           "-i", str(path),
           "-map", "0:v:0", "-map", "1:a:0?",
           *vcodec,
           "-c:a", "aac", "-b:a", "192k",
           "-threads", "4", "-filter_threads", "2", "-max_muxing_queue_size", "4096"]
    if output_mode != "transparent":
        cmd += ["-movflags", "+faststart"]
    cmd += [str(tmp_video)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    if proc.stdin is None:
        raise FFmpegError("could not start encoder")

    bg_cap = None
    bg_frame = None
    if output_mode == "media":
        if not bg_path:
            raise FFmpegError("a background image/video is required for media mode")
        bg_info = ff.probe(bg_path)
        if bg_info["has_video"] and bg_info["duration"] > 0:
            bg_cap = _ffmpeg_stream(bg_path, bg_info["width"], bg_info["height"])
            ok, bg_frame = bg_cap.read()
            if not ok:
                bg_cap.close()
                raise FFmpegError(
                    f"could not read background media ({Path(bg_path).name}, "
                    f"{os.path.getsize(bg_path) if os.path.exists(bg_path) else 'missing'} bytes): "
                    f"{bg_cap.error_tail() or 'no frames could be decoded'}"
                )
        else:
            bg_frame = cv2.imread(str(bg_path))
            if bg_frame is None and bg_info["width"] > 0 and bg_info["height"] > 0:
                fallback = _ffmpeg_stream(bg_path, bg_info["width"], bg_info["height"])
                bg_frame = fallback.read()[1]
                fallback.close()
        if bg_frame is None:
            size = os.path.getsize(bg_path) if os.path.exists(bg_path) else "missing"
            raise FFmpegError(
                f"could not read background media: {Path(bg_path).name} "
                f"({size} bytes) - not a decodable image/video"
            )
        bg_frame = cv2.resize(bg_frame, (w, h), interpolation=cv2.INTER_AREA)

    try:
        try:
            idx = 0
            while True:
                if cancel and cancel():
                    raise CancelledError("Operation cancelled")
                ok, frame = cap.read()
                if not ok:
                    break
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                small, scale = _resize_for_mask(rgb, max_size)
                rgba_small = remove(small, session=session, post_process_mask=post_mask)
                if scale < 1.0:
                    rgba = cv2.resize(rgba_small, (w, h), interpolation=cv2.INTER_LINEAR)
                else:
                    rgba = rgba_small

                if output_mode == "transparent":
                    out_frame = rgba
                elif output_mode == "color":
                    bg = _color_frame(h, w, color)
                    _fill_color(bg, color)
                    out_frame = _composite(rgba, bg)
                else:  # media
                    if bg_cap is not None:
                        ok2, nf = bg_cap.read()
                        if not ok2:
                            bg_cap.close()
                            bg_cap = _ffmpeg_stream(bg_path, bg_info["width"], bg_info["height"])
                            nf = bg_cap.read()[1]
                        if nf is not None:
                            bg_frame = cv2.resize(nf, (w, h), interpolation=cv2.INTER_AREA)
                    if bg_frame is None:
                        raise FFmpegError("background failed to load")
                    out_frame = _composite(rgba, bg_frame)

                proc.stdin.write(out_frame.tobytes())
                idx += 1
                if progress_cb:
                    progress_cb(idx / total * 100.0)
        except CancelledError:
            proc.kill()
            proc.wait()
            raise
        finally:
            cap.close()
            if bg_cap is not None:
                bg_cap.close()
            try:
                proc.stdin.close()
            except Exception:
                pass
    except (BrokenPipeError, OSError) as e:
        err = proc.stderr.read().decode("utf-8", "replace") if proc.stderr else ""
        tmp_video.unlink(missing_ok=True)
        raise FFmpegError(f"encoding failed: {e}\n{err[-400:]}") from e

    proc.wait()
    err = proc.stderr.read().decode("utf-8", "replace") if proc.stderr else ""
    if proc.returncode != 0:
        tmp_video.unlink(missing_ok=True)
        raise FFmpegError(f"ffmpeg exited with code {proc.returncode}\n{err[-600:]}")
    if idx == 0:
        tmp_video.unlink(missing_ok=True)
        raise FFmpegError("no frames read from source")
    shutil.move(str(tmp_video), str(out))
    return str(out)


# ---------------------------------------------------------------- chroma key

def _key_filter(key_hex: str, similarity: float, blend: float) -> str:
    # colorkey uses RGB distance (sees brightness), so white/light backgrounds
    # work too. ffmpeg's chromakey is chroma-only and wipes neutral subjects.
    return f"colorkey=color=0x{key_hex}:similarity={similarity:.3f}:blend={blend:.3f}"


def chroma_key_video(
    path: str | Path,
    out: str | Path,
    key_hex: str = "00FF00",
    similarity: float = 0.1,
    blend: float = 0.1,
    output_mode: str = "color",
    color: tuple[int, int, int] = (0, 255, 0),
    bg_path: str | Path | None = None,
    max_size: int = 1920,
    progress_cb=None,
    cancel=None,
    stderr_cb=None,
) -> str:
    info = ff.probe(path)
    w, h = info["width"], info["height"]
    fps = info["fps"] or 30.0
    if not w or not h:
        raise FFmpegError("no video stream found")

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    key = _key_filter(key_hex, similarity, blend)
    color_hex = "{:02X}{:02X}{:02X}".format(color[2], color[1], color[0])

    # Keep memory sane: cap the working resolution and limit ffmpeg's
    # multi-threading. Filter threads each hold full-size frames, which can
    # exhaust RAM on long/high-res videos (ffmpeg error "Cannot allocate
    # memory").
    cap = max_size
    sw, sh = w, h
    scale_vf = ""
    if max(w, h) > cap:
        s = cap / max(w, h)
        sw, sh = int(round(w * s) / 2) * 2, int(round(h * s) / 2) * 2
        scale_vf = (
            f"scale={sw}:{sh}:force_original_aspect_ratio=decrease,"
            f"pad={sw}:{sh}:(ow-iw)/2:(oh-ih)/2,"
        )
    mem = ["-threads", "4", "-filter_threads", "2", "-max_muxing_queue_size", "4096"]

    if output_mode == "transparent":
        ff.run(
            ["-i", str(path), "-vf", f"{scale_vf}{key},format=yuva444p",
             "-map", "0:v:0", "-map", "0:a:0?",
             "-c:v", "prores_ks", "-profile:v", "4444",
             "-c:a", "aac", "-b:a", "192k", *mem, str(out)],
            duration=info["duration"], progress_cb=progress_cb, cancel=cancel, stderr_cb=stderr_cb,
        )
        return str(out)

    if output_mode == "media":
        if not bg_path:
            raise FFmpegError("a background image/video is required for media mode")
        bg_info = ff.probe(bg_path)
        if bg_info["duration"] <= 0:
            bg_args = ["-loop", "1", "-i", str(bg_path)]
        else:
            bg_args = ["-stream_loop", "-1", "-i", str(bg_path)]
        fc = (
            f"[0:v]{scale_vf}{key}[fg];"
            f"[1:v]scale={sw}:{sh}:force_original_aspect_ratio=decrease,"
            f"pad={sw}:{sh}:(ow-iw)/2:(oh-ih)/2[bg];"
            f"[bg][fg]overlay=shortest=1[v]"
        )
        args = ["-i", str(path), *bg_args, "-filter_complex", fc,
                "-map", "[v]", "-map", "0:a:0?",
                "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                *mem, str(out)]
    else:  # color
        fc = (
            f"[0:v]{scale_vf}{key}[fg];"
            f"color=c=0x{color_hex}:s={sw}x{sh}:r={fps}[bg];"
            f"[bg][fg]overlay=shortest=1[v]"
        )
        args = ["-i", str(path), "-filter_complex", fc,
                "-map", "[v]", "-map", "0:a:0?",
                "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                *mem, str(out)]

    ff.run(args, duration=info["duration"], progress_cb=progress_cb, cancel=cancel, stderr_cb=stderr_cb)
    return str(out)
