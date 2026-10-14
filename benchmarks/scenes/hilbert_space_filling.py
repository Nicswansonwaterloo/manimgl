from manimlib import *
from benchmarks.support.algorithms import hilbert_points_3d


class HilbertSpaceFilling3D(ThreeDScene):
    """15s: 3D Hilbert orders 2–6 up to 262,144 sites, 4,096 depth-tested stroke chunks and orbit."""
    default_camera_config = dict(background_color="#111022")

    def construct(self):
        title = Text("3D HILBERT CURVE · orders 2 → 6", font="sans-serif", font_size=26).to_corner(UL)
        title.fix_in_frame()
        self.frame.reorient(-35, 65).set_height(9)
        box = VCube(side_length=5.8, fill_opacity=0, stroke_color=GREY_B, stroke_width=1)
        self.add(box, title)

        def curve(order):
            points = 5.4 * (hilbert_points_3d(order) / ((1 << order) - 1) - 0.5)
            paths = VGroup()
            starts = list(range(0, len(points) - 1, 64))
            colors = color_gradient([BLUE, TEAL, GOLD, RED], len(starts))
            for start, color in zip(starts, colors):
                path = VMobject().set_points_as_corners(points[start:start + 65])
                path.set_stroke(color, max(1, 5 - order * 0.65)).set_flat_stroke(False)
                paths.add(path)
            return paths, points

        current, _ = curve(2)
        self.play(ShowCreation(current), run_time=1.5)
        for order, duration, angle in [(3, 2, -10), (4, 2.5, 20), (5, 3, 50), (6, 4, 80)]:
            target, points = curve(order)
            self.play(ReplacementTransform(current, target),
                      self.frame.animate.reorient(angle, 65), run_time=duration)
            current = target
        cursor = ValueTracker(0)
        marker = GlowDot(points[0], color=YELLOW, radius=0.07)
        tail = VMobject(stroke_color=WHITE, stroke_width=3)

        def trace_tail(m):
            index = min(int(cursor.get_value()), len(points) - 1)
            m.set_points_as_corners(points[max(0, index - 128):index + 1] if index else points[:2])
            marker.move_to(points[index])

        tail.add_updater(trace_tail)
        self.add(tail, marker)
        self.play(cursor.animate.set_value(len(points) - 1), self.frame.animate.reorient(120, 75),
                  run_time=2, rate_func=linear)
