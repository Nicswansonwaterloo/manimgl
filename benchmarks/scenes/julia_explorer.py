from manimlib import *


class JuliaExplorer(Scene):
    """Full-frame iterative fragment shader, changing complex parameter and camera zoom."""
    default_camera_config = dict(background_color=BLACK)

    def construct(self):
        plane = ComplexPlane((-4, 4), (-2.25, 2.25), width=14.3, height=8)
        fractal = JuliaFractal(plane, parameter=-0.75 + 0.15j, n_steps=80)
        phase = ValueTracker(0)
        fractal.add_updater(lambda m: m.set_c(-0.75 + 0.04 * np.sin(phase.get_value())
                                            + (0.15 + 0.06 * np.cos(phase.get_value())) * 1j))
        label = Text("Julia shader: 80 iterations / pixel", font="sans-serif", font_size=26).to_corner(UL)
        label.set_backstroke(BLACK, 5).fix_in_frame()
        self.add(fractal, label)
        self.play(phase.animate.set_value(TAU), self.frame.animate.set_height(4).shift(0.4 * LEFT),
                  run_time=4, rate_func=linear)
