from manimlib import *
from benchmarks.support.assets import texture_image


class DistinctTextureGallery(Scene):
    """36 distinct RGBA textures, overlapping moving quads and per-image opacity."""
    def construct(self):
        tiles = Group(*[ImageMobject(texture_image(i), height=0.9) for i in range(36)])
        tiles.arrange_in_grid(4, 9, buff=0.18)
        homes = [tile.get_center().copy() for tile in tiles]
        for i, (tile, home) in enumerate(zip(tiles, homes)):
            tile.add_updater(lambda m, dt, i=i, home=home: m.move_to(
                home + 0.3 * np.array([np.sin(2 * self.time + i), np.cos(self.time + i), 0]))
                .set_opacity(0.6 + 0.4 * np.cos(self.time + i)**2))
        self.add(tiles)
        self.wait(4)
