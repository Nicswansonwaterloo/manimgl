from manimlib import *
from benchmarks.support.hilbert_visuals import rainbow_hilbert


class HilbertSpaceFilling3D(ThreeDScene):
    """8s: rainbow Hilbert orders 1–4, progressive drawing, refinement morphs and orbit."""
    default_camera_config = dict(background_color="#111022")

    def construct(self):
        title = Text("3D HILBERT · recursive refinement", font="sans-serif", font_size=26).to_corner(UL)
        title.fix_in_frame()
        self.frame.reorient(-35, 65).set_height(8)
        self.add(title)
        current, points = rainbow_hilbert(1, 3)
        self.play(ShowCreation(current, lag_ratio=1), run_time=1)
        for order in (2, 3, 4):
            target, points = rainbow_hilbert(order, 3)
            self.play(ReplacementTransform(current, target, path_arc=PI / 6),
                      self.frame.animate.reorient(-35 + 30 * order, 65), run_time=1.5)
            current = target
        cursor = ValueTracker(0)
        marker = GlowDot(points[0], color=WHITE, radius=0.1)
        marker.add_updater(lambda m: m.move_to(points[min(int(cursor.get_value()), len(points) - 1)]))
        self.add(marker)
        self.play(cursor.animate.set_value(len(points) - 1), self.frame.animate.reorient(120, 75),
                  run_time=1.5, rate_func=linear)
        self.play(FadeOut(marker), self.frame.animate.reorient(150, 65), run_time=1)
