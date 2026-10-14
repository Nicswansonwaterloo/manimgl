from manimlib import *


class CameraPanZoom(InteractiveScene):
    """InteractiveScene setup plus scripted 2D pan/zoom and fixed overlay."""

    def construct(self):
        plane = NumberPlane((-12, 12), (-7, 7))
        shapes = VGroup(*[Circle(radius=0.2).move_to([x, y, 0]).set_fill(TEAL, 0.7)
                          for x in range(-10, 11) for y in range(-5, 6)])
        label = Text("Camera pan / zoom", font="sans-serif", font_size=28).to_corner(UL)
        label.fix_in_frame()
        self.add(plane, shapes, label)
        self.play(self.frame.animate.set_height(4).move_to(3 * RIGHT + UP), run_time=2)
        self.play(self.frame.animate.set_height(10).move_to(2 * LEFT), run_time=2)
