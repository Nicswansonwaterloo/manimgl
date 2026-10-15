from manimlib import *
from benchmarks.support.personal_math import elliptic_multiples
from benchmarks.support.elliptic_visuals import elliptic_curve, visible_additions


class EllipticDotSquiggle(Scene):
    """8s: 1,000 individual elliptic dots, 200 wave updaters and overlapping restores."""

    def construct(self):
        plane = NumberPlane((-4, 8), (-6, 6), width=12, height=6)
        plane.set_stroke(opacity=0.25)
        coords = elliptic_multiples(1200)
        visible = [(x, sign*y) for x, y in coords for sign in (1, -1)
                   if -4 < x < 8 and abs(y) < 6][:1000]
        colors = color_gradient([BLUE, PURPLE, PINK], len(visible))
        dots = VGroup(*[Dot(plane.c2p(*p), radius=0.035, fill_color=c)
                        for p, c in zip(sorted(visible, key=lambda p: p[1]), colors)])
        rng = np.random.default_rng(310)
        for i, dot in enumerate(dots):
            dot.save_state()
            if i % 5 == 0:
                turn_animation_into_updater(ApplyWave(
                    dot, amplitude=0.025, direction=rotate_vector(UP, rng.uniform(0, TAU)),
                    run_time=2 + rng.random()), cycle=True)
        self.add(plane, elliptic_curve(plane, xmax=3.3), dots,
                 Tex(r"y^2=x^3-x+1", font_size=30).to_corner(UL))
        anchor = plane.c2p(0, 1)
        # Keep ten visible additions from the same orbit used for the wallpaper.
        steps = visible_additions(coords, 10, x_range=(-3.5, 3.3), y_limit=5.8)
        for q, nxt in steps:
            target = plane.c2p(*nxt)
            dot = min(dots, key=lambda d: np.linalg.norm(d.get_center() - target))
            dot.clear_updaters()
            reflection = plane.c2p(nxt[0], -nxt[1])
            previous = plane.c2p(*q)
            start = max((anchor, previous), key=lambda p: np.linalg.norm(p-reflection))
            chord = Line(start, reflection, color=WHITE, stroke_width=1)
            vertical = Line(reflection, target, color=TEAL, stroke_width=1)
            self.play(ShowCreation(chord), run_time=0.2)
            self.play(ShowCreation(vertical), FadeOut(chord), run_time=0.2)
            self.play(dot.animate.scale(2).set_color(YELLOW), run_time=0.2)
            self.play(FadeOut(vertical), run_time=0.2)
            turn_animation_into_updater(Restore(dot, run_time=2))
