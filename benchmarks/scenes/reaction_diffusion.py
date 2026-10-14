from manimlib import *
from benchmarks.support.algorithms import gray_scott_step


class ReactionDiffusionLaboratory(Scene):
    """15s: two chemical PDEs, 10,240 simulation cells, 2,560 vector tiles and evolving profiles."""
    default_camera_config = dict(background_color="#101824")

    def construct(self):
        height, width = 80, 128
        rng = np.random.default_rng(12880)
        a, b = np.ones((height, width)), np.zeros((height, width))
        yy, xx = np.indices(a.shape)
        for row, col in [(20, 24), (55, 30), (35, 63), (60, 95), (18, 105), (15, 65)]:
            mask = (yy - row)**2 + (xx - col)**2 < 8**2
            a[mask] = 0.5
            b[mask] = 0.25 + rng.uniform(-0.03, 0.03, mask.sum())
        colors = color_gradient(["#101824", BLUE_E, TEAL, YELLOW, RED], 256)
        tiles = VGroup(*[
            Square(side_length=0.146, stroke_width=0, fill_opacity=1)
            .move_to([(col - 31.5) * 0.145 - 1.1, (row - 19.5) * 0.145, 0])
            for row in range(40) for col in range(64)
        ])
        profile_x = np.linspace(4.1, 6.4, width)
        profiles = VGroup(*[VMobject(stroke_color=color, stroke_width=2) for color in [TEAL, GOLD]])
        title = Text("REACTION–DIFFUSION · Gray–Scott dynamics", font="sans-serif", font_size=24).to_edge(UP)
        captions = VGroup(Text("Mean B / column", font="sans-serif", font_size=18).move_to([5.2, 2.2, 0]),
                          Text("Mean A / column", font="sans-serif", font_size=18).move_to([5.2, -0.3, 0]))
        state = dict(a=a, b=b, accumulator=0.0, steps=0)

        def evolve(_, dt):
            state["accumulator"] += dt * 240
            while state["accumulator"] >= 1 - 1e-8:
                state["a"], state["b"] = gray_scott_step(state["a"], state["b"],
                    feed=0.035 + 0.003 * np.sin(state["steps"] / 400))
                state["accumulator"] -= 1
                state["steps"] += 1
            field = np.clip(state["b"][::2, ::2] * 3.5, 0, 1)
            for tile, value in zip(tiles, field.ravel()):
                tile.set_fill(colors[int(value * 255)], opacity=1)
            profiles[0].set_points_as_corners(np.column_stack([
                profile_x, 0.7 + 3 * state["b"].mean(axis=0), np.zeros(width)]))
            profiles[1].set_points_as_corners(np.column_stack([
                profile_x, -2.2 + state["a"].mean(axis=0), np.zeros(width)]))

        controller = Mobject().add_updater(evolve)
        self.add(tiles, profiles, title, captions, controller)
        self.wait(15)
