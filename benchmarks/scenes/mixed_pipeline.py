from manimlib import *
from benchmarks.support.assets import checker_image, checker_video, vector_image


class MixedPipelineCarousel(ThreeDScene):
    """Mixed shader families: SVG, text, image, streaming video, dots and shaded surfaces."""
    default_camera_config = dict(background_color="#271734")

    def construct(self):
        rng = np.random.default_rng(7)
        objects = Group(
            SVGMobject(vector_image()).set_height(1.6),
            ImageMobject(checker_image(), height=1.6),
            VideoMobject(checker_video(), height=1.6, preload=False, loop=True).play_from(0),
            Sphere(radius=0.8, color=GOLD, resolution=(51, 31)),
            DotCloud(rng.normal(size=(2000, 3)) * 0.4, radius=0.025, color=TEAL),
            Torus(r1=0.65, r2=0.2, color=PINK, resolution=(51, 31)),
        )
        for i, obj in enumerate(objects):
            angle = TAU * i / len(objects)
            obj.move_to([3.2 * np.cos(angle), 3.2 * np.sin(angle), 0])
        title = Text("Mixed shader / texture / depth workload", font="sans-serif", font_size=26).to_corner(UL)
        title.fix_in_frame()
        self.frame.set_height(10).reorient(-25, 55)
        self.add(objects, title)
        self.play(Rotate(objects, angle=PI, axis=OUT), self.frame.animate.reorient(20, 70),
                  run_time=4, rate_func=linear)
