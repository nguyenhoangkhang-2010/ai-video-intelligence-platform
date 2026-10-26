import subprocess
from unittest.mock import MagicMock, patch

from ai.vision.keyframes import extract_keyframes, scene_change_times, select_times


# ---- select_times ----

def test_starts_near_the_beginning_and_keeps_scene_changes():
    assert select_times([10.0, 20.0], duration=30, min_gap=4, max_gap=60, max_frames=10) == [0.5, 10.0, 20.0]


def test_drops_scene_changes_closer_than_min_gap():
    times = select_times([5.0, 6.0, 7.0, 12.0], duration=20, min_gap=4, max_gap=60, max_frames=10)

    assert times == [0.5, 5.0, 12.0]


def test_fills_long_stretches_without_a_scene_change():
    times = select_times([], duration=100, min_gap=4, max_gap=30, max_frames=10)

    assert len(times) == 4
    assert all(later - earlier <= 30 for earlier, later in zip(times, times[1:]))


def test_caps_frames_with_an_even_spread():
    scenes = [float(t) for t in range(5, 300, 5)]

    times = select_times(scenes, duration=300, min_gap=4, max_gap=30, max_frames=6)

    assert len(times) == 6
    assert times[0] == 0.5
    assert times[-1] > 200


def test_ignores_scene_times_outside_the_video():
    assert select_times([-1.0, 50.0], duration=40, min_gap=4, max_gap=60, max_frames=10) == [0.5]


def test_nothing_for_an_empty_video():
    assert select_times([3.0], duration=0, min_gap=4, max_gap=30, max_frames=10) == []
    assert select_times([3.0], duration=10, min_gap=4, max_gap=30, max_frames=0) == []


# ---- ffmpeg wrappers ----

def test_scene_change_times_parses_showinfo_output():
    stderr = (
        "[Parsed_showinfo_1 @ 0x1] n:   0 pts:  12800 pts_time:12.5 duration: 512\n"
        "[Parsed_showinfo_1 @ 0x1] n:   1 pts:  40960 pts_time:40 duration: 512\n"
    )
    with patch("ai.vision.keyframes.subprocess.run", return_value=MagicMock(stderr=stderr)) as run:
        assert scene_change_times("video.mp4", 0.3) == [12.5, 40.0]

    assert "select='gt(scene,0.3)',showinfo" in run.call_args.args[0]


def test_extract_keyframes_falls_back_to_even_sampling_when_scene_detection_fails(tmp_path):
    def fake_run(command, **kwargs):
        if "-f" in command and "null" in command:
            raise subprocess.CalledProcessError(1, command)
        (tmp_path / command[-1].split("/")[-1].split("\\")[-1]).write_bytes(b"jpeg")
        return MagicMock()

    with patch("ai.vision.keyframes.subprocess.run", side_effect=fake_run):
        frames = extract_keyframes(
            "video.mp4", str(tmp_path), duration=70,
            scene_threshold=0.3, min_gap=4, max_gap=30, max_frames=10, width=640,
        )

    assert [frame.time for frame in frames][0] == 0.5
    assert len(frames) == 3
