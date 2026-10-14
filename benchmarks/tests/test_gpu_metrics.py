"""Validate timing units and hardware evidence without a graphics adapter."""
import struct
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from benchmarks.support.gpu import GpuMeasurement


class GpuMetricTests(unittest.TestCase):
    def gpu(self, adapter_type="IntegratedGPU"):
        return SimpleNamespace(
            device=SimpleNamespace(features=set(), create_buffer=Mock(return_value=Mock())),
            queue=SimpleNamespace(on_submitted_work_done_sync=Mock(), read_buffer=Mock()),
            adapter=SimpleNamespace(info={"backend_type": "Metal", "device": "test",
                                          "adapter_type": adapter_type}),
        )

    def test_hardware_requires_draws_and_completed_queue(self):
        gpu = self.gpu()
        measurement = GpuMeasurement(gpu, False)
        measurement.passes = 1
        self.assertFalse(measurement.finish()["hardware_rendering_confirmed"])
        measurement.draw_calls = 2
        self.assertTrue(measurement.finish()["hardware_rendering_confirmed"])
        gpu.queue.on_submitted_work_done_sync.assert_called()
        gpu.queue.on_submitted_work_done_sync.side_effect = RuntimeError("device lost")
        with self.assertRaisesRegex(RuntimeError, "device lost"):
            measurement.finish()

    def test_cpu_adapter_and_unsupported_timing(self):
        measurement = GpuMeasurement(self.gpu("CPU"), True)
        measurement.passes = measurement.draw_calls = 1
        result = measurement.finish()
        self.assertFalse(result["hardware_rendering_confirmed"])
        self.assertTrue(result["timing_status"].startswith("unsupported"))
        self.assertIsNone(result["render_pass_mean_ms"])

    def test_incompatible_completion_callback_uses_readback_fence(self):
        gpu = self.gpu()
        fence = Mock()
        gpu.device.create_buffer = Mock(return_value=fence)
        gpu.queue.on_submitted_work_done_sync.side_effect = TypeError("incompatible callback signature")
        measurement = GpuMeasurement(gpu, False)
        measurement.passes = measurement.draw_calls = 1
        result = measurement.finish()
        self.assertTrue(result["hardware_rendering_confirmed"])
        self.assertEqual(result["completion_method"], "buffer readback fence")
        gpu.queue.read_buffer.assert_called_once_with(fence)
        fence.destroy.assert_called_once()

    def test_timestamp_stride_period_and_percentile(self):
        gpu = self.gpu()
        measurement = GpuMeasurement(gpu, False)
        measurement.query_set = object()
        measurement.resolve_buffer = object()
        measurement.period_ns = 2.0
        measurement.pending = 2
        data = bytearray(512)
        struct.pack_into("=2Q", data, 0, 100, 500100)
        struct.pack_into("=2Q", data, 256, 900000, 1900000)
        gpu.queue.read_buffer.return_value = data
        measurement.collect_timestamps()
        result = measurement.finish()
        self.assertEqual(result["timed_passes"], 2)
        self.assertEqual(result["render_pass_mean_ms"], 1.5)
        self.assertEqual(result["render_pass_p95_ms"], 2.0)
        self.assertEqual(result["render_pass_total_seconds"], 0.003)
        self.assertEqual(measurement.pending, 0)

    def test_invalid_timestamp_disables_timing_without_aborting_render(self):
        gpu = self.gpu()
        measurement = GpuMeasurement(gpu, False)
        measurement.query_set = object()
        measurement.resolve_buffer = object()
        measurement.period_ns = 1.0
        measurement.pending = 1
        measurement.durations_ms = [1.0]
        data = bytearray(256)
        struct.pack_into("=2Q", data, 0, 100, 0)
        gpu.queue.read_buffer.return_value = data
        measurement.collect_timestamps()
        measurement.passes = measurement.draw_calls = 1
        result = measurement.finish()
        self.assertTrue(result["hardware_rendering_confirmed"])
        self.assertTrue(result["timing_status"].startswith("unavailable: invalid driver"))
        self.assertIsNone(result["render_pass_mean_ms"])
        self.assertIsNone(measurement.query_set)


if __name__ == "__main__":
    unittest.main()
