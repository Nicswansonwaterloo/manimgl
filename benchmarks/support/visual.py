"""Post-render validation of decoded video frames; never part of timed rendering."""
from itertools import zip_longest
import hashlib
import json
from pathlib import Path

import av
import numpy as np
from PIL import Image


DEFAULT_TOLERANCES = {
    "pixel_tolerance": 12,
    "max_changed_fraction": 0.001,
    "max_mean_error": 0.5,
    "duration_tolerance": 0.001,
}


def checksum(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def video_path(root, run):
    path = (root / run["video"]).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Video path escapes its result directory")
    return path


def inspect_video(path, run, report, duration_tolerance):
    """Decode all frames, checking output against worker accounting and playback time."""
    width, height = map(int, report["resolution"].split("x"))
    fps = report["fps"]
    count = 0
    errors = []
    last_time = None
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        if stream.average_rate is None or abs(float(stream.average_rate) - fps) > 1e-6:
            errors.append("Encoded frame rate differs from requested FPS")
        for frame in container.decode(stream):
            if (frame.width, frame.height) != (width, height):
                if "Frame dimensions differ" not in errors:
                    errors.append("Frame dimensions differ")
            timestamp = float(frame.pts * frame.time_base) if frame.pts is not None else None
            if timestamp is None or abs(timestamp - count / fps) > duration_tolerance:
                if "Frame timestamps differ from requested cadence" not in errors:
                    errors.append("Frame timestamps differ from requested cadence")
            last_time = timestamp
            count += 1
        duration = last_time + 1 / fps if last_time is not None else None
        if stream.duration is None:
            errors.append("Encoded duration is unavailable")
        elif duration is None or abs(float(stream.duration * stream.time_base) - duration) > duration_tolerance:
            errors.append("Encoded duration differs from decoded frame timeline")
    if count == 0 or count != run.get("frames"):
        errors.append("Decoded frame count differs from worker frame count or is zero")
    animation = run.get("animation_seconds")
    # Playback durations can round to a whole frame; larger discrepancies are invalid.
    if animation is None or duration is None or abs(duration - animation) > 1 / fps + duration_tolerance:
        errors.append("Decoded duration differs from scene animation duration")
    return {"frames": count, "duration_seconds": duration, "errors": errors,
            "sha256": checksum(path)}


def load_reference(path, candidate):
    root = path if path.is_dir() else path.parent
    source = path / "results.json" if path.is_dir() else path
    if not source.is_file():
        raise ValueError("Create the visual reference first: python benchmarks/run.py --baseline")
    baseline = json.loads(source.read_text())
    for key in ("schema_version", "resolution", "fps", "phases", "config_sha256"):
        if baseline.get(key) != candidate.get(key):
            raise ValueError(f"Visual baseline {key} differs; use identical workloads and render settings")
    if baseline.get("validation_encoding", baseline.get("encoding")) != candidate.get("validation_encoding", candidate.get("encoding")):
        raise ValueError("Visual baseline validation encoding differs")
    if baseline.get("interrupted") or not baseline.get("visual_reference", {}).get("passed"):
        raise ValueError("Baseline is not a complete visual reference; generate it with --baseline")
    for scene in candidate["scenes"]:
        name = scene["name"]
        if not candidate.get("scene_sha256", {}).get(name) or baseline.get("scene_sha256", {}).get(name) != candidate["scene_sha256"][name]:
            raise ValueError(f"Visual baseline workload differs for {name}; use unchanged benchmark scenes")
    expected = {(s["name"], phase) for s in candidate["scenes"] for phase in candidate["phases"]}
    runs = baseline["runs"]
    baseline_expected = {(s["name"], phase) for s in baseline["scenes"] for phase in baseline["phases"]}
    if len(runs) != len(baseline_expected) or {(r["name"], r["phase"]) for r in runs} != baseline_expected or not expected <= baseline_expected:
        raise ValueError("Visual baseline scene/phase set differs")
    for run in runs:
        if run["status"] != "ok" or not run.get("visual", {}).get("passed"):
            raise ValueError("Visual baseline contains a failed or unchecked render")
        movie = video_path(root, run)
        if not movie.is_file() or checksum(movie) != run["visual"]["sha256"]:
            raise ValueError(f"Baseline video missing or changed: {run['name']} / {run['phase']}")
    return root, baseline


def frame_metrics(reference, candidate, tolerances):
    difference = np.abs(reference.astype(np.int16) - candidate.astype(np.int16))
    changed_fraction = float(np.mean(np.max(difference, axis=2) > tolerances["pixel_tolerance"]))
    mean_error = float(np.mean(difference))
    failed = (changed_fraction > tolerances["max_changed_fraction"] or
              mean_error > tolerances["max_mean_error"])
    return difference, changed_fraction, mean_error, failed


def compare_video(reference, candidate, destination, tolerances):
    """Stream every frame pair, retaining only the worst failing pair for diagnostics."""
    failures = []
    worst = None
    worst_score = -1
    compared = 0
    max_fraction = max_error = 0.0
    with av.open(str(reference)) as left, av.open(str(candidate)) as right:
        for index, (a, b) in enumerate(zip_longest(left.decode(video=0), right.decode(video=0))):
            if a is None or b is None:
                failures.append({"frame": index, "reason": "missing reference or candidate frame"})
                # Retain the available frame even for an end-of-video mismatch.
                if worst is None:
                    available = (a if a is not None else b).to_ndarray(format="rgb24")
                    worst = (index, available if a is not None else None,
                             available if b is not None else None)
                continue
            ref = a.to_ndarray(format="rgb24")
            new = b.to_ndarray(format="rgb24")
            compared += 1
            if ref.shape != new.shape:
                failures.append({"frame": index, "reason": "dimensions differ"})
                if worst_score < float("inf"):
                    worst_score, worst = float("inf"), (index, ref, new)
                continue
            _, fraction, error, failed = frame_metrics(ref, new, tolerances)
            max_fraction, max_error = max(max_fraction, fraction), max(max_error, error)
            if failed:
                failures.append({"frame": index, "changed_fraction": fraction, "mean_error": error})
                score = max(fraction / max(tolerances["max_changed_fraction"], 1e-12),
                            error / max(tolerances["max_mean_error"], 1e-12))
                if score > worst_score:
                    worst_score, worst = score, (index, ref.copy(), new.copy())
    if worst is not None:
        save_diff(destination, *worst)
    return {"compared_frames": compared, "failed_frames": failures,
            "max_changed_fraction": max_fraction, "max_mean_error": max_error}


def save_diff(destination, index, reference, candidate):
    destination.mkdir(parents=True, exist_ok=True)
    for label, pixels in (("reference", reference), ("candidate", candidate)):
        if pixels is not None:
            Image.fromarray(pixels).save(destination / f"frame-{index:06d}-{label}.png")
    if reference is not None and candidate is not None:
        # Pad dimension mismatches for a meaningful visual diff without resizing.
        height = max(reference.shape[0], candidate.shape[0])
        width = max(reference.shape[1], candidate.shape[1])
        a = np.zeros((height, width, 3), dtype=np.int16)
        b = a.copy()
        a[:reference.shape[0], :reference.shape[1]] = reference
        b[:candidate.shape[0], :candidate.shape[1]] = candidate
        diff = np.clip(np.abs(a - b) * 4, 0, 255).astype(np.uint8)
        Image.fromarray(diff).save(destination / f"frame-{index:06d}-diff-4x.png")


def validate_suite(report, output, tolerances, reference=None):
    """Called after ALL timed renders, so comparison cannot warm subsequent scenes."""
    reference_runs = {}
    if reference:
        root, baseline = reference
        reference_runs = {r["name"]: r for r in baseline["runs"] if r["phase"] == "first"}
    results = []
    for run in report["runs"]:
        result = {"name": run["name"], "phase": run["phase"], "passed": False, "errors": []}
        diagnostic = output / "visual-diffs" / run["name"] / run["phase"]
        try:
            if report.get("timing_protocol") == "default-export-separate-lossless-v1":
                if not run.get("export_validation", {}).get("passed"):
                    raise ValueError("Timed export checks failed: " + "; ".join(run.get("export_validation", {}).get("errors", [])))
                if run.get("validation_render", {}).get("status") != "ok":
                    raise ValueError("Lossless validation render failed or is missing")
            if run["status"] != "ok" or not run.get("video"):
                raise ValueError("Render did not complete; no valid video available")
            movie = video_path(output, run)
            result.update(inspect_video(movie, run, report, tolerances["duration_tolerance"]))
            if reference:
                old = reference_runs[run["name"]]
                metadata = old["visual"]
                scene_tolerances = metadata["tolerances"]
                result["tolerances"] = scene_tolerances
                if result["frames"] != metadata["frames"]:
                    result["errors"].append("Frame count differs from baseline")
                duration = result["duration_seconds"]
                if duration is None or abs(duration - metadata["duration_seconds"]) > tolerances["duration_tolerance"]:
                    result["errors"].append("Duration differs from baseline")
                result.update(compare_video(video_path(root, old), movie, diagnostic, scene_tolerances))
                if result["failed_frames"]:
                    result["errors"].append("Decoded frames differ beyond tolerances")
                # Timing-only failures still get a representative visual pair.
                if result["errors"] and not diagnostic.exists():
                    with av.open(str(video_path(root, old))) as a, av.open(str(movie)) as b:
                        first_a = next(a.decode(video=0), None)
                        first_b = next(b.decode(video=0), None)
                        save_diff(diagnostic, 0,
                                  first_a.to_ndarray(format="rgb24") if first_a is not None else None,
                                  first_b.to_ndarray(format="rgb24") if first_b is not None else None)
            result["passed"] = not result["errors"]
        except (av.error.FFmpegError, OSError, ValueError, KeyError, IndexError, StopIteration) as error:
            result["errors"].append(str(error))
        if not result["passed"]:
            diagnostic.mkdir(parents=True, exist_ok=True)
            (diagnostic / "failure.json").write_text(json.dumps(result, indent=2))
        result.pop("failed_frames", None)
        result.pop("name", None)
        result.pop("phase", None)
        run["visual"] = result
        results.append(result)
    if not reference:
        # Measure repeatability within the approved baseline, never from a candidate.
        # A baseline with substantial phase differences is rejected rather than
        # learning permissive thresholds that could hide future regressions.
        ceiling = {**tolerances, "max_changed_fraction": 0.005, "max_mean_error": 1.5}
        for scene in report["scenes"]:
            pair = [r for r in report["runs"] if r["name"] == scene["name"]]
            if len(pair) != 2 or not all(r["visual"]["passed"] for r in pair):
                continue
            diagnostic = output / "visual-diffs" / scene["name"] / "baseline-repeatability"
            try:
                metrics = compare_video(video_path(output, pair[0]), video_path(output, pair[1]),
                                        diagnostic, ceiling)
                stable = not metrics["failed_frames"]
                if abs(pair[0]["visual"]["duration_seconds"] - pair[1]["visual"]["duration_seconds"]) > tolerances["duration_tolerance"]:
                    stable = False
                calibrated = {
                    **tolerances,
                    "max_changed_fraction": min(ceiling["max_changed_fraction"],
                        max(tolerances["max_changed_fraction"], metrics["max_changed_fraction"] * 1.5)),
                    "max_mean_error": min(ceiling["max_mean_error"],
                        max(tolerances["max_mean_error"], metrics["max_mean_error"] * 1.5)),
                }
                for run in pair:
                    run["visual"]["tolerances"] = calibrated
                    if not stable:
                        run["visual"]["passed"] = False
                        run["visual"]["errors"].append("Baseline first/cached outputs are not sufficiently repeatable")
                if not stable:
                    diagnostic.mkdir(parents=True, exist_ok=True)
                    (diagnostic / "failure.json").write_text(json.dumps(metrics, indent=2))
            except (av.error.FFmpegError, OSError, ValueError, KeyError, IndexError) as error:
                for run in pair:
                    run["visual"]["passed"] = False
                    run["visual"]["errors"].append(f"Repeatability check failed: {error}")
    complete = len(results) == len(report["scenes"]) * 2 and not report.get("interrupted")
    validation = {"passed": complete and all(r["passed"] for r in results),
                  "mode": "comparison" if reference else "reference",
                  "tolerances": tolerances}
    if reference:
        validation["baseline"] = str(root.resolve())
    report["visual_validation" if reference else "visual_reference"] = validation
    return validation["passed"]
