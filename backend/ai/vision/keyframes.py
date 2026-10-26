"""
Keyframe selection.

A vision model on CPU takes ~10-30 s per frame, so which frames get
looked at matters more than anything else here. Frames are picked
where the picture actually changes (ffmpeg's scene-change score), so
a slide deck yields one frame per slide and a talking head yields
very few - then two rules bound that:

- min_gap: never two frames closer than this (cuts in fast edits);
- max_gap: never a stretch longer than this without a frame (a slow
  pan or a slide with its text building up has no "scene change"
  but still shows new things).

Finally the total is capped at max_frames, keeping an even spread.
"""
import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger(__name__)

FFMPEG_TIMEOUT_SECONDS = 300
_PTS_TIME = re.compile(r"pts_time:([0-9.]+)")


@dataclass(frozen=True)
class Keyframe:
    time: float
    path: str


def scene_change_times(file_path: str, threshold: float) -> list[float]:
    """Timestamps (s) where ffmpeg's scene-change score exceeds `threshold`."""
    command = [
        "ffmpeg", "-hide_banner", "-nostats",
        "-i", file_path,
        "-an",
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-f", "null", "-",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        errors="replace",
        check=True,
        timeout=FFMPEG_TIMEOUT_SECONDS,
    )
    return [float(match) for match in _PTS_TIME.findall(result.stderr)]


def select_times(
    scene_times: list[float],
    duration: float,
    min_gap: float,
    max_gap: float,
    max_frames: int,
) -> list[float]:
    """
    Frame times to analyse: the opening frame, scene changes at least
    `min_gap` apart, extra frames so no gap exceeds `max_gap`, then at
    most `max_frames` of them spread evenly. Pure, so it is unit-tested
    without ffmpeg.
    """
    if duration <= 0 or max_frames <= 0:
        return []

    # Slightly in, not frame 0: the very first frame is often black.
    times = [min(0.5, duration / 2)]
    for t in sorted(scene_times):
        if 0 < t < duration and t - times[-1] >= min_gap:
            times.append(t)

    filled: list[float] = []
    for start, end in zip(times, [*times[1:], duration]):
        filled.append(start)
        gap = end - start
        if gap > max_gap:
            steps = int(gap // max_gap)
            filled += [start + gap * k / (steps + 1) for k in range(1, steps + 1)]

    if len(filled) <= max_frames:
        return [round(t, 2) for t in filled]
    step = len(filled) / max_frames
    return [round(filled[int(i * step)], 2) for i in range(max_frames)]


def extract_frame(file_path: str, time: float, out_path: str, width: int) -> bool:
    """One JPEG at `time`, scaled to `width` px wide. False if ffmpeg fails."""
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", f"{time:.2f}",
        "-i", file_path,
        "-frames:v", "1",
        "-vf", f"scale={width}:-2",
        "-q:v", "3",
        out_path,
    ]
    try:
        subprocess.run(command, capture_output=True, check=True, timeout=60)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as error:
        logger.warning("Frame extraction failed at %.2fs for %s: %s", time, file_path, error)
        return False
    return Path(out_path).is_file() and Path(out_path).stat().st_size > 0


def extract_keyframes(
    file_path: str,
    out_dir: str,
    duration: float,
    scene_threshold: float,
    min_gap: float,
    max_gap: float,
    max_frames: int,
    width: int,
) -> list[Keyframe]:
    try:
        scenes = scene_change_times(file_path, scene_threshold)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as error:
        # Still useful without scene detection: max_gap sampling alone.
        logger.warning("Scene detection failed for %s, sampling evenly: %s", file_path, error)
        scenes = []

    times = select_times(scenes, duration, min_gap, max_gap, max_frames)
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    frames = []
    for index, time in enumerate(times):
        path = str(Path(out_dir) / f"{index:03d}.jpg")
        if extract_frame(file_path, time, path, width):
            frames.append(Keyframe(time=time, path=path))

    logger.info(
        "Selected %s keyframe(s) from %s scene change(s) over %.0fs of video.",
        len(frames), len(scenes), duration,
    )
    return frames
