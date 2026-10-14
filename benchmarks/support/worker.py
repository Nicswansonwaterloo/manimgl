"""Run the normal CLI with lightweight measurement hooks in this process only."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time


def main():
    destination = Path(os.environ["MANIM_BENCHMARK_METRICS"])
    # manimlib parses argv at import time, so leave the CLI arguments intact.
    started = time.perf_counter()
    import manimlib
    from manimlib.__main__ import main as render
    from manimlib.scene.scene import Scene
    from manimlib.scene.scene_file_writer import SceneFileWriter
    from benchmarks.support.gpu import install

    install(timing_requested=os.environ.get("MANIM_BENCHMARK_GPU_TIMING") == "1")

    metrics = {"import_seconds": time.perf_counter() - started, "frames_written": 0}
    original_init = Scene.__init__
    original_run = Scene.run
    original_write = SceneFileWriter.write_frame

    def measured_init(self, *args, **kwargs):
        start = time.perf_counter()
        original_init(self, *args, **kwargs)
        metrics["scene_init_seconds"] = time.perf_counter() - start
        metrics["scene"] = type(self).__name__
        metrics["adapter"] = dict(self.camera.gpu.adapter.info)
        metrics["resolution"] = list(self.camera.get_pixel_shape())
        metrics["fps"] = self.camera.fps
        metrics["msaa_samples"] = self.samples

    def measured_run(self):
        start = time.perf_counter()
        original_run(self)
        metrics["scene_run_seconds"] = time.perf_counter() - start
        metrics["animation_seconds"] = self.time
        metrics["interrupted"] = self.file_writer.ended_with_interrupt
        encoder = getattr(self.file_writer, "writing_process", None)
        metrics["encoder_returncode"] = encoder.returncode if encoder else None
        metrics["gpu_rendering"] = self.camera.gpu.benchmark_measurement.finish()

    def measured_write(self):
        original_write(self)
        if self.write_to_movie:
            metrics["frames_written"] += 1

    Scene.__init__ = measured_init
    Scene.run = measured_run
    SceneFileWriter.write_frame = measured_write
    metrics["manimgl_version"] = manimlib.__version__
    metrics["completed"] = False
    try:
        render()
        metrics["completed"] = True
    finally:
        # getrusage retains CPU time for exited/waited-for children (the encoder).
        # This is more accurate than sampling CPU time of short-lived subprocesses.
        try:
            import resource

            own = resource.getrusage(resource.RUSAGE_SELF)
            children = resource.getrusage(resource.RUSAGE_CHILDREN)
            metrics["cpu_seconds"] = own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime
            metrics["worker_peak_rss_bytes"] = own.ru_maxrss * (1 if sys.platform == "darwin" else 1024)
        except ImportError:
            metrics["cpu_seconds"] = None
            metrics["worker_peak_rss_bytes"] = None
        destination.write_text(json.dumps(metrics, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
