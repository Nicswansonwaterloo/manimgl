from manimlib import *


class MultiScaleZoom(Scene):
    """729 nested triangles, small-scale antialiasing and a deep moving-camera zoom."""
    default_camera_config = dict(background_color="#FEF7DB")

    def construct(self):
        triangles = VGroup()

        def build(vertices, depth):
            if depth == 0:
                triangles.add(Polygon(*vertices, stroke_width=0, fill_opacity=1, fill_color=BLUE_E))
                return
            a, b, c = vertices
            build([a, (a + b) / 2, (a + c) / 2], depth - 1)
            build([(a + b) / 2, b, (b + c) / 2], depth - 1)
            build([(a + c) / 2, (b + c) / 2, c], depth - 1)

        build([np.array([-5, -3, 0]), np.array([5, -3, 0]), np.array([0, 3.5, 0])], 6)
        label = Text("729 triangles: zoom across six scales", font="sans-serif", font_size=26, fill_color=BLACK)
        label.to_corner(UL).fix_in_frame()
        self.add(triangles, label)
        self.play(self.frame.animate.set_height(0.4).move_to([-4.65, -2.75, 0]), run_time=3)
        self.play(self.frame.animate.set_height(8).move_to(ORIGIN), run_time=1)
