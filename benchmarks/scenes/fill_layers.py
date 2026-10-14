from manimlib import *


class FillLayers(Scene):
    """Overlapping transparent fills, gradients and holes; fixed camera."""

    def construct(self):
        layers = VGroup(*[
            Annulus(inner_radius=0.3, outer_radius=1.4)
            .set_fill([BLUE, RED], 0.25, gradient_direction=RIGHT)
            .set_stroke(width=0).shift(0.08 * i * RIGHT)
            for i in range(40)
        ]).center()
        self.play(FadeIn(layers), run_time=1)
        self.play(Rotate(layers, angle=PI), run_time=2)
        self.play(layers.animate.scale(1.4).set_opacity(0.5), run_time=1)
