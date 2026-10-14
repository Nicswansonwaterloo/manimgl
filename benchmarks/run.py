#!/usr/bin/env python3
"""Render benchmarks sequentially, or compare two saved runs."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import fnmatch
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


def positive_int(value):
    value = int(value)
    if value < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return value


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--compare", nargs=2, type=Path, metavar=("BASELINE", "CANDIDATE"),
                        help="compare two result directories or results.json files; no rendering")
    parser.add_argument("--scene-file", type=Path, help="benchmark scenes from a file, e.g. example_scenes.py")
    parser.add_argument("--only", nargs="+", metavar="NAME", help="scene names or quoted globs")
    parser.add_argument("--resolution", default="854x480")
    parser.add_argument("--fps", type=positive_int, default=15)
    parser.add_argument("--timeout", type=positive_int, default=300, help="seconds per scene")
    parser.add_argument("--output", type=Path, help="new directory for JSON, CSV and logs")
    parser.add_argument("--compile-video", action="store_true", help="keep suite.mp4 inside the result directory")
    parser.add_argument("--baseline", action="store_true",
                        help="create the visual reference; subsequent normal runs check it automatically")
    args = parser.parse_args()
    if args.baseline and (args.compare or args.output or args.only or args.scene_file):
        parser.error("--baseline creates the complete built-in suite at its standard location; use it on its own")
    try:
        width, height = map(int, args.resolution.split("x"))
        if min(width, height) < 2 or width % 2 or height % 2:
            raise ValueError
    except ValueError:
        parser.error("--resolution requires even dimensions, for example 1920x1080")
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


def run_one(scene, iteration, args, output, scratch, retained_clip=None):
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
                  "text": {"font": "sans-serif"},
                  "file_writer": {"video_codec": "libx264", "pixel_format": "yuv420p", "crf": 23}}
        config_path = temporary / "config.yml"
        config_path.write_text(yaml.safe_dump(config))
        command = [sys.executable, str(WORKER), str(HERE / scene["file"]), scene["name"],
                   "-w", "-q", "--resolution", args.resolution, "--fps", str(args.fps),
                   "--video_dir", str(temporary), "--file_name", scene["name"],
                   "--config_file", str(config_path), "--log-level", "WARNING"]
        env = {**os.environ, "MANIM_BENCHMARK_METRICS": str(metrics_path),
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
        size = movie.stat().st_size if movie.exists() else 0
        if success and retained_clip:
            shutil.copyfile(movie, retained_clip)  # Outside measured time.
    gpu = [{"id": uuid, "uuid": uuid if values["provider"] == "nvidia-smi" else None,
            "name": values["name"], "provider": values["provider"], "scope": "device-wide",
            "samples": len(values["utilization"]),
            "mean_utilization_percent": statistics.mean(values["utilization"]) if values["utilization"] else None} for uuid, values in readings["gpu"].items()]
    render_time = worker.get("scene_run_seconds")
    cpu_time = worker.get("cpu_seconds")
    utilization = [device["mean_utilization_percent"] for device in gpu if device["mean_utilization_percent"] is not None]
    return {"name": scene["name"], "iteration": iteration, "phase": "first" if iteration == 1 else "cached",
            "status": "ok" if success else "timeout" if timed_out else "failed",
            "wall_seconds": wall, "render_seconds": render_time,
            "frames": worker.get("frames_written"),
            "render_fps": worker.get("frames_written", 0) / render_time if render_time else None,
            "cpu_percent": 100 * cpu_time / wall if cpu_time is not None else None,
            "tree_peak_mib": max(readings["rss"]) / 2**20 if readings["rss"] else None,
            "worker_peak_mib": worker.get("worker_peak_rss_bytes", 0) / 2**20 if worker.get("worker_peak_rss_bytes") else None,
            "gpu": gpu or None, "notes": sorted(notes), "video_bytes": size, "movies_deleted": True,
            "adapter": worker.get("adapter"),
            # A single device can be displayed unambiguously. Multi-GPU readings
            # remain per-device in JSON instead of conflating unrelated adapters.
            "device_gpu_utilization_percent": utilization[0] if len(gpu) == 1 and utilization else None,
            "import_seconds": worker.get("import_seconds"), "scene_init_seconds": worker.get("scene_init_seconds"),
            "animation_seconds": worker.get("animation_seconds"), "msaa_samples": worker.get("msaa_samples"),
            "log": str(log_path.relative_to(output))}


def compile_video(clips, destination, scratch, timeout):
    manifest = scratch / "concat.txt"
    manifest.write_text("".join(f"file '{clip.name}'\n" for clip in clips))
    partial = destination.with_name(destination.stem + "-partial.mp4")
    with (scratch / "concat.log").open("w") as log:
        process = subprocess.Popen(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "concat",
                                    "-safe", "1", "-i", str(manifest), "-c", "copy", "-movflags", "+faststart", str(partial)],
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
    if args.compare:
        compare(*args.compare)
        return 0
    scenes = discover(args.scene_file)
    for pattern in args.only or []:
        if not any(fnmatch.fnmatchcase(scene["name"], pattern) for scene in scenes):
            raise ValueError(f"No scene matches {pattern!r}; use --list")
    scenes = [scene for scene in scenes if not args.only or any(
        fnmatch.fnmatchcase(scene["name"], pattern) for pattern in args.only)]
    if not scenes:
        raise ValueError("No benchmark scenes found")
    if args.list:
        for scene in scenes:
            CONSOLE.print(f"{scene['name']:27} {scene['description']}")
        return 0
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    visual_baseline = getattr(args, "baseline", False)
    baseline_path = HERE / "results" / "visual-baseline"
    output = (baseline_path if visual_baseline else args.output or HERE / "results" / timestamp).resolve()
    report = make_report(args, scenes, ROOT, timestamp)
    reference = None
    from benchmarks.support.visual import DEFAULT_TOLERANCES, load_reference, validate_suite
    tolerances = dict(DEFAULT_TOLERANCES)
    if not visual_baseline:
        # Fail before rendering if this isn't a compatible, intact reference.
        reference = load_reference(baseline_path, report)
    elif output.exists():
        raise ValueError("A visual baseline already exists. Move it aside before creating a replacement.")
    output.mkdir(parents=True, exist_ok=False)
    (output / "logs").mkdir()
    (output / "videos").mkdir()
    CONSOLE.rule("[bold cyan]ManimGL Render Benchmark")
    CONSOLE.print(f"[bold]{args.resolution} · {args.fps} fps · {len(scenes)} scenes · first run + cached repeat[/bold]\n"
                  "One renderer at a time · movie encoding included · temporary data deleted")
    CONSOLE.print("Both scene movies retained · visual checks run after all timed renders")
    clips = {}
    failed = False
    with tempfile.TemporaryDirectory(prefix="manim-benchmark-") as temporary:
        scratch = Path(temporary)
        try:
            if not args.scene_file:
                prepare_assets(scratch / "assets")
            for number, scene in enumerate(scenes, 1):
                for iteration in (1, 2):
                    clip = output / "videos" / f"{scene['name']}-{iteration:02d}.mp4"
                    phase_label = "first run" if iteration == 1 else "cached repeat"
                    with CONSOLE.status(f"[{number}/{len(scenes)}] {scene['name']} · {phase_label}"):
                        result = run_one(scene, iteration, args, output, scratch, clip)
                    report["runs"].append(result)
                    if result["status"] == "ok":
                        result["video"] = str(clip.relative_to(output))
                        result["movies_deleted"] = False
                    if len(report["runs"]) == 1 and result.get("adapter"):
                        adapter = result["adapter"]
                        CONSOLE.print(f"GPU: {adapter.get('device')} · {adapter.get('backend_type')}")
                    if args.compile_video and result["status"] == "ok" and scene["name"] not in clips:
                        # The concat manifest uses filenames in the scratch directory.
                        join_clip = scratch / f"{number:02d}-{scene['name']}.mp4"
                        shutil.copyfile(clip, join_clip)
                        clips[scene["name"]] = join_clip
                    if result["status"] != "ok":
                        CONSOLE.print(f"[red]{scene['name']}: {result['status']}[/red] · {output / result['log']}")
                    save_report(report, output)
            if args.compile_video:
                if len(clips) != len(scenes):
                    failed = True
                    report["compilation_error"] = "Some selected scenes had no successful render"
                    CONSOLE.print("[red]Combined video skipped: some scenes failed.[/red]")
                else:
                    compile_video([clips[scene["name"]] for scene in scenes], output / "suite.mp4", scratch, args.timeout)
                    report["video"] = "suite.mp4"
        except KeyboardInterrupt:
            report["interrupted"] = True
        finally:
            save_report(report, output)
    print_results(report)
    if not report["interrupted"]:
        try:
            with CONSOLE.status("Checking decoded videos (outside render timings)"):
                valid = validate_suite(report, output, tolerances, reference)
            failed = failed or not valid
            CONSOLE.print(f"Visual {'comparison' if reference else 'reference checks'}: "
                          f"{'PASS' if valid else 'FAIL'} · {output / 'validation.json'}")
            for run in report["runs"]:
                if run.get("visual", {}).get("passed") is False:
                    CONSOLE.print(f"[red]{run['name']} / {run['phase']}: "
                                  f"{'; '.join(run['visual']['errors'])}[/red]")
            if visual_baseline and valid:
                CONSOLE.print("Review the retained videos before accepting this reference as visually correct.")
        except KeyboardInterrupt:
            report["interrupted"] = True
        finally:
            save_report(report, output)
    CONSOLE.print(f"Reports: {output}")
    if report.get("video"):
        CONSOLE.print(f"Combined video: {output / report['video']}")
    return 130 if report["interrupted"] else int(failed or any(run["status"] != "ok" for run in report["runs"]))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        CONSOLE.print(f"[red]Benchmark error: {error}[/red]")
        sys.exit(2)
