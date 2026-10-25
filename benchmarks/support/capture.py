"""Capture the exact encoder input with bounded memory; compress after timing."""
import time
from fractions import Fraction


class CaptureSink:
    def __init__(self, encoder, path, append=False):
        self.encoder = encoder
        # Unbuffered writes consume mapped GPU memory before it is unmapped.
        self.file = path.open("ab" if append else "wb", buffering=0)
        self.frames = 0
        self.write_seconds = 0.0

    def write(self, frame):
        written = self.encoder.write(frame)
        if written != len(frame):
            raise OSError("Incomplete encoder frame write")
        started = time.perf_counter()
        remaining = memoryview(frame)
        while remaining:
            count = self.file.write(remaining)
            if not count:
                raise OSError("Incomplete capture write")
            remaining = remaining[count:]
        self.write_seconds += time.perf_counter() - started
        self.frames += 1
        return written

    def close(self):
        self.file.close()


def encode_capture(source, destination, resolution, fps, frames):
    """Read one raw frame at a time; reject truncated or extra capture data."""
    import av
    import numpy as np

    width, height = map(int, resolution.split("x"))
    size = width * height * 4
    if frames <= 0 or source.stat().st_size != size * frames:
        raise ValueError("Raw capture size differs from timed frame count and dimensions")
    with source.open("rb") as raw, av.open(str(destination), "w") as container:
        stream = container.add_stream("libx264rgb", rate=fps)
        stream.width, stream.height = width, height
        stream.pix_fmt = "rgb24"
        stream.options = {"crf": "0", "preset": "ultrafast"}
        for index in range(frames):
            data = raw.read(size)
            if len(data) != size:
                raise ValueError("Truncated raw capture")
            pixels = np.frombuffer(data, np.uint8).reshape(height, width, 4)
            frame = av.VideoFrame.from_ndarray(pixels, format="rgba")
            frame.pts, frame.time_base = index, Fraction(1, fps)
            for packet in stream.encode(frame):
                container.mux(packet)
        if raw.read(1):
            raise ValueError("Extra raw capture data")
        for packet in stream.encode():
            container.mux(packet)
