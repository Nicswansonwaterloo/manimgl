from manimlib import *


class Solids3D(ThreeDScene):
    """Opaque solids, lighting, depth testing and camera orbit with 4x MSAA."""

    def construct(self):
        solids = Group(
            Cube(side_length=1.5, color=BLUE),
            Sphere(radius=0.8, color=TEAL, resolution=(61, 31)),
            Cylinder(radius=0.65, height=1.8, color=YELLOW),
            Cone(radius=0.8, height=1.8, color=RED),
        ).arrange(RIGHT, buff=0.6)
        self.add(solids)
        self.play(Rotate(solids, angle=PI, axis=UP), run_time=2)
        self.play(self.frame.animate.reorient(40, 65), run_time=2)
