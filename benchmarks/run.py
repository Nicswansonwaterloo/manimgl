#!/usr/bin/env python3
"""Render first/cached benchmarks and check every frame against the baseline."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import threading
import time

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCENES = HERE / "scenes"
WORKER = HERE / "support" / "worker.py"
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

from benchmarks.support.assets import prepare_assets
from benchmarks.support.reporting import CONSOLE, compare, make_report, print_results, save_report
from benchmarks.support.telemetry import monitor_resources


def discover(scene_file=None):
    scenes = []
    paths = [Path(scene_file).resolve()] if scene_file else sorted(SCENES.glob("*.py"))
    for path in paths:
        for node in ast.parse(path.read_text()).body:
            if isinstance(node, ast.ClassDef) and any(
                isinstance(base, ast.Name) and base.id in {"Scene", "ThreeDScene", "InteractiveScene"}
                for base in node.bases
            ):
                scenes.append({"name": node.name, "file": str(path.resolve()),
                               "description": ast.get_docstring(node) or ""})
    return scenes


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true", help="replace the baseline and compile its preview")
    parser.add_argument("--only", nargs="+", metavar="NAME", help="run selected scene names")
    args = parser.parse_args()
    if args.baseline and args.only:
        parser.error("--baseline builds the full suite; use --only for comparisons")
    args.resolution, args.fps, args.timeout = "854x480", 15, 300
    return args


def stop_process(process):
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif process.poll() is None:
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
    process.wait()


def run_one(scene, iteration, args, output, scratch, retained_clip):
    label = f"{scene['name']}-{iteration:02d}"
    log_path = output / "logs" / f"{label}.log"
    scene_cache = scratch / "scene-caches" / scene["name"]
    readings = {"rss": [], "gpu": {}}
    notes = set()
    timed_out = False
    with tempfile.TemporaryDirectory(prefix=label, dir=scratch) as temporary:
        temporary = Path(temporary)
        metrics_path = temporary / "metrics.json"
        config = {"directories": {"cache": str(scene_cache / "cache"),
                                  "subdirs": {"latex_cache": str(scene_cache / "latex")}},
                  "text": {"font": "sans-serif"}}
        config_path = temporary / "config.yml"
        config_path.write_text(yaml.safe_dump(config))
        command = [sys.executable, str(WORKER), str(HERE / scene["file"]), scene["name"],
                   "-w", "-q", "--resolution", args.resolution, "--fps", str(args.fps),
                   "--video_dir", str(temporary), "--file_name", scene["name"],
                   "--config_file", str(config_path), "--log-level", "WARNING"]
        capture = scratch / "captures" / f"{label}.rgba"
        capture.parent.mkdir(exist_ok=True)
        env = {**os.environ, "MANIM_BENCHMARK_CAPTURE": str(capture.resolve()), "MANIM_BENCHMARK_METRICS": str(metrics_path),
               "MPLCONFIGDIR": str(scene_cache / "matplotlib"),
               "MANIM_BENCHMARK_ASSETS": str(scratch / "assets"),
               "PYTHONDONTWRITEBYTECODE": "1",
               "PYTHONPATH": str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", "")}
        with log_path.open("w") as log:
            start = time.perf_counter()
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=os.name == "posix")
            stop = threading.Event()
            sampler = threading.Thread(target=monitor_resources,
                                       args=(process.pid, stop, readings, notes), daemon=True)
            sampler.start()
            try:
                process.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
            finally:
                wall = time.perf_counter() - start
                stop.set()
                stop_process(process)  # Also stops an encoder left behind by an exception.
                sampler.join()
        worker = json.loads(metrics_path.read_text()) if metrics_path.exists() else {}
        movie = temporary / f"{scene['name']}.mp4"
        success = (not timed_out and process.returncode == 0 and worker.get("completed")
                   and worker.get("scene") == scene["name"] and not worker.get("interrupted")
                   and worker.get("encoder_returncode") == 0 and worker.get("frames_written", 0) > 0
                   and movie.exists() and movie.stat().st_size > 0)
        if movie.exists() and retained_clip:
            shutil.copyfile(movie, retained_clip)  # Outside measured time.
    render_time = worker.get("scene_run_seconds")
    cpu_time = worker.get("cpu_seconds")
    utilization = [statistics.mean(device["utilization"]) for device in readings["gpu"].values()
                   if device["utilization"]]
    return {"name": scene["name"], "iteration": iteration, "phase": "first" if iteration == 1 else "cached",
            "status": "ok" if success else "timeout" if timed_out else "failed",
            "wall_seconds": wall, "render_seconds": render_time,
            "capture": str(capture.resolve()),
            "capture_frames": worker.get("capture_frames"),
            "capture_write_seconds": worker.get("capture_write_seconds"),
            "frames": worker.get("frames_written"),
            "render_fps": worker.get("frames_written", 0) / render_time if render_time else None,
            "cpu_percent": 100 * cpu_time / wall if cpu_time is not None else None,
            "tree_peak_mib": max(readings["rss"]) / 2**20 if readings["rss"] else None,
            "device_gpu_utilization_percent": utilization[0] if len(utilization) == 1 else None,
            "animation_seconds": worker.get("animation_seconds"), "msaa_samples": worker.get("msaa_samples"),
            "adapter": worker.get("adapter"),
            "log": str(log_path.relative_to(output))}


def prepare_validation(report, args, output):
    """Compress captured encoder input only after every timed run has finished."""
    import av
    from benchmarks.support.capture import encode_capture
    from benchmarks.support.visual import DEFAULT_TOLERANCES, inspect_video

    for measured in report["runs"]:
        errors = []
        try:
            if measured["status"] != "ok" or not measured.get("export_video"):
                raise ValueError("Timed export did not complete")
            info = inspect_video(output / measured["export_video"], measured, report,
                                 DEFAULT_TOLERANCES["duration_tolerance"])
            errors.extend(info["errors"])
            if measured.get("capture_frames") != measured.get("frames"):
                raise ValueError("Captured frame count differs from timed writer count")
            capture = output / measured["capture"]
            clip = output / "reference-videos" / capture.with_suffix(".mp4").name
            with CONSOLE.status(f"Compressing captured frames: {measured['name']} · {measured['phase']}"):
                encode_capture(capture, clip, args.resolution, args.fps, measured["frames"])
            measured["video"] = str(clip.relative_to(output))
            capture.unlink()
            measured.pop("capture")
        except (av.error.FFmpegError, OSError, ValueError, KeyError) as error:
            errors.append(str(error))
        if errors and measured.get("capture"):
            source = Path(measured["capture"])
            if source.exists():
                retained = output / "reference-videos" / source.name
                shutil.move(str(source), retained)
                measured["capture"] = str(retained.relative_to(output))
        measured["export_validation"] = {"passed": not errors, "errors": errors}
        save_report(report, output)


def compile_video(clips, destination, scratch, timeout):
    manifest = scratch / "concat.txt"
    manifest.write_text("".join(f"file '{clip.name}'\n" for clip in clips))
    partial = destination.with_name(destination.stem + "-partial.mp4")
    with (scratch / "concat.log").open("w") as log:
        process = subprocess.Popen(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "concat",
                                    "-safe", "1", "-i", str(manifest), "-an", "-c:v", "libx264",
                                    "-pix_fmt", "yuv420p", "-crf", "18", "-threads", "1",
                                    "-movflags", "+faststart", str(partial)],
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=os.name == "posix")
        try:
            process.wait(timeout=timeout)
            if process.returncode or not partial.exists() or not partial.stat().st_size:
                raise RuntimeError(f"Video compilation failed: {(scratch / 'concat.log').read_text()}")
            partial.replace(destination)
        finally:
            stop_process(process)
            partial.unlink(missing_ok=True)


def main():
    args = parse_args()
    scenes = discover()
    unknown = set(args.only or []) - {s["name"] for s in scenes}
    if unknown:
        raise ValueError(f"Unknown scenes: {', '.join(sorted(unknown))}")
    scenes = [s for s in scenes if not args.only or s["name"] in args.only]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    baseline_path = HERE / "results" / "baseline"
    output = baseline_path if args.baseline else HERE / "results" / timestamp
    report = make_report(args, scenes, ROOT, timestamp)
    from benchmarks.support.visual import DEFAULT_TOLERANCES, load_reference, validate_suite
    reference = None if args.baseline else load_reference(baseline_path, report)
    if args.baseline and output.exists():
        shutil.rmtree(output)
    for folder in ("logs", "reference-videos", "exports"):
        (output / folder).mkdir(parents=True)
    CONSOLE.rule("[bold cyan]ManimGL Render Benchmark")
    CONSOLE.print(f"{args.resolution} · {args.fps} fps · {len(scenes)} scenes · first + cached")
    CONSOLE.print("Default encoder + raw capture timings · every captured frame validated after timing")
    valid = False
    with tempfile.TemporaryDirectory(prefix="manim-benchmark-") as temporary:
        scratch = Path(temporary)
        try:
            prepare_assets(scratch / "assets")
            for number, scene in enumerate(scenes, 1):
                for iteration in (1, 2):
                    clip = output / "exports" / f"{scene['name']}-{iteration:02d}.mp4"
                    with CONSOLE.status(f"[{number}/{len(scenes)}] {scene['name']} · {'first' if iteration == 1 else 'cached'}"):
                        result = run_one(scene, iteration, args, output, scratch, clip)
                    report["runs"].append(result)
                    if clip.exists():
                        result["export_video"] = str(clip.relative_to(output))
                    if result["status"] != "ok":
                        CONSOLE.print(f"[red]{scene['name']}: {result['status']}[/red] · {output / result['log']}")
                    save_report(report, output)
            started = time.perf_counter()
            try:
                prepare_validation(report, args, output)
                with CONSOLE.status("Validating every frame"):
                    valid = validate_suite(report, output, DEFAULT_TOLERANCES, reference)
            finally:
                report["validation_seconds"] = time.perf_counter() - started
            if args.baseline and valid:
                clips = []
                for run in report["runs"]:
                    if run["phase"] == "first":
                        clip = scratch / f"{run['name']}.mp4"
                        shutil.copyfile(output / run["video"], clip)
                        clips.append(clip)
                with CONSOLE.status("Compiling baseline preview"):
                    compile_video(clips, output / "suite.mp4", scratch, args.timeout)
                report["video"] = "suite.mp4"
        except KeyboardInterrupt:
            report["interrupted"] = True
        finally:
            clean_successful_artifacts(report, output, args.baseline)
            save_report(report, output)
    print_results(report)
    CONSOLE.print(f"Visual checks: {'PASS' if valid else 'FAIL'} · {output}")
    for run in report["runs"]:
        if run.get("visual", {}).get("errors"):
            CONSOLE.print(f"[red]{run['name']} / {run['phase']}: {'; '.join(run['visual']['errors'])}[/red]")
    if reference and not report["interrupted"]:
        compare(baseline_path, output)
    if report.get("video"):
        CONSOLE.print(f"Baseline preview: {output / report['video']}")
    return 130 if report["interrupted"] else int(not valid)


def clean_successful_artifacts(report, output, baseline=False):
    first = {r["name"]: r for r in report["runs"] if r.get("phase") == "first"}
    for run in report["runs"]:
        if run["status"] != "ok" or run.get("visual", {}).get("passed") is not True:
            continue
        if run.get("log"):
            (output / run.pop("log")).unlink(missing_ok=True)
        if run.get("export_video"):
            (output / run.pop("export_video")).unlink(missing_ok=True)
        if baseline and run.get("phase") == "cached":
            source = first.get(run["name"], {})
            if not source.get("video") or source.get("visual", {}).get("passed") is not True:
                continue
        if run.get("video") and (not baseline or run.get("phase") == "cached"):
            (output / run.pop("video")).unlink(missing_ok=True)
            if baseline:
                source = first[run["name"]]
                run["video"] = source["video"]
                run["visual"]["sha256"] = source["visual"]["sha256"]
    for folder in (output / "logs", output / "reference-videos", output / "exports"):
        if folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        CONSOLE.print(f"[red]Benchmark error: {error}[/red]")
        sys.exit(2)
