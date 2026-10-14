from manimlib import *
from benchmarks.support.assets import checker_image


class TexturedSurfaceOrbit(ThreeDScene):
    """UV textures on surfaces, translucent layers and a moving 3D camera."""

    def construct(self):
        sphere = TexturedSurface(Sphere(radius=1.4, resolution=(81, 41)), checker_image())
        torus = Torus(r1=2.5, r2=0.35, resolution=(81, 31), color=TEAL, opacity=0.5)
        torus.set_sort_to_camera(True)
        overlay = Text("Textured surface", font="sans-serif", font_size=28).to_corner(UL)
        overlay.fix_in_frame()
        self.add(sphere, torus, overlay)
        self.play(Rotate(sphere, angle=TAU, axis=OUT),
                  self.frame.animate.reorient(60, 65), run_time=4, rate_func=linear)
