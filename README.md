# EasyCut

A Windows 10 desktop video editing app built with **PySide6 (Qt)**, **ffmpeg**, **OpenCV**, **faster-whisper** and **rembg**.

Features AI background removal, face retouching, silence cutting, speech-to-text subtitles, chroma keying, and a timeline editor where every tool's output drops back in for further editing.

---

## Requirements

- Windows 10
- Python 3.12+ (tested on 3.14)
- **ffmpeg** full build on your system (https://www.gyan.dev/ffmpeg/builds/ — download "essentials" or "full")

## Install

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

First launch downloads AI models automatically (requires internet, only once):

| Tool | Model | Cache location | Approx. size |
|---|---|---|---|
| Subtitles | faster-whisper (whisper) | `%USERPROFILE%\.cache\huggingface\` | 0.5 – 5 GB (depends on model size) |
| AI Background | rembg (u2net) | `%USERPROFILE%\.u2net\` | ~170 MB |

## Run

```
.venv\Scripts\python main.py
```

---

## The interface

The window has **two panels**:

- **Left (tabs):** eight tabs — one per tool plus the editor.
- **Right (preview):** a built-in media player with a seek slider, volume control, and a **Send to...** button. You can also load the preview with any video from the tabs.

## Face Retouch

Detects frontal faces in each video frame and applies edge-preserving skin smoothing inside a soft face mask. The original audio is preserved and the result is sent to the Editor.

| Control | What it does |
|---|---|
| **Smoothing strength** | Controls how strongly skin texture is softened. Zero leaves the video unchanged. |
| **Face detection** | Trades detection coverage for processing speed. Use **More faces / slower** for smaller or less frontal faces. |

---

## Editor (timeline)

The timeline tab is the centre of the app. Every other tool sends its output straight into it.

| Action | How |
|---|---|
| **Add clip** | Click **Add video** and pick a file. |
| **Select a clip** | Click on it in the timeline. |
| **Trim** | Drag the left or right edge of a clip. |
| **Split** | Position the playhead inside a clip, click **Split**. |
| **Move** | Select a clip, use **Move left** / **Move right**. |
| **Delete** | Select a clip, click **Delete**. |
| **Scrub** | Click anywhere on the timeline ruler or drag the playhead handle. |
| **Render** | Click **Render Timeline** — concatenates all kept clips into one output file. |

The preview player is linked to the playhead; when you scrub the timeline the video frames update.

---

## Cut Silence

Removes quiet sections from a video using ffmpeg's `silencedetect`.

| Control | What it does | Tuning tip |
|---|---|---|
| **Threshold** | dB level below which audio counts as "silence" | Lower toward −40 dB if quiet speech is being removed (e.g. whispered endings). |
| **Min silence (s)** | Silence must be this long before it's removed | Raise to only remove longer pauses. |
| **Padding (s)** | Extra time kept around each surviving clip | **Raise this if word endings get clipped.** Default is 0.5 s; try 0.8–1.0 s if needed. Range goes up to 1.5 s. |

The kept segments load directly into the Editor timeline.

---

## Remove Background

Uses the **rembg** library with ONNX runtime — runs entirely on CPU (no GPU required, but slow on long videos).

### Models

| Model | Best for |
|---|---|
| **Human (face/hair/body)** *(default)* | People; clean edges around hair and skin |
| u2net | General purpose (objects, animals, etc.) |
| isnet-general-use | Higher quality, slower general model |
| u2netp | Fastest, lower quality |

### Output modes

| Mode | Output | Notes |
|---|---|---|
| **Solid color** | `.mp4` | Green screen replacement or flat background. |
| **Transparent** | `.mov` (ProRes 4444) | Alpha channel preserved; import into Premiere/After Effects/DaVinci as an overlay. |
| **Media** | `.mp4` | Composites over a background image or looping background video. |

### Still images

The tab also accepts `.png`, `.jpg`, `.webp`, `.bmp`, `.tif` inputs — output is a PNG with the background removed (transparent or composited).

### Quality

"Quality" sets the **max processing resolution** per frame. Lower values = faster, less memory. Your machine has ~4 GB RAM free; 720 px is the safe default.

---

## Subtitles

Transcribes speech with **faster-whisper** and produces an `.srt` file.

1. Load a video/audio file.
2. Pick **model size** — `small` (balanced) or `base` (fast) on modest RAM.
3. Pick **language** — Auto-detect works well for most content.
4. Click **Run**. The `.srt` file is saved next to your source.
5. (Optional) tick **Burn subtitles into video** to hardcode them.

Transcription runs in a background thread with progress reporting.

---

## Subtitle Editor

Appears after running the Subtitles tab (it loads the `.srt` automatically), or load one manually.

| Control | Action |
|---|---|
| **Add row** | Insert a new subtitle at the cursor time. |
| **Delete row** | Remove the selected subtitle. |
| **Move up / down** | Reorder subtitles. |
| **Preview at row** | Jumps the preview player to that subtitle's start time. |
| **Save .srt** | Writes the edited subtitles to disk. |
| **Burn into video** | Hardcodes the edited subtitles into the video using ffmpeg. |

Each row has Start (HH:MM:SS.zzz), End (HH:MM:SS.zzz), and Text columns — all editable.

---

## Chroma Key

Classic green/blue screen removal.

1. Load a video and click **Pick key color from frame**.
2. A dialog appears showing the frame. The background color is auto-detected (median of edge pixels). Click anywhere in the preview to override, or just use the detected color.
3. Adjust **Similarity** (how far from the key color to treat as transparent; lower = stricter) and **Blend** (edge softness).
4. Pick output mode (solid color / transparent / media).
5. Click **Run** — the keyed preview updates live as you adjust.

If your subject turns white/washed out, the **similarity is too high** — lower it (0.05–0.15 is typical).

The engine uses ffmpeg `colorkey` (RGB-distance based), which works on white/gray backgrounds unlike pure chrominance-only keyers.

---

## Silence + BG (one-click pipeline)

Runs **Cut Silence → Remove Background** in a single job. Configure both sets of controls in one tab and click Run. The result is sent directly to the Editor.

Useful for the common workflow: "remove silent pauses, then key out the background."

---

## Memory and performance

| Concern | Detail |
|---|---|
| **RAM** | AI background removal peaks at ~500 MB (1080p), ~1.8 GB (4K). "Quality" (max processing resolution) controls this. |
| **Disk** | Temp files are written to `%TEMP%` (auto-cleaned when the job finishes). Frames are streamed via pipe to ffmpeg — no temp PNGs on disk. |
| **Speed** | Expect ~1–3 seconds per frame for AI background removal on CPU. Subtitles are much faster (speech runs at real-time or faster with `base` model). |

### Long videos on low-RAM machines

Lower the "Quality" setting to 512 px; the output is still upscaled to the original resolution — the difference is barely visible but memory use drops dramatically.

---

## Output formats

| Tool | Default output | Where |
|---|---|---|
| Cut Silence | `.mp4` | Next to source, suffix `_cut` |
| Remove Background | `.mp4` (color/media), `.mov` (transparent) | Next to source, suffix `_nobg` |
| Subtitles | `.srt` | Next to source, suffix `_subs` |
| Subtitle Editor burn | `.mp4` | Next to source, suffix `_subs_burn` |
| Chroma Key | `.mp4` (color/media), `.mov` (transparent) | Next to source, suffix `_keyed` |
| Silence + BG | `.mp4` / `.mov` | Next to source, suffix `_cut_nobg` |
| Editor render | `.mp4` | As chosen by the user |

---

## Cleaning up temporary / cache files

| What | Where | Size |
|---|---|---|
| faster-whisper models | `%USERPROFILE%\.cache\huggingface` | 0.5 – 5 GB |
| rembg models | `%USERPROFILE%\.u2net\` | ~170 MB |
| Temp job files | `%TEMP%\ve_bg_*`, `%TEMP%\ve_render_*` | Auto-cleaned per job; delete manually if the app crashed mid-job |

To fully reclaim disk space:

```
rmdir /s /q %USERPROFILE%\.cache\huggingface
rmdir /s /q %USERPROFILE%\.u2net
```

(Models re-download on next launch.)

---

## Troubleshooting

| Problem | Fix |
|---|---|
| **"could not read background media"** | The background file is corrupt, a OneDrive cloud placeholder (right-click → "Always keep on this device"), or an unsupported format. |
| **"FFmpeg exited with code 1" with no clear error** | The real error is in the displayed log lines — scroll up. Common cause: low disk space in `%TEMP%` on C:. |
| **AI background output has wrong colors / too dark** | This was an old bug (fixed) — make sure you're running the latest version of the app. |
| **Last word clipped after Cut Silence** | Increase **Padding** (try 0.8–1.0 s) and/or lower **Threshold** (toward −40 dB). |
| **Slow AI background removal** | Lower "Quality" to 512 px; use `u2netp` model; shorter videos are much faster. |
| **Preview shows a still image / won't play** | The file might be an image, not a video. Images can still be sent to the editor. |
| **Transparent output won't import into Premiere** | Use the `.mov` file (ProRes 4444). Some editors need "Import > Alpha" toggled. |

---

## Project layout

```
main.py                         Entry point
requirements.txt                Python dependencies
app/
  ffmpeg_tools.py               ffmpeg / ffprobe wrappers + progress parsing
  silence.py                    Silence detection (silencedetect) + cutting
  background.py                 AI removal (rembg), chroma key, overlay compositing
  subtitles.py                  faster-whisper transcription → SRT, burning
  timeline.py                   Clip / timeline model (split, trim, locate)
  workers.py                    QThread background worker
  utils.py                      Small helpers (format_time, frame extraction)
  ui/
    main_window.py              Main window, all tool tabs, editor, preview panel
    timeline_widget.py          Custom-painted timeline strip (select/trim/split/scrub)
    widgets.py                  File pickers, color picker, chroma-key picker dialog
    theme.py                    Dark theme (QSS)
```
