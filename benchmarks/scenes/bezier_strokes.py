from manimlib import *


class BezierStrokeStress(Scene):
    """64 long smooth paths with 200 anchors each, tapered widths and rounded joins."""
    default_camera_config = dict(background_color="#111119")

    def construct(self):
        x = np.linspace(-6, 6, 200)
        paths = VGroup()
        palette = color_gradient([BLUE, TEAL, GOLD, RED], 64)
        for i in range(64):
            y = 1.8 * np.sin(x * (0.7 + i / 80) + i / 8)
            path = VMobject().set_points_smoothly(np.column_stack([x, y, np.zeros_like(x)]))
            path.set_stroke(palette[i], [0.5, 3.5, 0.5], opacity=0.6).set_joint_roundness(1)
            paths.add(path)
        self.play(ShowCreation(paths, lag_ratio=0.005), run_time=2)
        self.play(paths.animate.apply_function(lambda p: np.array([
            p[0], p[1] + 0.5 * np.sin(2 * p[0]), p[2]
        ])), run_time=2)
