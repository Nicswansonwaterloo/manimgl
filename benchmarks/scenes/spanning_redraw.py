from manimlib import *


class SpanningVectorRedraw(Scene):
    """8s: always-redrawn vector sums, per-frame TeX matrices and accumulated ghost arrows."""

    def construct(self):
        plane = NumberPlane((-7,7), (-5,5), width=12, height=6)
        plane.set_stroke(opacity=0.35)
        clock = ValueTracker(0)
        coefficients = lambda: (1.3*np.cos(clock.get_value()), 0.9*np.sin(1.3*clock.get_value()))
        def endpoints():
            a, b = coefficients()
            return plane.c2p(2*a, a), plane.c2p(2*a-b, a+3*b)
        origin = plane.c2p(0,0)
        arrows = always_redraw(lambda: VGroup(
            Arrow(origin, endpoints()[0], buff=0, fill_color=RED),
            Arrow(endpoints()[0], endpoints()[1], buff=0, fill_color=BLUE),
            Arrow(origin, endpoints()[1], buff=0, fill_color=YELLOW)))
        def equation():
            a, b = coefficients()
            return Tex(rf"{a:.1f}\begin{{bmatrix}}2\\1\end{{bmatrix}}"
                       rf"+({b:.1f})\begin{{bmatrix}}-1\\3\end{{bmatrix}}",
                       font_size=30).to_edge(DOWN).add_background_rectangle(opacity=0.9, buff=0.15)
        readout = always_redraw(equation)
        self.add(plane, arrows, readout)
        for k in range(8):
            self.play(clock.animate.set_value((k+1)*TAU/8), run_time=1, rate_func=linear)
            ghost = arrows.copy().clear_updaters().set_opacity(0.2)
            self.add(ghost)
