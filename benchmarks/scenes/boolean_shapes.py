from manimlib import *


class BooleanShapes(Scene):
    """CPU path clipping rebuilt every frame, then rendered as filled paths."""

    def construct(self):
        offset = ValueTracker(-0.8)
        operations = [Union, Intersection, Difference, Exclusion]
        panels = VGroup(*[
            always_redraw(lambda op=op, i=i: op(
                Circle(radius=1), Circle(radius=1).shift(offset.get_value() * RIGHT)
            ).set_fill([BLUE, TEAL, YELLOW, RED][i], 0.8)
              .set_stroke(WHITE, 1).shift((i - 1.5) * 3 * RIGHT))
            for i, op in enumerate(operations)
        ])
        self.add(panels)
        self.play(offset.animate.set_value(0.8), run_time=4, rate_func=there_and_back)
