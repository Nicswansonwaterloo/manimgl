"""Synthetic video regression checks; these do not render Manim scenes."""
from fractions import Fraction
from pathlib import Path
import tempfile
import unittest

import av
import numpy as np

from benchmarks.support.visual import (
    DEFAULT_TOLERANCES, compare_video, frame_metrics, inspect_video, validate_suite,
)


def write_video(path, values, fps=15):
    with av.open(str(path), "w") as container:
        stream = container.add_stream("libx264", rate=fps)
        stream.width = stream.height = 32
        stream.pix_fmt = "yuv444p"
        stream.options = {"crf": "0"}
        for index, value in enumerate(values):
            frame = av.VideoFrame.from_ndarray(np.full((32, 32, 3), value, np.uint8), format="rgb24")
            frame.pts, frame.time_base = index, Fraction(1, fps)
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)


class VisualTests(unittest.TestCase):
    def test_small_pixel_noise_passes_but_removed_object_fails(self):
        reference = np.zeros((100, 100, 3), np.uint8)
        noisy = reference.copy()
        noisy[0, 0] = 5
        self.assertFalse(frame_metrics(reference, noisy, DEFAULT_TOLERANCES)[3])
        noisy[20:40, 20:40] = 255
        self.assertTrue(frame_metrics(reference, noisy, DEFAULT_TOLERANCES)[3])

    def test_middle_frame_regression_saves_visual_diffs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_video(root / "old.mp4", [0, 0, 0])
            write_video(root / "new.mp4", [0, 255, 0])
            result = compare_video(root / "old.mp4", root / "new.mp4", root / "diffs", DEFAULT_TOLERANCES)
            self.assertEqual(result["compared_frames"], 3)
            self.assertEqual([f["frame"] for f in result["failed_frames"]], [1])
            self.assertEqual(len(list((root / "diffs").glob("*.png"))), 3)

    def test_truncated_video_is_detected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_video(root / "old.mp4", [0, 0, 0])
            write_video(root / "new.mp4", [0, 0])
            result = compare_video(root / "old.mp4", root / "new.mp4", root / "diffs", DEFAULT_TOLERANCES)
            self.assertEqual(result["failed_frames"][0]["frame"], 2)
            info = inspect_video(root / "new.mp4", {"frames": 3, "animation_seconds": 3 / 15},
                                 {"resolution": "32x32", "fps": 15}, 0.001)
            self.assertTrue(info["errors"])

    def test_wrong_playback_rate_fails_even_with_identical_pixels(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "wrong-rate.mp4"
            write_video(path, [0, 0, 0], fps=30)
            info = inspect_video(path, {"frames": 3, "animation_seconds": 3 / 15},
                                 {"resolution": "32x32", "fps": 15}, 0.001)
            self.assertIn("Encoded frame rate differs from requested FPS", info["errors"])

    def test_baseline_calibrates_both_phases_and_candidate_regression_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            baseline = root / "baseline"
            candidate = root / "candidate"
            baseline.mkdir()
            candidate.mkdir()
            def report(folder, changed=False):
                runs = []
                for phase in ("first", "cached"):
                    write_video(folder / f"{phase}.mp4", [0, 255 if changed else 0, 0])
                    runs.append({"name": "Case", "phase": phase, "status": "ok", "frames": 3,
                                 "animation_seconds": 0.2, "video": f"{phase}.mp4"})
                return {"resolution": "32x32", "fps": 15, "scenes": [{"name": "Case"}], "runs": runs}
            old = report(baseline)
            self.assertTrue(validate_suite(old, baseline, DEFAULT_TOLERANCES))
            self.assertTrue(all("tolerances" in r["visual"] for r in old["runs"]))
            new = report(candidate, changed=True)
            self.assertFalse(validate_suite(new, candidate, DEFAULT_TOLERANCES, (baseline, old)))
            self.assertTrue((candidate / "validation.json").exists())
            self.assertEqual(len(list((candidate / "visual-diffs").rglob("*-diff-4x.png"))), 2)


if __name__ == "__main__":
    unittest.main()
