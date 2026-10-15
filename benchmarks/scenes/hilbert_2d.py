from manimlib import *
from benchmarks.support.hilbert_visuals import rainbow_hilbert, refinement_knots


class HilbertRefinement2D(Scene):
    """4s: rainbow square-filling curve, five orders of curved refinement transforms."""
    def construct(self):
        knots = refinement_knots(2, 5)
        current, _ = rainbow_hilbert(1, 2, knots)
        self.play(ShowCreation(current, lag_ratio=1), run_time=0.6)
        for order in (2, 3, 4, 5):
            target, points = rainbow_hilbert(order, 2, knots)
            self.play(ReplacementTransform(current, target, path_arc=PI / 4), run_time=0.65)
            current = target
        cursor = ValueTracker(0)
        dots = Group(*[GlowDot(path.get_start(), color=WHITE, radius=0.06) for path in current])
        for dot, path in zip(dots, current):
            dot.add_updater(lambda m, dt, path=path: m.move_to(
                path.quick_point_from_proportion(cursor.get_value())))
        self.add(dots)
        self.play(cursor.animate.set_value(1), run_time=0.8, rate_func=linear)
