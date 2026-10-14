"""Small reproducible local inputs, generated before timed runner invocations."""
import os
from pathlib import Path

import numpy as np
from PIL import Image


def asset_path(name, directory=None):
    # Runner invocations use a temporary directory. Direct scene previews can
    # still create reproducible inputs without configuring an environment.
    directory = Path(directory or os.environ.get(
        "MANIM_BENCHMARK_ASSETS", Path(__file__).resolve().parents[1] / "_generated"))
    directory.mkdir(parents=True, exist_ok=True)
    return directory / name


def checker_image(directory=None):
    path = asset_path("checker.png", directory)
    if not path.exists():
        y, x = np.indices((256, 256))
        check = ((x // 32 + y // 32) % 2).astype(np.uint8)
        Image.fromarray(np.stack([255 * check, x.astype(np.uint8), y.astype(np.uint8)], axis=-1)).save(path)
    return str(path)


def vector_image(directory=None):
    path = asset_path("curves.svg", directory)
    if not path.exists():
        path.write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
<path d="M 10 100 C 10 10 190 10 190 100 C 190 190 10 190 10 100 Z" fill="#58c4dd"/>
<path d="M 40 100 Q 100 10 160 100 Q 100 190 40 100 Z" fill="#fc6255"/>
<circle cx="100" cy="100" r="22" fill="#ffff00"/>
</svg>''', encoding="utf-8")
    return str(path)


def checker_video(directory=None):
    import av

    path = asset_path("checker.mov", directory)
    if not path.exists():
        y, x = np.indices((128, 128))
        with av.open(str(path), mode="w") as container:
            stream = container.add_stream("qtrle", rate=30)
            stream.width = stream.height = 128
            stream.pix_fmt = "argb"
            for index in range(90):
                pixels = np.empty((128, 128, 4), dtype=np.uint8)
                pixels[..., 0] = ((x + 3 * index) % 256).astype(np.uint8)
                pixels[..., 1] = (2 * y).astype(np.uint8)
                pixels[..., 2] = 255 * ((x // 16 + y // 16 + index // 5) % 2)
                pixels[..., 3] = 255
                frame = av.VideoFrame.from_ndarray(pixels, format="rgba")
                container.mux(stream.encode(frame))
            container.mux(stream.encode())
    return str(path)


def prepare_assets(directory):
    checker_image(directory)
    vector_image(directory)
    checker_video(directory)
