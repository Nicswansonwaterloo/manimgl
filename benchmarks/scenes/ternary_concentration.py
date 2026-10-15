from manimlib import *
from benchmarks.support.personal_math import reduced_forms


class TexCounter(Integer):
    def char_to_mob(self, char):
        return Tex(char.replace("–", "-"))


class TernaryFormCloud(ThreeDScene):
    """16s: n=1..51, e=1..6, two plain clouds, changing TeX digits and orbit."""
    default_camera_config = dict(background_color=BLACK)

    def construct(self):
        self.frame.reorient(35, 65)
        self.frame.add_updater(lambda m, dt: m.increment_theta(0.10 * dt))
        vertices = np.array([(-1,0,0), (-1,1,0), (-1,0,1), (0,1,1),
                             (1,0,0), (1,1,0), (1,0,1), (1,1,1)])
        faces = [(0,2,1), (4,5,7,6), (0,4,6,2), (0,1,5,4),
                 (1,3,7,5), (2,6,7,3), (1,2,3)]
        project = lambda p: (p - [0, 0.5, 0.5]) * 3
        shell = VGroup(*[Polygon(*project(vertices[list(f)]), fill_color=BLUE,
                                fill_opacity=0.025, stroke_color=TEAL,
                                stroke_width=1, stroke_opacity=0.4).apply_depth_test()
                         for f in faces])
        clouds = Group(DotCloud(radius=0.023, color=BLUE),
                       DotCloud(radius=0.030, color=PINK))
        # The translucent enclosure must not hide the projected density display.
        clouds.deactivate_depth_test()
        title = Text("REDUCED TERNARY FORMS", font_size=24).to_corner(UR).fix_in_frame()
        readout = TexCounter(1, font_size=26)
        e_readout = TexCounter(1, font_size=26)
        counters = VGroup(VGroup(Tex("n =", font_size=24), readout).arrange(RIGHT, buff=0.15),
                          VGroup(Tex("e =", font_size=24), e_readout).arrange(RIGHT, buff=0.15))
        counters.arrange(DOWN, aligned_edge=LEFT, buff=0.15).to_corner(UL)
        counters.add_background_rectangle(color=BLACK, opacity=0.62, buff=0.1)
        counters.fix_in_frame().set_z_index(10)
        legend = VGroup(Text("Cross coefficients", font_size=20, fill_color=BLUE),
                        Text("Prime discriminant", font_size=20, fill_color=PINK))
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.1).to_corner(DL).fix_in_frame()
        axes = ThreeDAxes((-1.1, 1.1, 1), (-0.1, 1.1, 1), (-0.1, 1.1, 1),
                         width=6.6, height=3.6, depth=3.6)
        axes.shift(project(ORIGIN) - axes.c2p(0, 0, 0))
        axes.set_stroke(GREY_B, 0.8, opacity=0.5)
        self.add(shell, axes, counters, title, legend)
        self.add(clouds, set_depth_test=False)
        stages = [(n, 1, 0.2) for n in range(1, 52)] + [(51, e, 1.2) for e in range(2, 7)]
        for n, e, duration in stages:
            points, primes = reduced_forms(n, e)
            for category, cloud in enumerate(clouds):
                selected = project(points[primes == bool(category)])
                cloud.set_points(selected)
            readout.set_value(n).fix_in_frame().set_z_index(10)
            e_readout.set_value(e).fix_in_frame().set_z_index(10)
            self.wait(duration)
