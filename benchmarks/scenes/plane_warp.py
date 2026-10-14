from manimlib import *


class PlaneWarp(Scene):
    """Dense subdivided grid under nonlinear point transformations."""

    def construct(self):
        plane = NumberPlane((-7, 7, 0.5), (-4, 4, 0.5))
        plane.prepare_for_nonlinear_transform(num_inserted_curves=30)
        self.add(plane)
        self.play(plane.animate.apply_function(lambda p: np.array([
            p[0] + 0.4 * np.sin(p[1]), p[1] + 0.3 * np.sin(p[0]), p[2]
        ])), run_time=2)
        self.play(plane.animate.apply_complex_function(lambda z: z + 0.15 * np.sin(z)), run_time=2)
