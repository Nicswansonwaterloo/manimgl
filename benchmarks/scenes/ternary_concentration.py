from manimlib import *
from benchmarks.support.personal_math import reduced_forms


class TernaryFormCloud(ThreeDScene):
    """15s: n=1..51 concentration, e=1..5 dense clouds, prime highlights, halos and orbit."""
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
        layers = ((0.065, 0.12), (0.04, 0.35), (0.025, 1))
        clouds = Group(*[DotCloud(radius=r, color=c, opacity=o, anti_alias_width=0.65)
                         for c in (BLUE, PINK) for r, o in layers])
        # These layers are a projected density display; blend all halo layers
        # without letting a foreground halo occlude a bright center.
        clouds.deactivate_depth_test()
        title = Text("REDUCED TERNARY FORMS", font_size=24).to_corner(UR).fix_in_frame()
        readout = Integer(1, font_size=26)
        e_readout = Integer(1, font_size=26)
        counters = VGroup(VGroup(Text("n =", font_size=24), readout).arrange(RIGHT, buff=0.15),
                          VGroup(Text("e =", font_size=24), e_readout).arrange(RIGHT, buff=0.15))
        counters.arrange(DOWN, aligned_edge=LEFT, buff=0.15).to_corner(UL).fix_in_frame()
        legend = VGroup(Text("Cross coefficients", font_size=20, fill_color=BLUE),
                        Text("Prime discriminant", font_size=20, fill_color=PINK))
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.1).to_corner(DL).fix_in_frame()
        axes = ThreeDAxes((-1.1, 1.1, 1), (-0.1, 1.1, 1), (-0.1, 1.1, 1),
                         width=6.6, height=3.6, depth=3.6)
        axes.shift(project(ORIGIN) - axes.c2p(0, 0, 0))
        axes.set_stroke(GREY_B, 0.8, opacity=0.5)
        self.add(shell, axes, counters, title, legend)
        self.add(clouds, set_depth_test=False)
        stages = [(n, 1, 0.2) for n in range(1, 52)] + [(51, e, 1.2) for e in range(2, 6)]
        for n, e, duration in stages:
            points, primes = reduced_forms(n, e)
            size = min(1, np.sqrt(700 / max(1, len(points))))
            for category in (0, 1):
                selected = project(points[primes == bool(category)])
                for cloud, (radius, _) in zip(clouds[3*category:3*category+3], layers):
                    cloud.set_points(selected)
                    cloud.set_radius(max(0.016 if category else 0.008, radius * size))
            readout.set_value(n).fix_in_frame()
            e_readout.set_value(e).fix_in_frame()
            self.wait(duration)
