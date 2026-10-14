from manimlib import *


class ClippedSolids3D(ThreeDScene):
    """Animated shader clip planes on solid, translucent and vector 3D geometry."""
    default_camera_config = dict(background_color="#20362F")

    def construct(self):
        objects = Group(
            Sphere(radius=1.1, color=GOLD, resolution=(81, 41)).shift(3 * LEFT),
            Torus(r1=1.2, r2=0.45, color=BLUE, opacity=0.7, resolution=(81, 41)),
            VCube(side_length=2, fill_color=RED, stroke_color=WHITE, stroke_width=2).shift(3 * RIGHT),
        )
        sweep = ValueTracker(-1.5)
        for obj in objects:
            obj.add_updater(lambda m: m.set_clip_plane(UP, sweep.get_value()))
        self.frame.reorient(-20, 65).set_height(9)
        self.add(objects)
        self.play(sweep.animate.set_value(1.5), self.frame.animate.reorient(35, 70),
                  run_time=4, rate_func=there_and_back)
