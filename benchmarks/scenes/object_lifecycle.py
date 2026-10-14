from manimlib import *


class ObjectLifecycle(Scene):
    """Allocate, add and remove 72 fresh vector mobjects at each frame; no reusable pool."""
    default_camera_config = dict(background_color="#321F23")

    def construct(self):
        live = VGroup()
        palette = color_gradient([GOLD, RED, PINK, BLUE], 72)

        def replace_frame(_):
            self.remove(*live.submobjects)
            live.set_submobjects([])
            for i in range(72):
                phase = TAU * i / 72
                radius = 0.8 + 2.5 * ((self.time * 0.6 + i / 72) % 1)
                piece = RegularPolygon(n=3 + i % 5, radius=0.08 + 0.02 * (i % 3))
                piece.set_fill(palette[i], 0.9).set_stroke(width=0)
                piece.rotate(phase + self.time).move_to([
                    1.6 * radius * np.cos(phase + self.time), radius * np.sin(phase + self.time), 0
                ])
                live.add(piece)
            self.add(*live.submobjects)

        controller = Mobject().add_updater(replace_frame)
        self.add(controller)
        self.wait(4)
