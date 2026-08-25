"""Timeline model: clips that reference a source video + time ranges."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Clip:
    source: str
    src_start: float = 0.0
    src_end: float = 0.0
    label: str = ""
    src_dur: float | None = None  # known source duration (for trim clamping)

    @property
    def duration(self) -> float:
        return max(0.0, self.src_end - self.src_start)


class Timeline:
    def __init__(self):
        self.clips: list[Clip] = []

    def total(self) -> float:
        return sum(c.duration for c in self.clips)

    def locate(self, t: float):
        """Return (index, clip, clip_start_in_timeline) for timeline time t."""
        if not self.clips:
            return -1, None, 0.0
        t = max(0.0, t)
        acc = 0.0
        for i, c in enumerate(self.clips):
            if t < acc + c.duration:
                return i, c, acc
            acc += c.duration
        last = len(self.clips) - 1
        return last, self.clips[last], acc - self.clips[last].duration

    def clip_start(self, idx: int) -> float:
        return sum(c.duration for c in self.clips[:idx])

    def split(self, t: float) -> int:
        """Split the clip under timeline time t; returns index of the second half (-1 if no-op)."""
        if len(self.clips) < 1:
            return -1
        total = self.total()
        if t <= 1e-3 or t >= total - 1e-3:
            return -1
        idx, c, cs = self.locate(t)
        tlocal = t - cs
        left = Clip(c.source, c.src_start, c.src_start + tlocal, c.label, c.src_dur)
        right = Clip(c.source, c.src_start + tlocal, c.src_end, c.label, c.src_dur)
        self.clips[idx:idx + 1] = [left, right]
        return idx + 1

    def remove(self, idx: int) -> None:
        if 0 <= idx < len(self.clips):
            del self.clips[idx]

    def move(self, idx: int, delta: int) -> int:
        """Move clip at idx by delta (-1/+1); returns new index."""
        j = idx + delta
        if 0 <= idx < len(self.clips) and 0 <= j < len(self.clips):
            self.clips[idx], self.clips[j] = self.clips[j], self.clips[idx]
            return j
        return idx

    def set_segments(self, source: str, segments, label: str = "seg", src_dur: float | None = None) -> None:
        self.clips = [
            Clip(source, float(s), float(e), label, src_dur)
            for s, e in segments if float(e) - float(s) > 0.001
        ]

    def add(self, clip: Clip) -> int:
        self.clips.append(clip)
        return len(self.clips) - 1

    def clear(self) -> None:
        self.clips = []
