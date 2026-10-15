from manimlib import *
from benchmarks.support.personal_math import elliptic_multiples
from benchmarks.support.elliptic_visuals import elliptic_curve, visible_additions


class EllipticChordBuild(Scene):
    """8s: elliptic addition, accumulating dots, short chord/reflection plays and restores."""

    def construct(self):
        plane = NumberPlane((-2, 3), (-4.5, 4.5), width=11, height=5.8)
        plane.set_stroke(opacity=0.35)
        coords = elliptic_multiples(1200)
        anchor = Dot(plane.c2p(0, 1), radius=0.07, fill_color=GOLD)
        title = Tex(r"y^2=x^3-x+1", font_size=30).to_corner(UL)
        caption = Tex(r"P+Q=R", font_size=30).to_edge(DOWN)
        self.add(plane, elliptic_curve(plane), title, caption, anchor)
        for q, nxt in visible_additions(coords, 8):
            previous = Dot(plane.c2p(*q), radius=0.055, fill_color=BLUE)
            result = Dot(plane.c2p(*nxt), radius=0.055, fill_color=BLUE)
            previous.save_state()
            self.add(previous)
            x, y = nxt
            reflected = Dot(plane.c2p(x, -y), radius=0.05, fill_color=PINK)
            chord = Line(previous.get_center(), reflected.get_center(), color=TEAL)
            vertical = Line(reflected.get_center(), result.get_center(), color=TEAL)
            self.play(ShowCreation(chord), run_time=0.2)
            self.play(FadeIn(reflected), run_time=0.2)
            self.play(ShowCreation(vertical), FadeOut(chord), run_time=0.2)
            self.play(FadeIn(result), Restore(previous), run_time=0.2)
            self.play(result.animate.set_color(YELLOW).scale(1.6),
                      FadeOut(vertical), reflected.animate.set_opacity(0.3), run_time=0.2)
