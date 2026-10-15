from manimlib import *
from benchmarks.support.hilbert_visuals import rainbow_hilbert, refinement_knots


class HilbertSpaceFilling3D(ThreeDScene):
    """8s: rainbow Hilbert orders 1–4, progressive drawing, refinement morphs and orbit."""
    default_camera_config = dict(background_color="#111022")

    def construct(self):
        title = Text("3D HILBERT · recursive refinement", font="sans-serif", font_size=26).to_corner(UL)
        title.fix_in_frame()
        self.frame.reorient(-35, 65).set_height(10)
        self.frame.add_updater(lambda m, dt: m.increment_theta(0.22 * dt))
        enclosure = VCube(side_length=5.5, fill_opacity=0, stroke_color=GREY_B,
                          stroke_width=0.7, stroke_opacity=0.2).apply_depth_test()
        caption = Text("Order 1 · 8 sites", font_size=22).to_corner(DL).fix_in_frame()
        self.add(title, caption, enclosure)
        knots = refinement_knots(3, 4)
        current, points = rainbow_hilbert(1, 3, knots)
        self.play(ShowCreation(current, lag_ratio=1), run_time=1)
        for order in (2, 3, 4):
            target, points = rainbow_hilbert(order, 3, knots)
            next_caption = Text(f"Order {order} · {8**order:,} sites", font_size=22)
            next_caption.to_corner(DL).fix_in_frame()
            self.play(ReplacementTransform(current, target, path_arc=PI / 6),
                      Transform(caption, next_caption), run_time=1.5)
            current = target
        cursor = ValueTracker(0)
        # Thirty-two local tracers cover the whole curve without one marker
        # teleporting hundreds of corners between adjacent video frames.
        markers = Group(*[GlowDot(path.get_start(), color=WHITE, radius=0.07)
                          for path in current])
        for marker, path in zip(markers, current):
            marker.add_updater(lambda m, dt, path=path: m.move_to(
                path.quick_point_from_proportion(cursor.get_value())))
        highlight = current.copy().set_stroke(WHITE, 2.2, opacity=0.55)
        self.add(markers)
        self.play(cursor.animate.set_value(1), ShowCreation(highlight, lag_ratio=0),
                  run_time=1.5, rate_func=linear)
        self.play(FadeOut(markers), FadeOut(highlight), run_time=1)
