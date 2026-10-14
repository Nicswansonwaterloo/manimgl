from manimlib import *
from benchmarks.support.assets import checker_video


class VideoTiles(Scene):
    """Shared decoded video frames uploaded as animated textures."""

    def construct(self):
        tiles = Group(*[VideoMobject(checker_video(), height=0.8) for _ in range(48)])
        tiles.arrange_in_grid(6, 8, buff=0.15)
        for tile in tiles:
            tile.play_from(0)
        self.add(tiles)
        self.play(tiles.animate.scale(1.1), run_time=3, rate_func=there_and_back)
        self.play(FadeOut(tiles), run_time=1)
