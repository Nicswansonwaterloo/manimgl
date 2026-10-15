"""Accounting, cleanup and movie joining checks that do not need a graphics adapter."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import run
from benchmarks.support import reporting, telemetry


class RunnerTests(unittest.TestCase):
    def test_cleanup_keeps_baseline_and_failures_but_removes_successful_candidates(self):
        for baseline in (False, True):
            with tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary)
                (output / "logs").mkdir()
                (output / "videos").mkdir()
                runs = []
                for name, status, valid in [("good", "ok", True), ("render", "failed", False),
                                             ("visual", "ok", False), ("unchecked", "ok", None)]:
                    log, video = f"logs/{name}.log", f"videos/{name}.mp4"
                    (output / log).write_text("log")
                    (output / video).write_bytes(b"video")
                    runs.append(dict(name=name, status=status, visual={"passed": valid}, log=log, video=video))
                run.clean_successful_artifacts({"runs": runs}, output, baseline)
                self.assertFalse((output / "logs/good.log").exists())
                self.assertEqual((output / "videos/good.mp4").exists(), baseline)
                for name in ("render", "visual", "unchecked"):
                    self.assertTrue((output / f"logs/{name}.log").exists())
                    self.assertTrue((output / f"videos/{name}.mp4").exists())

    def test_cli_has_only_baseline_and_scene_selection(self):
        with patch("sys.argv", ["run.py", "--only", "Solids3D"]):
            self.assertEqual(run.parse_args().only, ["Solids3D"])
        for arguments in (["--compile-video"], ["--output", "x"], ["--baseline", "--only", "A"]):
            with patch("sys.argv", ["run.py", *arguments]), self.assertRaises(SystemExit):
                run.parse_args()

    def test_baseline_cleanup_shares_one_reference(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            runs = []
            for phase in ("first", "cached"):
                (output / f"{phase}.mp4").write_bytes(phase.encode())
                runs.append(dict(name="Case", phase=phase, status="ok", video=f"{phase}.mp4",
                                 visual={"passed": True, "sha256": phase}))
            run.clean_successful_artifacts({"runs": runs}, output, True)
            self.assertEqual(list(output.iterdir()), [output / "first.mp4"])
            self.assertEqual(runs[1]["video"], runs[0]["video"])
            self.assertEqual(runs[1]["visual"]["sha256"], "first")

    def test_failed_first_baseline_keeps_cached_diagnostic(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / "cached.mp4").write_bytes(b"movie")
            runs = [dict(name="Case", phase="first", status="failed", visual={"passed": False}),
                    dict(name="Case", phase="cached", status="ok", video="cached.mp4",
                         visual={"passed": True})]
            run.clean_successful_artifacts({"runs": runs}, output, True)
            self.assertTrue((output / "cached.mp4").exists())

    def test_baseline_replaces_results_separates_timing_and_compiles(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "results" / "baseline"
            output.mkdir(parents=True)
            (output / "stale.txt").write_text("disposable")
            args = argparse.Namespace(baseline=True, only=None, resolution="854x480", fps=15, timeout=300)
            report = {"runs": [], "interrupted": False}
            def render(scene, iteration, args, output, scratch, clip, *, lossless=False):
                clip.write_bytes(b"movie")
                return dict(name=scene["name"], iteration=iteration, phase="first" if iteration == 1 else "cached",
                            status="ok", wall_seconds=100 if lossless else 1)
            def validate(report, *args):
                for row in report["runs"]:
                    row["visual"] = {"passed": True, "sha256": "same"}
                return True
            with patch.object(run, "HERE", root), patch.object(run, "parse_args", return_value=args), \
                 patch.object(run, "discover", return_value=[{"name": "Case"}]), \
                 patch.object(run, "make_report", return_value=report), \
                 patch.object(run, "prepare_assets"), patch.object(run, "save_report"), \
                 patch.object(run, "print_results"), patch.object(run, "CONSOLE"), \
                 patch.object(run, "run_one", side_effect=render) as render_mock, \
                 patch.object(run, "compile_video") as compile_mock, \
                 patch("benchmarks.support.visual.inspect_video", return_value={"errors": []}), \
                 patch("benchmarks.support.visual.validate_suite", side_effect=validate):
                self.assertEqual(run.main(), 0)
            self.assertEqual(render_mock.call_count, 4)
            self.assertEqual([c.kwargs.get("lossless", False) for c in render_mock.call_args_list],
                             [False, False, True, True])
            self.assertNotEqual(render_mock.call_args_list[0].args[4], render_mock.call_args_list[2].args[4])
            self.assertEqual([r["wall_seconds"] for r in report["runs"]], [1, 1])
            self.assertEqual([r["validation_render"]["wall_seconds"] for r in report["runs"]], [100, 100])
            compile_mock.assert_called_once()
            self.assertEqual(compile_mock.call_args.args[1], output / "suite.mp4")
            self.assertFalse((output / "stale.txt").exists())
            self.assertEqual(len(list((output / "reference-videos").iterdir())), 1)

    def test_forty_nine_distinct_workloads(self):
        scenes = run.discover()
        self.assertEqual(len(scenes), 49)
        self.assertEqual(len({s["name"] for s in scenes}), 49)
        self.assertTrue({"WaveLattice500", "DepthCity500", "OrbitalSwarm600", "MovingLight3D"}
                        <= {s["name"] for s in scenes})
        self.assertTrue({"BreadthFirstSearchGraph", "HilbertSpaceFilling3D", "ClothWindSimulation3D",
                         "GalaxyMergerNBody3D", "ReactionDiffusionLaboratory"} <= {s["name"] for s in scenes})
        self.assertTrue({"EllipticChordBuild", "EllipticDotSquiggle", "TernaryFormCloud",
                         "TernaryTetrahedronWalk", "ArithmeticSemicircleSweep", "ComplexSquareRedraw",
                         "LinearRankCollapse", "SpanningVectorRedraw"} <= {s["name"] for s in scenes})
        self.assertFalse({"GeometryGrid", "PathMorphs", "UpdaterGrid", "SVGPaths", "ImageTiles"}
                         & {s["name"] for s in scenes})

    def test_summary_keeps_first_and_cached_separate(self):
        rows = reporting.summarize([
            {"name": "Case", "phase": "first", "status": "ok", "wall_seconds": 10},
            {"name": "Case", "phase": "cached", "status": "ok", "wall_seconds": 2},
        ])
        self.assertEqual([row["wall_seconds"] for row in rows], [10, 2])
        self.assertEqual([row["phase"] for row in rows], ["first", "cached"])

    def test_builtin_example_discovery(self):
        scenes = run.discover(run.ROOT / "example_scenes.py")
        self.assertTrue({"TextExample", "AnimatingMethods", "SurfaceExample"}
                        <= {scene["name"] for scene in scenes})
        self.assertTrue(all(Path(scene["file"]).is_absolute() for scene in scenes))

    def test_gpu_summary_preserves_unavailable_and_excludes_failures(self):
        rows = reporting.summarize([
            {"name": "Case", "phase": "first", "status": "ok", "device_gpu_utilization_percent": None},
            {"name": "Case", "phase": "cached", "status": "failed", "device_gpu_utilization_percent": 99},
        ])
        self.assertTrue(all(row["device_gpu_utilization_percent"] is None for row in rows))

    def test_apple_telemetry_skips_missing_and_invalid_counters(self):
        import plistlib

        entries = [{"IORegistryEntryID": 7, "IOClass": "AGXAccelerator", "PerformanceStatistics": {"Device Utilization %": 42}},
                   {"PerformanceStatistics": {}},
                   {"PerformanceStatistics": {"Device Utilization %": 999}}]
        with patch.object(telemetry.subprocess, "run", return_value=argparse.Namespace(stdout=plistlib.dumps(entries))):
            self.assertEqual(telemetry.apple_gpu_samples(), [{"id": "ioreg:7", "name": "AGXAccelerator", "utilization": 42.0}])

    def exercise_subprocess(self, mode, lossless=False):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            harness = root / "harness"
            harness.mkdir()
            (harness / "worker.py").write_text('''import json, os, pathlib, sys, time, yaml
args = sys.argv
config = yaml.safe_load(pathlib.Path(args[args.index("--config_file") + 1]).read_text())
expected_lossless = ''' + repr(lossless) + '''
if expected_lossless:
    assert config["file_writer"] == {"video_codec": "libx264rgb", "pixel_format": "rgb24", "crf": 0}
else:
    assert "file_writer" not in config
movies = pathlib.Path(args[args.index("--video_dir") + 1])
(movies / "Case.mp4").write_bytes(b"movie bytes")
mode = ''' + repr(mode) + '''
if mode == "timeout":
    time.sleep(10)
if mode == "failure":
    sys.exit(7)
metrics = {"completed": True, "scene": "Case", "frames_written": 2,
           "encoder_returncode": 3 if mode == "encoder_failure" else 0,
           "scene_run_seconds": 0.01, "cpu_seconds": 0.01}
pathlib.Path(os.environ["MANIM_BENCHMARK_METRICS"]).write_text(json.dumps(metrics))
''')
            output = root / "output"
            scratch = root / "scratch"
            output.mkdir()
            (output / "logs").mkdir()
            scratch.mkdir()
            args = argparse.Namespace(resolution="320x180", fps=10,
                                      timeout=0.2 if mode == "timeout" else 10)
            clip = scratch / "retained.mp4"
            with patch.object(run, "WORKER", harness / "worker.py"):
                result = run.run_one({"name": "Case", "file": "case.py"}, 1, args, output, scratch, clip, lossless=lossless)
            self.assertEqual(list(scratch.iterdir()), [clip])
            self.assertTrue((output / result["log"]).exists())
            return result

    def test_success_deletes_original_movie_and_retains_only_join_input(self):
        self.assertEqual(self.exercise_subprocess("success")["status"], "ok")

    def test_lossless_render_uses_separate_encoder(self):
        self.assertEqual(self.exercise_subprocess("success", lossless=True)["status"], "ok")

    def test_failure_deletes_partial_movie(self):
        self.assertEqual(self.exercise_subprocess("failure")["status"], "failed")

    def test_encoder_failure_is_not_a_success(self):
        self.assertEqual(self.exercise_subprocess("encoder_failure")["status"], "failed")

    def test_timeout_terminates_process_and_deletes_movie(self):
        self.assertEqual(self.exercise_subprocess("timeout")["status"], "timeout")

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg unavailable")
    def test_combined_movie_decodes_all_frames_in_order(self):
        import av
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            clips = []
            for index, color in enumerate(["red", "blue"]):
                clip = folder / f"clip-{index}.mp4"
                subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "lavfi",
                                "-i", f"color=c={color}:s=32x32:r=10", "-frames:v", "3",
                                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clip)],
                               check=True, capture_output=True)
                clips.append(clip)
            destination = folder / "joined.mp4"
            run.compile_video(clips, destination, folder, 10)
            with av.open(str(destination)) as container:
                frames = [frame.to_ndarray(format="rgb24") for frame in container.decode(video=0)]
            self.assertEqual(len(frames), 6)
            self.assertGreater(frames[0][0, 0, 0], 200)
            self.assertGreater(frames[-1][0, 0, 2], 200)
            self.assertFalse((folder / "joined-partial.mp4").exists())


if __name__ == "__main__":
    unittest.main()
