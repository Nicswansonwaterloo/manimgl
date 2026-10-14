from manimlib import *
from benchmarks.support.hilbert_visuals import rainbow_hilbert


class HilbertRefinement2D(Scene):
    """4s: rainbow square-filling curve, five orders of curved refinement transforms."""
    def construct(self):
        current, _ = rainbow_hilbert(1, 2)
        self.play(ShowCreation(current, lag_ratio=1), run_time=0.6)
        for order in (2, 3, 4, 5):
            target, points = rainbow_hilbert(order, 2)
            self.play(ReplacementTransform(current, target, path_arc=PI / 4), run_time=0.65)
            current = target
        cursor = ValueTracker(0)
        dot = GlowDot(points[0], color=WHITE, radius=0.1)
        dot.add_updater(lambda m: m.move_to(points[min(int(cursor.get_value()), len(points) - 1)]))
        self.add(dot)
        self.play(cursor.animate.set_value(len(points) - 1), run_time=0.8, rate_func=linear)
