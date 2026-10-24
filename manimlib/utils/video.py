"""Choose an encoder by testing the installed FFmpeg and driver together."""
from functools import lru_cache
import subprocess


@lru_cache(maxsize=16)
def nvenc_available(ffmpeg_bin: str, width: int, height: int, fps: float) -> bool:
    # An encoder listing alone does not establish that the GPU and driver can use it.
    # Use the same input format and output dimensions as the actual movie.
    command = [
        ffmpeg_bin, "-nostdin", "-loglevel", "error",
        "-f", "rawvideo", "-s", f"{width}x{height}", "-pix_fmt", "rgba",
        "-r", str(fps), "-i", "pipe:0", "-an", "-frames:v", "1",
        "-vcodec", "h264_nvenc", "-pix_fmt", "yuv420p", "-f", "null", "-",
    ]
    try:
        result = subprocess.run(
            command, input=bytes(width * height * 4),
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def select_video_codec(
    codec: str, ffmpeg_bin: str, width: int, height: int,
    fps: float, pixel_format: str, crf: int | None,
) -> str:
    if codec != "auto":
        return codec
    # CRF is an x264 setting. Preserve its meaning, and leave specialized pixel
    # formats to the existing software path instead of silently changing them.
    if crf is None and pixel_format == "yuv420p" and nvenc_available(ffmpeg_bin, width, height, fps):
        return "h264_nvenc"
    return "libx264"
