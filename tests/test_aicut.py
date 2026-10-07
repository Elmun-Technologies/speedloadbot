"""Unit tests for utils/aicut.py (the 'smart cut' shorts tool).

ffmpeg/ffprobe are not required — subprocess is mocked.
"""
import subprocess

from utils import aicut


def test_get_video_duration_parses_ffprobe_output(monkeypatch):
    monkeypatch.setattr(subprocess, "check_output", lambda cmd: b"95.5\n")
    assert aicut.get_video_duration("video.mp4") == 95.5


def test_smart_cut_too_short_video_returns_empty(monkeypatch, tmp_path):
    monkeypatch.setattr(subprocess, "check_output", lambda cmd: b"20.0\n")
    assert aicut.smart_cut_shorts("short.mp4", str(tmp_path)) == []


def test_smart_cut_creates_three_vertical_shorts(monkeypatch, tmp_path):
    monkeypatch.setattr(subprocess, "check_output", lambda cmd: b"95.5\n")
    cmds = []
    monkeypatch.setattr(subprocess, "run", lambda cmd, check: cmds.append(cmd))

    paths = aicut.smart_cut_shorts("video.mp4", str(tmp_path))

    assert len(paths) == 3
    assert len(cmds) == 3
    for cmd in cmds:
        assert cmd[0] == "ffmpeg"
        # re-encoded as a vertical 9:16 short
        assert "crop=ih*9/16:ih,scale=720:1280" in cmd
    # marks: start=5, middle=95.5/2=47.75, end=95.5-25=70.5
    starts = [cmd[cmd.index("-ss") + 1] for cmd in cmds]
    assert starts == ["5", "47.75", "70.5"]
    # each cut is 20 seconds long
    durations = [cmd[cmd.index("-t") + 1] for cmd in cmds]
    assert durations == ["20", "20", "20"]


def test_smart_cut_ffmpeg_failure_returns_empty(monkeypatch, tmp_path):
    monkeypatch.setattr(subprocess, "check_output", lambda cmd: b"95.5\n")

    def boom(cmd, check):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(subprocess, "run", boom)
    assert aicut.smart_cut_shorts("video.mp4", str(tmp_path)) == []


def test_smart_cut_ffprobe_failure_returns_empty(monkeypatch, tmp_path):
    def boom(cmd):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(subprocess, "check_output", boom)
    assert aicut.smart_cut_shorts("video.mp4", str(tmp_path)) == []
