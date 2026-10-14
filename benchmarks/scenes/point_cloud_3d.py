from manimlib import *


class PointCloud3D(ThreeDScene):
    """20,000 GPU dots, position buffer updates, glow and camera motion."""

    def construct(self):
        rng = np.random.default_rng(2026)
        points = rng.normal(size=(20_000, 3))
        points *= 2 / np.maximum(np.linalg.norm(points, axis=1, keepdims=True), 0.1)
        cloud = DotCloud(points, radius=0.025, color=BLUE, glow_factor=0.3)
        axes = ThreeDAxes((-3, 3), (-3, 3), (-3, 3))
        self.add(axes, cloud)
        self.play(Rotate(cloud, angle=PI, axis=UP), run_time=2)
        self.play(cloud.animate.apply_function(lambda p: p * [1.5, 0.7, 1]),
                  self.frame.animate.reorient(45, 75), run_time=2)
