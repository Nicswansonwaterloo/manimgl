from manimlib import *


class TextGlyphs(Scene):
    """Pango glyph construction, writing and matching shapes (no LaTeX)."""

    def construct(self):
        lines = VGroup(*[
            Text(f"Vector rendering benchmark {i:02d}", font="sans-serif", font_size=26)
            for i in range(14)
        ]).arrange(DOWN, buff=0.13)
        self.play(Write(lines, lag_ratio=0.001), run_time=2)
        target = Text("Geometry in motion", font="sans-serif", font_size=64)
        self.play(TransformMatchingShapes(lines, target), run_time=2)
