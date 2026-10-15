from manimlib import *


class PendulumRig(Scene):
    """24 coupled-looking pendulums, endpoint-constrained rods and four live traces."""
    default_camera_config = dict(background_color="#221B18")

    def construct(self):
        rods, bobs = VGroup(), VGroup()
        palette = color_gradient([GOLD, RED, PINK, BLUE], 24)
        for i in range(24):
            pivot = np.array([(i - 11.5) * 0.45, 2.7, 0])
            length = 2.1 + 0.055 * i

            def endpoint(i=i, pivot=pivot, length=length):
                angle = 0.5 * np.cos((2.5 + i * 0.05) * self.time)
                return pivot + length * np.array([np.sin(angle), -np.cos(angle), 0])

            rod = Line(pivot, endpoint(), stroke_width=2, color=GREY_B)
            rod.add_updater(lambda m, dt, pivot=pivot, endpoint=endpoint: m.put_start_and_end_on(pivot, endpoint()))
            bob = Dot(radius=0.08, fill_color=palette[i])
            bob.add_updater(lambda m, dt, endpoint=endpoint: m.move_to(endpoint()))
            rods.add(rod)
            bobs.add(bob)
        traces = VGroup(*[TracedPath(bob.get_center, time_traced=1.5, stroke_color=bob.get_color(),
                                   stroke_width=2) for bob in bobs[::6]])
        support = Line(5.7 * LEFT + 2.7 * UP, 5.7 * RIGHT + 2.7 * UP, stroke_width=5)
        self.add(support, rods, bobs, traces)
        self.wait(4)
