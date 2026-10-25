"""Check that captured encoder input survives conversion without losing any frame."""
import io
from pathlib import Path
import tempfile
import unittest

import av
import numpy as np

from benchmarks.support.capture import CaptureSink, encode_capture
from benchmarks.support.visual import DEFAULT_TOLERANCES, compare_video


class CaptureTests(unittest.TestCase):
    def test_every_frame_including_last_survives_buffer_reuse_and_compression(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            encoder = io.BytesIO()
            sink = CaptureSink(encoder, root / "frames.rgba")
            rng = np.random.default_rng(123)
            expected = rng.integers(0, 256, (5, 32, 34, 4), dtype=np.uint8)
            buffer = bytearray(expected[0].nbytes)
            for pixels in expected:
                buffer[:] = pixels.tobytes()
                sink.write(memoryview(buffer))
                buffer[:] = bytes(len(buffer))
            sink.close()
            self.assertEqual(sink.frames, 5)
            self.assertEqual(encoder.getvalue(), expected.tobytes())
            self.assertEqual((root / "frames.rgba").read_bytes(), encoder.getvalue())
            encode_capture(root / "frames.rgba", root / "frames.mp4", "34x32", 15, 5)
            with av.open(str(root / "frames.mp4")) as video:
                decoded = list(video.decode(video=0))
                self.assertEqual(len(decoded), 5)
                for index, frame in enumerate(decoded):
                    np.testing.assert_array_equal(frame.to_ndarray(format="rgb24"), expected[index, :, :, :3])
            expected[2, :, :, :3] = 255
            (root / "changed.rgba").write_bytes(expected.tobytes())
            encode_capture(root / "changed.rgba", root / "changed.mp4", "34x32", 15, 5)
            result = compare_video(root / "frames.mp4", root / "changed.mp4", root / "diffs", DEFAULT_TOLERANCES)
            self.assertEqual(result["compared_frames"], 5)
            self.assertEqual([f["frame"] for f in result["failed_frames"]], [2])

    def test_missing_extra_and_partial_frames_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for size in (0, 32 * 32 * 4 - 1, 32 * 32 * 4 * 2):
                (root / "frames.rgba").write_bytes(bytes(size))
                with self.assertRaisesRegex(ValueError, "capture size"):
                    encode_capture(root / "frames.rgba", root / "frames.mp4", "32x32", 15, 1)

    def test_encoder_short_write_is_not_accepted(self):
        class ShortWriter:
            def write(self, frame):
                return len(frame) - 1

        with tempfile.TemporaryDirectory() as temporary:
            sink = CaptureSink(ShortWriter(), Path(temporary) / "frames.rgba")
            try:
                with self.assertRaises(OSError):
                    sink.write(b"rgba")
                self.assertEqual(sink.frames, 0)
            finally:
                sink.close()
