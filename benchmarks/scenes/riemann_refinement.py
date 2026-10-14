from manimlib import *


class RiemannRefinement(Scene):
    """Riemann partitions refined 16 to 256 rectangles, braces and numeric readout."""
    default_camera_config = dict(background_color="#ECEFF4")

    def construct(self):
        axes = Axes((0, 8), (0, 4), width=11, height=5, axis_config=dict(stroke_color=BLACK))
        graph = axes.get_graph(lambda x: 1.7 + np.sin(x), color=BLUE_E)
        partitions = [axes.get_riemann_rectangles(graph, x_range=(0, 8), dx=8 / n,
                                                stroke_width=0.5, fill_opacity=0.8)
                      for n in [16, 32, 64, 128, 256]]
        counter = Integer(16, color=BLACK, font_size=32).to_corner(UR)
        brace = Brace(axes.x_axis, DOWN, color=BLACK)
        self.add(axes, graph, partitions[0], counter, brace)
        current = partitions[0]
        for n, partition in zip([32, 64, 128, 256], partitions[1:]):
            self.play(ReplacementTransform(current, partition), ChangeDecimalToValue(counter, n), run_time=1)
            current = partition
