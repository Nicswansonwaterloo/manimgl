from manimlib import *
from math import isqrt, sqrt


class ArithmeticSemicircleSweep(Scene):
    """6s: four compressed 0.5s sweeps, small vector dots, cleanup and faded old passes."""

    def construct(self):
        plane = NumberPlane((-3.2, 3.2), (0, 3.4), width=11, height=5.8)
        plane.shift(2.7*DOWN - plane.c2p(0, 0))
        plane.set_stroke(opacity=0.25)
        self.add(plane)
        for n in (3, 7, 12, 18):
            scale = 2*sqrt(n)
            bound = isqrt(36*n)
            lines = VGroup(*[Line(plane.c2p(b/scale, 0), plane.c2p(b/scale, 3.15),
                                 stroke_width=1, stroke_opacity=0.3, color=BLUE)
                             for b in range(-bound, bound+1)])
            title = Tex(rf"n={n}", font_size=30).to_corner(UL)
            self.play(FadeIn(lines), FadeIn(title), run_time=0.2)
            current, arcs, writes = VGroup(), VGroup(), []
            for m in range(1, 10):
                arc = Arc(start_angle=0, angle=PI, radius=plane.x_axis.get_unit_size()*sqrt(m),
                          arc_center=plane.c2p(0, 0), color=BLUE, stroke_width=2)
                dots = VGroup(*[Dot(plane.c2p(b/scale, sqrt(4*n*m-b*b)/scale),
                                       radius=0.042, fill_color=BLUE_B)
                               for b in range(-bound, bound+1) if b*b < 4*n*m])
                current.add(dots)
                arcs.add(arc)
                write = Write(dots, rate_func=linear)
                write.begin()
                writes.append(write)

            def sweep(mob, alpha):
                progress = alpha * len(writes)
                for i, (arc, write) in enumerate(zip(arcs, writes)):
                    phase = np.clip(progress - i, 0, 1)
                    opacity = 1 if progress < i else min(4 * phase, 4 * (1 - phase), 1)
                    arc.set_stroke(opacity=float(opacity))
                    write.interpolate(np.clip(2 * (phase - 0.25), 0, 1))

            self.play(UpdateFromAlphaFunc(VGroup(arcs, current), sweep), run_time=0.5, rate_func=linear)
            for write in writes:
                write.finish()
            self.remove(arcs)
            self.wait(0.5)
            self.play(current.animate.set_color(GREY_B).set_opacity(0.25),
                      FadeOut(lines), FadeOut(title), run_time=0.4)
