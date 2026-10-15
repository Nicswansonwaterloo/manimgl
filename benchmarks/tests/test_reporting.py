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
    def test_single_table_includes_cached_wall_gpu_and_total_minutes_seconds(self):
        runs = [{"name": "Case", "phase": phase, "status": "ok", "wall_seconds": 61.4}
                for phase in ("first", "cached")]
        with patch.object(reporting, "CONSOLE") as console:
            reporting.print_results({"runs": runs, "summary": reporting.summarize(runs), "validation_seconds": 65})
        tables = [call.args[0] for call in console.print.call_args_list
                  if isinstance(call.args[0], reporting.Table)]
        self.assertEqual(len(tables), 1)
        self.assertIn("Cached wall s", [c.header for c in tables[0].columns])
        self.assertTrue(all("GPU %" in [c.header for c in table.columns] for table in tables))
        self.assertIn("2m 03s", console.print.call_args.args[0])
        self.assertIn("Validation: 1m 05s", console.print.call_args.args[0])

    def test_saved_report_contains_no_duplicate_measurements(self):
        import json
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = {"scenes": [{"name": "Case", "file": "unused", "description": "unused"}],
                      "runs": [{"name": "Case", "phase": "first", "status": "ok",
                                "wall_seconds": 1.25, "visual": {"passed": True}}]}
            reporting.save_report(report, root)
            self.assertEqual([p.name for p in root.iterdir()], ["results.json"])
            saved = json.loads((root / "results.json").read_text())
            self.assertNotIn("summary", saved)
            self.assertEqual(saved["scenes"], [{"name": "Case"}])
            self.assertEqual(reporting.summarize(saved["runs"]), report["summary"])

    def test_display_averages_resources_but_preserves_separate_timings(self):
        runs = [{"name": "Case", "phase": phase, "status": "ok", "wall_seconds": seconds,
                 "render_seconds": seconds - 1, "render_fps": seconds,
                 "cpu_percent": seconds * 10, "tree_peak_mib": seconds * 100,
                 "device_gpu_utilization_percent": seconds}
                for phase, seconds in [("first", 10), ("cached", 4)]]
        summary = reporting.summarize(runs)
        row = reporting.display_rows(summary)[0]
        self.assertEqual((row["wall_seconds"], row["cached_wall_seconds"]), (10, 4))
        self.assertEqual((row["render_seconds"], row["render_fps"]), (9, 10))
        self.assertEqual((row["cpu_percent"], row["tree_peak_mib"], row["device_gpu_utilization_percent"]), (70, 700, 7))
        self.assertEqual(summary[0]["cpu_percent"], 100)
        summary[1]["device_gpu_utilization_percent"] = None
        self.assertIsNone(reporting.display_rows(summary)[0]["device_gpu_utilization_percent"])
        summary[1]["status"] = "failed"
        row = reporting.display_rows(summary)[0]
        self.assertEqual(row["status"], "ok/failed")
        self.assertIsNone(row["cpu_percent"])

    def report(self, seconds=10):
        return {"schema_version": 7, "resolution": "1920x1080", "fps": 60,
                "encoding": {"crf": 23}, "workload_sha256": "same",
                "phases": ["first", "cached"], "scenes": [{"name": "Case"}], "interrupted": False,
                "summary": [{"name": "Case", "phase": phase, "status": "ok",
                             "render_seconds": seconds, "wall_seconds": seconds + 2} for phase in ("first", "cached")]}

    def test_negative_means_faster_and_positive_means_slower(self):
        baseline = self.report()
        self.assertAlmostEqual(comparison_rows(baseline, self.report(8))[0]["render_change_percent"], -20)
        self.assertAlmostEqual(comparison_rows(baseline, self.report(12))[0]["render_change_percent"], 20)

    def test_selected_scenes_compare_against_full_baseline(self):
        baseline, candidate = self.report(), self.report(8)
        baseline["scenes"].append({"name": "Other"})
        baseline["summary"] += [{**row, "name": "Other"} for row in baseline["summary"]]
        baseline["scene_sha256"] = {"Case": "same", "Other": "other"}
        candidate["scene_sha256"] = {"Case": "same"}
        candidate["workload_sha256"] = "subset"
        self.assertEqual(len(comparison_rows(baseline, candidate)), 2)
        candidate["scene_sha256"]["Case"] = "changed"
        with self.assertRaisesRegex(ValueError, "workload_sha256"):
            comparison_rows(baseline, candidate)

    def test_different_workloads_or_settings_are_rejected(self):
        baseline = self.report()
        for field, different in [("workload_sha256", "changed"), ("fps", 30),
                                 ("resolution", "640x360"),
                                 ("encoding", {"crf": 0})]:
            candidate = deepcopy(baseline)
            candidate[field] = different
            with self.assertRaisesRegex(ValueError, field):
                comparison_rows(baseline, candidate)

    def test_old_lossless_timings_cannot_compare_with_default_exports(self):
        old, new = self.report(), self.report()
        new["timing_protocol"] = "default-export-separate-lossless-v1"
        with self.assertRaisesRegex(ValueError, "timing_protocol"):
            comparison_rows(old, new)

    def test_new_timings_require_explicit_validation_success(self):
        old, new = self.report(), self.report(8)
        for report in (old, new):
            report["timing_protocol"] = "default-export-separate-lossless-v1"
        self.assertIsNone(comparison_rows(old, new)[0]["render_change_percent"])
        for report in (old, new):
            for row in report["summary"]:
                row["visual_passed"] = True
        self.assertAlmostEqual(comparison_rows(old, new)[0]["render_change_percent"], -20)

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
