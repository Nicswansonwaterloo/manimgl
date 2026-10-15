from manimlib import *


class ComplexSquareRedraw(Scene):
    """4s: paired complex planes, rebuilt TeX/dot labels and matching algebra transforms."""

    def construct(self):
        planes = [ComplexPlane((-2, 2), (-2, 2), width=5, height=5).shift(3.3*side + 0.5*UP)
                  for side in (LEFT, RIGHT)]
        for plane in planes:
            plane.add_coordinate_labels(font_size=16)
        theta = ValueTracker(0)
        z = lambda: 1.15*np.exp(1j*theta.get_value())

        def marker(plane, value, color):
            w = value()
            label = Tex(rf"{w.real:.1f}{w.imag:+.1f}i", font_size=24)
            point = plane.n2p(w)
            label.next_to(point, UR, buff=0.12)
            return VGroup(Dot(point, radius=0.06, fill_color=color), label)

        first = always_redraw(lambda: marker(planes[0], z, YELLOW))
        second = always_redraw(lambda: marker(planes[1], lambda: z()**2, PINK))
        equations = [Tex(s, font_size=34).to_edge(DOWN) for s in (
            r"z^2=(a+bi)^2", r"z^2=a^2+2abi+b^2i^2", r"z^2=(a^2-b^2)+(2ab)i")]
        self.add(*planes, first, second, equations[0])
        self.play(theta.animate.set_value(TAU/3), run_time=4/3, rate_func=linear)
        self.play(theta.animate.set_value(2*TAU/3), TransformMatchingTex(equations[0], equations[1]),
                  run_time=4/3, rate_func=linear)
        self.play(theta.animate.set_value(TAU), TransformMatchingTex(equations[1], equations[2]),
                  run_time=4/3, rate_func=linear)
