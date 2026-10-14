from manimlib import *


class HomotopyRibbons(Scene):
    """24 subdivided ribbons under a time-dependent nonlinear homotopy and restoration."""
    def construct(self):
        ribbons = VGroup()
        colors = color_gradient([BLUE, TEAL, GOLD, RED], 24)
        for i, color in enumerate(colors):
            points = np.column_stack([np.linspace(-5, 5, 80), np.full(80, (i - 11.5) * 0.2), np.zeros(80)])
            ribbons.add(VMobject(stroke_color=color, stroke_width=2).set_points_as_corners(points))
        self.add(ribbons)

        def warp(x, y, z, t):
            envelope = np.sin(PI * t)
            return [x + 0.35 * envelope * np.sin(2 * y + 4 * t),
                    y + 0.55 * envelope * np.sin(1.5 * x - 5 * t), z]

        self.play(Homotopy(warp, ribbons), run_time=4, rate_func=linear)
