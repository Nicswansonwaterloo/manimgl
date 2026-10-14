"""Guard performance comparisons against changed inputs and incomplete measurements."""
import argparse
from copy import deepcopy
import tempfile
from pathlib import Path
import unittest

from benchmarks.support.reporting import comparison_rows, make_report


class ReportingTests(unittest.TestCase):
    def report(self, seconds=10):
        return {"schema_version": 4, "resolution": "1920x1080", "fps": 60,
                "gpu_timing_requested": False, "encoding": {"crf": 23}, "workload_sha256": "same",
                "repeat": 3, "scenes": [{"name": "Case"}], "interrupted": False,
                "summary": [{"name": "Case", "passed": 3, "failed": 0,
                             "render_seconds": seconds, "wall_seconds": seconds + 2}]}

    def test_negative_means_faster_and_positive_means_slower(self):
        baseline = self.report()
        self.assertAlmostEqual(comparison_rows(baseline, self.report(8))[0]["render_change_percent"], -20)
        self.assertAlmostEqual(comparison_rows(baseline, self.report(12))[0]["render_change_percent"], 20)

    def test_different_workloads_or_settings_are_rejected(self):
        baseline = self.report()
        for field, different in [("workload_sha256", "changed"), ("fps", 30),
                                 ("resolution", "640x360"), ("gpu_timing_requested", True),
                                 ("encoding", {"crf": 0})]:
            candidate = deepcopy(baseline)
            candidate[field] = different
            with self.assertRaisesRegex(ValueError, field):
                comparison_rows(baseline, candidate)

    def test_failed_or_partial_repetitions_have_no_percentage(self):
        baseline, candidate = self.report(), self.report(2)
        candidate["summary"][0].update(passed=2, failed=1)
        self.assertIsNone(comparison_rows(baseline, candidate)[0]["render_change_percent"])
        candidate["summary"][0]["failed"] = 0
        self.assertIsNone(comparison_rows(baseline, candidate)[0]["render_change_percent"])

    def test_interrupted_and_missing_scenes_are_rejected(self):
        baseline, candidate = self.report(), self.report()
        candidate["interrupted"] = True
        with self.assertRaisesRegex(ValueError, "interrupted"):
            comparison_rows(baseline, candidate)
        candidate["interrupted"] = False
        candidate["summary"] = []
        with self.assertRaisesRegex(ValueError, "incomplete"):
            comparison_rows(baseline, candidate)

    def test_workload_fingerprint_tracks_sources_not_git_revision(self):
        # Use an existing helper root; the temporary source simulates a selected
        # external scene without importing Manim or touching the real workload.
        root = Path(__file__).resolve().parents[2]
        args = argparse.Namespace(resolution="1920x1080", fps=60, repeat=3, gpu_timing=False)
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "case.py"
            source.write_text("class Case: pass\n")
            scenes = [{"name": "Case", "file": str(source)}]
            first = make_report(args, scenes, root, "test")
            second = make_report(args, scenes, root, "other-time")
            self.assertEqual(first["workload_sha256"], second["workload_sha256"])
            source.write_text("class Case: count = 500\n")
            third = make_report(args, scenes, root, "test")
            self.assertNotEqual(first["workload_sha256"], third["workload_sha256"])


if __name__ == "__main__":
    unittest.main()
