from manimlib import *
from benchmarks.support.assets import texture_image


class DualTextureLighting3D(ThreeDScene):
    """Separate light/dark surface textures under a moving light and camera."""
    default_camera_config = dict(light_source_position=[-4, -3, 4])

    def construct(self):
        shapes = Group(
            TexturedSurface(Sphere(radius=1.3, resolution=(41, 21)), texture_image(2), texture_image(17)),
            TexturedSurface(Torus(r1=1.1, r2=0.4, resolution=(41, 21)), texture_image(6), texture_image(29)),
        ).arrange(RIGHT, buff=1)
        self.frame.reorient(-25, 60).set_height(7)
        self.add(shapes)
        self.play(Rotate(self.camera.light_source, TAU, about_point=ORIGIN),
                  Rotate(shapes, PI / 3, axis=UP), self.frame.animate.reorient(30, 70),
                  run_time=4, rate_func=linear)
