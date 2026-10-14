from manimlib import *


class TexMatching(Scene):
    """LaTeX compilation/cache, glyph rendering and matching string transforms."""

    def construct(self):
        equations = [
            Tex(r"(a+b)^2 = a^2 + 2ab + b^2", font_size=72),
            Tex(r"(a-b)^2 = a^2 - 2ab + b^2", font_size=72),
            Tex(r"a^2 - b^2 = (a+b)(a-b)", font_size=72),
        ]
        self.play(Write(equations[0]), run_time=1)
        self.play(TransformMatchingStrings(equations[0], equations[1]), run_time=1.5)
        self.play(TransformMatchingStrings(equations[1], equations[2]), run_time=1.5)
