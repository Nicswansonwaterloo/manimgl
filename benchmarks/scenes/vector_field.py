from manimlib import *


class VectorFieldFlow(Scene):
    """Vectorized arrow field recomputation and particle advection."""

    def construct(self):
        plane = NumberPlane((-6, 6), (-3, 3))
        phase = ValueTracker(0)

        def flow(coords):
            x, y = coords[:, 0], coords[:, 1]
            return np.column_stack((-y + np.sin(phase.get_value()), x)) * 0.4

        field = VectorField(flow, plane, density=2, stroke_width=2)
        field.add_updater(lambda m: m.update_vectors())
        particles = VGroup(*[Dot(plane.c2p(x, y), radius=0.04, color=YELLOW)
                             for x in np.linspace(-4, 4, 16) for y in [-1, 0, 1]])
        for dot in particles:
            dot.add_updater(lambda m, dt: m.shift(
                dt * 0.4 * np.array([-m.get_y(), m.get_x(), 0])))
        self.add(plane, field, particles)
        self.play(phase.animate.set_value(TAU), run_time=4, rate_func=linear)
