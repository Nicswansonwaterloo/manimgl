from manimlib import *


class GraphTracking(Scene):
    """Graphs, coordinate labels, tracked points and changing decimal glyphs."""

    def construct(self):
        axes = Axes((-4, 4), (-2, 2), width=11, height=5)
        axes.add_coordinate_labels(font_size=18)
        graphs = VGroup(*[
            axes.get_graph(lambda x, k=k: np.sin(k * x), color=BLUE, stroke_opacity=0.35)
            for k in np.linspace(0.5, 3, 12)
        ])
        tracked_graph = axes.get_graph(np.sin, color=YELLOW, stroke_width=3)
        tracker = ValueTracker(-4)
        dot = Dot(fill_color=YELLOW)
        dot.add_updater(lambda m: m.move_to(axes.c2p(tracker.get_value(), np.sin(tracker.get_value()))))
        number = DecimalNumber(-4, font_size=32).to_edge(UP)
        number.add_updater(lambda m: m.set_value(tracker.get_value()))
        self.add(axes, dot, number)
        self.play(ShowCreation(graphs), ShowCreation(tracked_graph), run_time=1)
        self.play(tracker.animate.set_value(4), run_time=3, rate_func=linear)
