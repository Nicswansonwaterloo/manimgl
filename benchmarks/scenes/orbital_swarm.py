from manimlib import *


class OrbitalSwarm600(Scene):
    """600 separate vector dots, orbital updaters, twelve fading traces and central glow."""
    default_camera_config = dict(background_color="#061625")

    def construct(self):
        rng = np.random.default_rng(600)
        swarm = VGroup()
        palette = color_gradient([TEAL, BLUE, PINK, GOLD], 600)
        for i in range(600):
            radius, phase = rng.uniform(0.4, 3.1), rng.uniform(0, TAU)
            speed = 0.5 + 1.5 / (radius + 0.5)
            dot = Dot(radius=0.015 + 0.008 * (i % 3), fill_color=palette[i])
            dot.add_updater(lambda m, dt, r=radius, p=phase, w=speed: m.move_to([
                1.8 * r * np.cos(p + w * self.time), r * np.sin(p + w * self.time), 0
            ]))
            swarm.add(dot)
        traces = VGroup(*[TracedPath(dot.get_center, time_traced=0.6, stroke_width=1,
                                   stroke_color=dot.get_color()) for dot in swarm[::50]])
        self.add(GlowDot(radius=0.35, color=GOLD), swarm, traces)
        self.wait(4)
