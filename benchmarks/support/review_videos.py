"""Player-compatible copies, kept separate from lossless validation references."""
import subprocess
from pathlib import Path


def prepare_review_videos(report, output, baseline=False):
    reviewed = set()
    for run in report["runs"]:
        if not run.get("video"):
            continue
        if not baseline and run.get("visual", {}).get("passed") is True:
            continue
        raw = output / run["video"]
        if not raw.exists():
            continue
        # Also migrates older references that put RGB H.264 files in videos/.
        reference_dir = output / "reference-videos"
        reference_dir.mkdir(exist_ok=True)
        if raw.parent != reference_dir:
            destination = reference_dir / raw.name
            if destination.exists():
                raise ValueError(f"Refusing to overwrite reference movie: {destination}")
            raw.rename(destination)
            raw = destination
            run["video"] = str(raw.relative_to(output))
        # One review copy per baseline scene; both phases remain lossless references.
        if baseline and run["name"] in reviewed and run.get("visual", {}).get("passed") is True:
            continue
        preview = output / "videos" / raw.name
        preview.parent.mkdir(exist_ok=True)
        if preview.exists() and run.get("preview") == str(preview.relative_to(output)):
            reviewed.add(run["name"])
            continue
        temporary = preview.with_name(preview.stem + "-preview-temp.mp4")
        try:
            subprocess.run([
                "ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(raw),
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                "-threads", "1", "-movflags", "+faststart", str(temporary),
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=60)
            temporary.replace(preview)
            run["preview"] = str(preview.relative_to(output))
            reviewed.add(run["name"])
        except (OSError, subprocess.SubprocessError) as error:
            run["preview_error"] = str(error)
        finally:
            temporary.unlink(missing_ok=True)
