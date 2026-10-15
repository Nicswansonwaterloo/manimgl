from manimlib import *


class TracedPaths(Scene):
    """Parametric curves, path-following animations and growing trace buffers."""

    def construct(self):
        curves = [ParametricCurve(
            lambda t, k=k: np.array([4 * np.sin(k * t), 2.5 * np.sin((k + 1) * t), 0]),
            t_range=(0, TAU, 0.02), stroke_width=1, stroke_opacity=0.2,
        ) for k in range(1, 9)]
        dots = [Dot(radius=0.06, fill_color=YELLOW).move_to(curve.get_start()) for curve in curves]
        traces = [TracedPath(dot.get_center, stroke_color=BLUE, stroke_width=2) for dot in dots]
        self.add(*curves, *dots, *traces)
        self.play(*[MoveAlongPath(dot, curve) for dot, curve in zip(dots, curves)],
                  run_time=4, rate_func=linear)
