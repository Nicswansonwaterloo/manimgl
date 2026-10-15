from manimlib import *
from benchmarks.support.assets import texture_image


class TextureFilteringZoom(Scene):
    """Nearest/linear samplers, transparent image edges and large magnification changes."""
    def construct(self):
        nearest = ImageMobject(texture_image(0), height=3).set_texture_filter("nearest").shift(2 * LEFT)
        linear_image = ImageMobject(texture_image(0), height=3).set_texture_filter("linear").shift(2 * RIGHT)
        labels = VGroup(Text("NEAREST", font_size=24).move_to([-2, 2.2, 0]),
                        Text("LINEAR", font_size=24).move_to([2, 2.2, 0]))
        labels.fix_in_frame()
        labels.to_edge(UP)
        self.add(nearest, linear_image, labels)
        self.play(self.frame.animate.set_height(3.5), run_time=2)
        self.play(self.frame.animate.set_height(8), Rotate(nearest, PI / 4),
                  Rotate(linear_image, -PI / 4), run_time=2)
