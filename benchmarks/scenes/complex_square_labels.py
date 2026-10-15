from manimlib import *


class ComplexSquareRedraw(Scene):
    """4s: paired complex planes, native numeric/dot labels and matching algebra transforms."""

    def construct(self):
        planes = [ComplexPlane((-2, 2), (-2, 2), width=5, height=5).shift(3.3*side + 0.5*UP)
                  for side in (LEFT, RIGHT)]
        for plane in planes:
            plane.add_coordinate_labels(font_size=16)
        theta = ValueTracker(0)
        z = lambda: 1.15*np.exp(1j*theta.get_value())

        def marker(plane, value, color):
            real = DecimalNumber(num_decimal_places=1, font_size=24)
            imag = DecimalNumber(num_decimal_places=1, include_sign=True, font_size=24)
            label = VGroup(real, imag, Text("i", font_size=24, font="serif", slant=ITALIC))
            dot = Dot(radius=0.06, fill_color=color)
            def update_marker(group):
                w = value()
                real.set_value(w.real)
                imag.set_value(w.imag)
                dot.move_to(plane.n2p(w))
                label.arrange(RIGHT, buff=0.02, aligned_edge=DOWN).next_to(dot.get_center(), UR, buff=0.12)
            return VGroup(dot, label).add_updater(update_marker)

        first = marker(planes[0], z, YELLOW)
        second = marker(planes[1], lambda: z()**2, PINK)
        equations = [Tex(s, font_size=34).to_edge(DOWN) for s in (
            r"z^2=(a+bi)^2", r"z^2=a^2+2abi+b^2i^2", r"z^2=(a^2-b^2)+(2ab)i")]
        self.add(*planes, first, second, equations[0])
        self.play(theta.animate.set_value(TAU/3), run_time=4/3, rate_func=linear)
        self.play(theta.animate.set_value(2*TAU/3), TransformMatchingTex(equations[0], equations[1]),
                  run_time=4/3, rate_func=linear)
        self.play(theta.animate.set_value(TAU), TransformMatchingTex(equations[1], equations[2]),
                  run_time=4/3, rate_func=linear)
