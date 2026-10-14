from manimlib import *


class SurfaceMorph(ThreeDScene):
    """Dense surface vertex interpolation and a separate wire mesh."""

    def construct(self):
        surface = ParametricSurface(
            lambda u, v: [u, v, 0.5 * np.sin(2 * u) * np.cos(2 * v)],
            u_range=(-3, 3), v_range=(-3, 3), resolution=(101, 101), color=BLUE,
        )
        target = ParametricSurface(
            lambda u, v: [u, v, 0.2 * (u * u - v * v)],
            u_range=(-3, 3), v_range=(-3, 3), resolution=(101, 101), color=TEAL,
        )
        mesh = SurfaceMesh(surface, resolution=(21, 21), stroke_width=1)
        self.add(surface, mesh)
        self.play(Transform(surface, target), Transform(mesh, SurfaceMesh(target, resolution=(21, 21))),
                  run_time=2)
        self.play(self.frame.animate.reorient(45, 70), run_time=2)
