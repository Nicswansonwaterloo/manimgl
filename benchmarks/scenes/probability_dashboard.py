from manimlib import *


class ProbabilityDashboard(Scene):
    """Nested sample spaces, 64-bin distribution, conditional-area rebuilds and decimal glyphs."""
    default_camera_config = dict(background_color="#E8EEE8")

    def construct(self):
        probability = ValueTracker(0.2)

        def partition():
            space = SampleSpace(width=4, height=3, stroke_color=BLACK)
            p = probability.get_value()
            space.divide_horizontally([p, 1 - p], colors=[BLUE_E, TEAL_E])
            for section, colors in zip(space.horizontal_parts, ([GOLD_E, MAROON_E], [BLUE_E, TEAL_E])):
                section.divide_vertically([0.3, 0.7], colors=colors)
            return space.shift(3.5 * LEFT)

        area = always_redraw(partition)
        x = np.linspace(-3, 3, 64)
        chart = BarChart(np.exp(-x * x), width=5.5, height=3.5, label_y_axis=False,
                         bar_stroke_width=0, bar_colors=[BLUE_E, TEAL_E], max_value=1)
        chart.shift(3 * RIGHT)
        chart.x_axis.set_stroke(BLACK, 1, opacity=0.6)
        chart.y_axis.set_stroke(BLACK, 1, opacity=0.6)
        # Subpixel tails must retain nonzero height in float32, so a later
        # stretch cannot magnify roundoff into a spurious isolated spike.
        chart.add_updater(lambda m: m.change_bar_values(np.maximum(0.001, np.exp(
            -((x - 3 * (probability.get_value() - 0.5)) / (0.4 + probability.get_value())) ** 2))))
        number = DecimalNumber(0.2, font_size=42, color=BLACK).to_edge(UP)
        number.add_updater(lambda m: m.set_value(probability.get_value()))
        self.add(area, chart, number)
        self.play(probability.animate.set_value(0.8), run_time=4, rate_func=there_and_back)
