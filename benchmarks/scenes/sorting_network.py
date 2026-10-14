from manimlib import *


class SortingNetwork(Scene):
    """Bitonic sorting: fifteen compare/swap stages, 32 bars and animated connections."""
    default_camera_config = dict(background_color="#101827")

    def construct(self):
        values = np.random.default_rng(32).permutation(np.linspace(0.4, 4.8, 32))
        palette = color_gradient([TEAL, BLUE, PINK, GOLD], 32)
        bars = VGroup(*[Rectangle(width=0.27, height=value, stroke_width=0,
                                 fill_color=palette[i], fill_opacity=1)
                        .move_to([(i - 15.5) * 0.35, -2.7 + value / 2, 0])
                        for i, value in enumerate(values)])
        self.add(bars)
        for size in [2, 4, 8, 16, 32]:
            stride = size // 2
            while stride:
                target = values.copy()
                connections = VGroup()
                for i in range(32):
                    j = i ^ stride
                    if j > i:
                        connections.add(ArcBetweenPoints(bars[i].get_top(), bars[j].get_top(),
                                                          angle=PI / 3, stroke_color=GREY_B, stroke_width=1))
                        if (values[i] > values[j]) == (i & size == 0):
                            target[i], target[j] = values[j], values[i]
                self.add(connections)
                self.play(*[bar.animate.stretch_to_fit_height(value).set_y(-2.7 + value / 2)
                            for bar, value in zip(bars, target)], run_time=4 / 15, rate_func=linear)
                self.remove(connections)
                values = target
                stride //= 2
