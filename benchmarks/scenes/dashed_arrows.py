from manimlib import *


class DashedArrows(Scene):
    """Dashes, arrow tips, arcs and changing stroke widths."""

    def construct(self):
        paths = VGroup(*[
            VGroup(
                DashedLine(2 * LEFT, 2 * RIGHT, dash_length=0.08),
                Arrow(2 * LEFT, 2 * RIGHT, buff=0),
                Arc(radius=0.6, angle=PI),
            ).arrange(RIGHT, buff=0.4)
            for _ in range(8)
        ]).arrange(DOWN, buff=0.2).set_height(6)
        self.play(ShowCreation(paths), run_time=2)
        self.play(paths.animate.set_stroke(YELLOW, 7).rotate(0.15), run_time=2)
