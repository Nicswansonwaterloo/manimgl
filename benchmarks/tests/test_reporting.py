"""Guard performance comparisons against changed inputs and incomplete measurements."""
import argparse
from copy import deepcopy
import tempfile
from pathlib import Path
import unittest

from benchmarks.support.reporting import comparison_rows, make_report
from benchmarks.support import reporting
from unittest.mock import patch


class ReportingTests(unittest.TestCase):
    def test_two_tables_include_gpu_and_total_uses_minutes_seconds(self):
        runs = [{"name": "Case", "phase": phase, "status": "ok", "wall_seconds": 61.4}
                for phase in ("first", "cached")]
        with patch.object(reporting, "CONSOLE") as console:
            reporting.print_results({"runs": runs, "summary": reporting.summarize(runs)})
        tables = [call.args[0] for call in console.print.call_args_list
                  if isinstance(call.args[0], reporting.Table)]
        self.assertEqual(len(tables), 2)
        self.assertTrue(all("GPU %" in [c.header for c in table.columns] for table in tables))
        self.assertIn("2m 03s", console.print.call_args.args[0])

    def report(self, seconds=10):
        return {"schema_version": 6, "resolution": "1920x1080", "fps": 60,
                "encoding": {"crf": 23}, "workload_sha256": "same",
                "phases": ["first", "cached"], "scenes": [{"name": "Case"}], "interrupted": False,
                "summary": [{"name": "Case", "phase": phase, "status": "ok",
                             "render_seconds": seconds, "wall_seconds": seconds + 2} for phase in ("first", "cached")]}

    def test_negative_means_faster_and_positive_means_slower(self):
        baseline = self.report()
        self.assertAlmostEqual(comparison_rows(baseline, self.report(8))[0]["render_change_percent"], -20)
        self.assertAlmostEqual(comparison_rows(baseline, self.report(12))[0]["render_change_percent"], 20)

    def test_different_workloads_or_settings_are_rejected(self):
        baseline = self.report()
        for field, different in [("workload_sha256", "changed"), ("fps", 30),
                                 ("resolution", "640x360"),
                                 ("encoding", {"crf": 0})]:
            candidate = deepcopy(baseline)
            candidate[field] = different
            with self.assertRaisesRegex(ValueError, field):
                comparison_rows(baseline, candidate)

    def test_failed_or_partial_repetitions_have_no_percentage(self):
        baseline, candidate = self.report(), self.report(2)
        candidate["summary"][0]["status"] = "failed"
        self.assertIsNone(comparison_rows(baseline, candidate)[0]["render_change_percent"])
        candidate["summary"][0]["status"] = "timeout"
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
        args = argparse.Namespace(resolution="1920x1080", fps=60)
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
