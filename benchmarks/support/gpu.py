"""GPU evidence and optional pass timestamps, installed only in benchmark workers."""
from contextlib import contextmanager
import math
import statistics
import struct
from unittest.mock import patch


class GpuMeasurement:
    BATCH_SIZE = 128  # Two queries per pass, below WebGPU's query-set limit.

    def __init__(self, gpu, timing_requested):
        import wgpu

        self.gpu = gpu
        self.passes = self.draw_calls = self.vertices = self.bundle_replays = 0
        self.bundles = {}
        self.pending = 0
        self.durations_ms = []
        self.timing_status = "disabled"
        self.query_set = None
        if not timing_requested:
            return
        if "timestamp-query" not in gpu.device.features:
            self.timing_status = "unsupported: adapter lacks timestamp-query"
            return
        # wgpu-py exposes pass queries but not the native queue's timestamp period.
        # Query it explicitly; never assume ticks are nanoseconds on every backend.
        try:
            from wgpu.backends.wgpu_native._ffi import lib

            self.period_ns = lib.wgpuQueueGetTimestampPeriod(gpu.queue._internal)
            if not math.isfinite(self.period_ns) or self.period_ns <= 0:
                raise ValueError("invalid timestamp period")
            self.resolve_buffer = gpu.device.create_buffer(
                size=256 * self.BATCH_SIZE,
                usage=wgpu.BufferUsage.QUERY_RESOLVE | wgpu.BufferUsage.COPY_SRC,
            )
            self.query_set = gpu.device.create_query_set(type="timestamp", count=2 * self.BATCH_SIZE)
            self.timing_status = "enabled"
        except (ImportError, AttributeError, ValueError, RuntimeError) as error:
            self.timing_status = f"unavailable: {error}"

    def collect_timestamps(self):
        if not self.pending:
            return
        # One synchronous read per batch, not per frame. This still adds profiling
        # overhead; timed runs must be compared to other timed runs.
        data = self.gpu.queue.read_buffer(self.resolve_buffer, size=256 * self.pending)
        durations = []
        for index in range(self.pending):
            start, end = struct.unpack_from("=2Q", data, 256 * index)
            if end < start or start == 0:
                self.timing_status = f"unavailable: invalid driver timestamps ({start}, {end})"
                self.query_set = None
                self.durations_ms.clear()
                self.pending = 0
                return
            durations.append((end - start) * self.period_ns / 1e6)
        self.durations_ms.extend(durations)
        self.pending = 0

    def finish(self):
        self.collect_timestamps()
        completion_method = "queue callback"
        try:
            self.gpu.queue.on_submitted_work_done_sync()
        except TypeError:
            # Some wgpu/native combinations disagree on the completion callback
            # signature. A queued copy followed by synchronous map/read is also
            # a fence, using the same readback path that movie rendering uses.
            import wgpu

            fence = self.gpu.device.create_buffer(size=4, usage=wgpu.BufferUsage.COPY_SRC)
            try:
                self.gpu.queue.read_buffer(fence)
            finally:
                fence.destroy()
            completion_method = "buffer readback fence"
        adapter = dict(self.gpu.adapter.info)
        hardware = (adapter.get("adapter_type") in {"IntegratedGPU", "DiscreteGPU"}
                    and adapter.get("backend_type") in {"Metal", "Vulkan", "D3D12", "OpenGL"})
        values = sorted(self.durations_ms)
        return {
            "backend": adapter.get("backend_type"),
            "device": adapter.get("device"),
            "hardware_adapter": hardware,
            "render_passes_submitted": self.passes,
            "draw_calls_executed": self.draw_calls,
            "vertices_submitted": self.vertices,
            "bundle_replays": self.bundle_replays,
            "queue_completed": True,
            "completion_method": completion_method,
            "hardware_rendering_confirmed": hardware and self.passes > 0 and self.draw_calls > 0,
            "timing_status": self.timing_status,
            "timed_passes": len(values),
            "render_pass_total_seconds": sum(values) / 1000 if values else None,
            "render_pass_mean_ms": statistics.mean(values) if values else None,
            "render_pass_p95_ms": values[math.ceil(0.95 * len(values)) - 1] if values else None,
        }


def install(timing_requested=False):
    """Wrap the normal renderer without changing production rendering defaults."""
    import wgpu
    from manimlib.renderer.gpu import Gpu, RenderPass

    original_init = Gpu.__init__
    original_pass = Gpu.render_pass
    original_draw = RenderPass.draw
    original_replay = RenderPass.replay
    original_bundle = Gpu.bundle

    def measured_init(self):
        request_adapter = wgpu.gpu.request_adapter_sync

        def measured_adapter(*args, **kwargs):
            adapter = request_adapter(*args, **kwargs)
            if timing_requested and "timestamp-query" in adapter.features:
                request_device = adapter.request_device_sync

                def timed_device(*args, **kwargs):
                    kwargs["required_features"] = [*kwargs.get("required_features", ()), "timestamp-query"]
                    return request_device(*args, **kwargs)

                adapter.request_device_sync = timed_device
            return adapter

        with patch.object(wgpu.gpu, "request_adapter_sync", measured_adapter):
            original_init(self)
        self.benchmark_measurement = GpuMeasurement(self, timing_requested)

    def measured_draw(self, pipeline, vertices, indices=None):
        original_draw(self, pipeline, vertices, indices)
        self.benchmark_draws = getattr(self, "benchmark_draws", 0) + 1
        self.benchmark_vertices = getattr(self, "benchmark_vertices", 0) + vertices

    def measured_bundle(self, draw):
        counts = []

        def record(render_pass):
            draw(render_pass)
            counts.extend((getattr(render_pass, "benchmark_draws", 0),
                           getattr(render_pass, "benchmark_vertices", 0)))

        bundle = original_bundle(self, record)
        # Keep just the current bundle: Renderer owns only one live cached bundle.
        self.benchmark_measurement.bundles = {id(bundle): counts}
        return bundle

    def measured_replay(self, bundle):
        original_replay(self, bundle)
        self.benchmark_bundles = getattr(self, "benchmark_bundles", []) + [id(bundle)]

    @contextmanager
    def measured_pass(self, attachments):
        measurement = self.benchmark_measurement
        if measurement.query_set is None:
            with original_pass(self, attachments) as render_pass:
                yield render_pass
        else:
            # Same pass and submission as Gpu.render_pass, with pass-boundary
            # timestamps. Encoder-level timestamps are unsuitable on Apple GPUs.
            encoder = self.device.create_command_encoder()
            render_pass = RenderPass(encoder.begin_render_pass(
                **attachments, timestamp_writes={
                    "query_set": measurement.query_set,
                    "beginning_of_pass_write_index": 2 * measurement.pending,
                    "end_of_pass_write_index": 2 * measurement.pending + 1,
                },
            ), self.frame_bind_group)
            try:
                yield render_pass
            finally:
                render_pass.encoder.end()
                # Resolve in the same encoder that wrote these timestamps. In
                # wgpu-native, resolving later in a fresh encoder can yield zeros.
                encoder.resolve_query_set(measurement.query_set, 2 * measurement.pending, 2,
                                          measurement.resolve_buffer, 256 * measurement.pending)
                self.queue.submit([encoder.finish()])
            measurement.pending += 1
        measurement.passes += 1
        measurement.draw_calls += getattr(render_pass, "benchmark_draws", 0)
        measurement.vertices += getattr(render_pass, "benchmark_vertices", 0)
        for bundle in getattr(render_pass, "benchmark_bundles", []):
            calls, vertices = measurement.bundles[bundle]
            measurement.draw_calls += calls
            measurement.vertices += vertices
            measurement.bundle_replays += 1
        if measurement.pending == measurement.BATCH_SIZE:
            measurement.collect_timestamps()

    Gpu.__init__ = measured_init
    Gpu.render_pass = measured_pass
    Gpu.bundle = measured_bundle
    RenderPass.draw = measured_draw
    RenderPass.replay = measured_replay
