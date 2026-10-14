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
    def test_thirty_five_distinct_workloads(self):
        scenes = run.discover()
        self.assertEqual(len(scenes), 35)
        self.assertEqual(len({s["name"] for s in scenes}), 35)
        self.assertTrue({"WaveLattice500", "DepthCity500", "OrbitalSwarm600", "MovingLight3D"}
                        <= {s["name"] for s in scenes})
        self.assertTrue({"BreadthFirstSearchGraph", "HilbertSpaceFilling3D", "ClothWindSimulation3D",
                         "GalaxyMergerNBody3D", "ReactionDiffusionLaboratory"} <= {s["name"] for s in scenes})
        self.assertFalse({"GeometryGrid", "PathMorphs", "UpdaterGrid", "SVGPaths", "ImageTiles"}
                         & {s["name"] for s in scenes})

    def test_summary_excludes_failed_measurements(self):
        def invocation(seconds, status="ok"):
            return {"name": "Case", "status": status,
                    **dict.fromkeys(["wall_seconds", "render_seconds", "render_fps", "cpu_percent",
                                     "tree_peak_mib", "worker_peak_mib"], seconds)}
        summary = reporting.summarize([invocation(2), invocation(4), invocation(99, "failed")])[0]
        self.assertEqual(summary["wall_seconds"], 3)
        self.assertEqual(summary["passed"], 2)
        self.assertEqual(summary["failed"], 1)

    def test_builtin_example_discovery(self):
        scenes = run.discover(run.ROOT / "example_scenes.py")
        self.assertTrue({"TextExample", "AnimatingMethods", "SurfaceExample"}
                        <= {scene["name"] for scene in scenes})
        self.assertTrue(all(Path(scene["file"]).is_absolute() for scene in scenes))

    def test_gpu_summary_does_not_confirm_missing_or_failed_evidence(self):
        def invocation(confirmed, status="ok"):
            return {"name": "Case", "status": status, "adapter": {"backend_type": "Metal"},
                    "gpu_rendering": {"hardware_rendering_confirmed": confirmed},
                    "gpu_render_passes": 100, "gpu_pass_mean_ms": 0.25}
        row = reporting.summarize([invocation(True), invocation(False, "failed")])[0]
        self.assertTrue(row["gpu_confirmed"])
        self.assertEqual(row["backend"], "Metal")
        self.assertEqual(row["gpu_pass_mean_ms"], 0.25)
        row = reporting.summarize([invocation(True), invocation(False)])[0]
        self.assertFalse(row["gpu_confirmed"])

    def test_apple_telemetry_skips_missing_and_invalid_counters(self):
        import plistlib

        entries = [{"IORegistryEntryID": 7, "IOClass": "AGXAccelerator", "PerformanceStatistics": {"Device Utilization %": 42}},
                   {"PerformanceStatistics": {}},
                   {"PerformanceStatistics": {"Device Utilization %": 999}}]
        with patch.object(telemetry.subprocess, "run", return_value=argparse.Namespace(stdout=plistlib.dumps(entries))):
            self.assertEqual(telemetry.apple_gpu_samples(), [{"id": "ioreg:7", "name": "AGXAccelerator", "utilization": 42.0}])

    def exercise_subprocess(self, mode):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            harness = root / "harness"
            harness.mkdir()
            (harness / "worker.py").write_text('''import json, os, pathlib, sys, time
args = sys.argv
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
                result = run.run_one({"name": "Case", "file": "case.py"}, 1, args, output, scratch, clip)
            self.assertEqual(list(scratch.iterdir()), [clip] if mode == "success" else [])
            self.assertTrue((output / result["log"]).exists())
            self.assertTrue(result["movies_deleted"])
            return result

    def test_success_deletes_original_movie_and_retains_only_join_input(self):
        self.assertEqual(self.exercise_subprocess("success")["status"], "ok")

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
