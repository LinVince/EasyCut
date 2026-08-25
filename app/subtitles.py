"""Speech-to-text (faster-whisper) and subtitle generation."""

from __future__ import annotations

from pathlib import Path

import pysubs2

from . import ffmpeg_tools as ff

WHISPER_MODELS = [
    ("tiny", "tiny (fastest, lowest accuracy)"),
    ("base", "base (fast)"),
    ("small", "small (balanced)"),
    ("medium", "medium (accurate, slow)"),
    ("large-v3", "large-v3 (most accurate, slowest)"),
]

LANGUAGES = [
    ("", "Auto-detect"),
    ("en", "English"),
    ("zh", "Chinese (Mandarin)"),
    ("ja", "Japanese"),
    ("ko", "Korean"),
    ("es", "Spanish"),
    ("fr", "French"),
    ("de", "German"),
    ("pt", "Portuguese"),
    ("ru", "Russian"),
    ("ar", "Arabic"),
    ("hi", "Hindi"),
    ("id", "Indonesian"),
    ("th", "Thai"),
    ("vi", "Vietnamese"),
    ("it", "Italian"),
    ("nl", "Dutch"),
    ("pl", "Polish"),
    ("tr", "Turkish"),
]


def pick_model(model: str) -> str:
    if model == "large-v3":
        return "large-v3"
    return model


def transcribe(
    path: str | Path,
    model_name: str = "small",
    language: str = "",
    device: str = "auto",
    progress_cb=None,
    cancel=None,
) -> list[dict]:
    """Transcribe audio and return [{start, end, text}, ...] in seconds."""
    from faster_whisper import WhisperModel

    if device == "auto":
        try:
            import ctranslate2
            device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
        except Exception:
            device = "cpu"
    compute = "float16" if device == "cuda" else "int8"
    model_size = pick_model(model_name)
    if progress_cb:
        progress_cb(2.0)
    model = WhisperModel(model_size, device=device, compute_type=compute)

    if progress_cb:
        progress_cb(5.0)
    segments_iter, _info = model.transcribe(
        str(path),
        language=language or None,
        vad_filter=True,
        beam_size=5,
    )

    out: list[dict] = []
    last = 0.0
    for seg in segments_iter:
        if cancel and cancel():
            raise ff.CancelledError("Operation cancelled")
        text = (seg.text or "").strip()
        if not text:
            continue
        out.append({"start": float(seg.start), "end": float(seg.end), "text": text})
        last = float(seg.end)
        if progress_cb:
            progress_cb(5.0 + min(95.0, last * 0.95))
    return out


def load_srt(path: str | Path) -> list[dict]:
    """Read an .srt (or .ass) file into [{start, end, text}] in seconds."""
    subs = pysubs2.load(str(path))
    return [
        {"start": float(e.start) / 1000.0, "end": float(e.end) / 1000.0, "text": e.text}
        for e in subs
    ]


def write_srt(segments: list[dict], out: str | Path) -> str:
    subs = pysubs2.SSAFile()
    for s in segments:
        subs.append(
            pysubs2.SSAEvent(
                start=int(s["start"] * 1000),
                end=int(s["end"] * 1000),
                text=s["text"],
            )
        )
    subs.save(str(out), format_="srt")
    return str(out)


def make_subtitles(
    path: str | Path,
    srt_out: str | Path,
    model_name: str = "small",
    language: str = "",
    device: str = "auto",
    progress_cb=None,
    cancel=None,
) -> str:
    info = ff.probe(path)
    if not info["has_audio"]:
        raise ff.FFmpegError("selected media has no audio stream")
    segs = transcribe(path, model_name, language, device, progress_cb, cancel)
    write_srt(segs, srt_out)
    return str(srt_out)
