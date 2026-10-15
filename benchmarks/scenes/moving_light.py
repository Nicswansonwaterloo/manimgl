from manimlib import *


class MovingLight3D(ThreeDScene):
    """A moving point light across matte, reflective and glossy surfaces with wire geometry."""
    default_camera_config = dict(background_color="#171020", light_source_position=[-4, -3, 3])

    def construct(self):
        objects = Group()
        materials = [(0.1, 0.6, 0), (0.5, 0.3, 0.1), (0.8, 0.5, 1)]
        for i, shading in enumerate(materials):
            sphere = Sphere(radius=0.9, resolution=(81, 41), color=[BLUE, GOLD, RED][i], shading=shading)
            torus = Torus(r1=0.9, r2=0.18, resolution=(61, 25), color=TEAL, shading=shading)
            sphere.shift((i - 1) * 3 * RIGHT + UP)
            torus.shift((i - 1) * 3 * RIGHT + DOWN)
            objects.add(sphere, torus)
        marker = GlowDot(radius=0.15, color=WHITE)
        marker.add_updater(lambda m: m.move_to(self.camera.light_source.get_center()))
        self.frame.reorient(0, 50).set_height(11)
        self.add(objects, marker)
        self.play(Rotate(self.camera.light_source, angle=TAU, axis=OUT, about_point=ORIGIN),
                  self.frame.animate.reorient(25, 60), run_time=4, rate_func=linear)
