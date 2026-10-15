from manimlib import *
from benchmarks.support.personal_math import EDGES, tetra_representatives, tetra_vertices


class TernaryTetrahedronWalk(ThreeDScene):
    """15s: all 70 tetrahedron morphs, n=8..17 convergence and e=1..3 destination clouds."""
    default_camera_config = dict(background_color=BLACK)
    always_depth_test = False

    def construct(self):
        self.frame.reorient(20, 65)
        self.frame.add_updater(lambda m, dt: m.increment_theta(0.08 * dt))
        reps = tetra_representatives()
        center = tetra_vertices((0,)*6).mean(axis=0)
        project = lambda v: 4 * (v - center)

        def tetra(lam, n=8):
            p = project(tetra_vertices(lam, n))
            faces = VGroup(*[Polygon(*p[list(f)], fill_color=BLUE, fill_opacity=0.1,
                                    stroke_width=0) for f in ((0,2,1),(0,1,3),(0,3,2),(1,2,3))])
            edges = VGroup(*[Line(p[i], p[j], color=interpolate_color(BLUE, PINK, w/6),
                                    stroke_width=2 + w/3) for (i,j), w in zip(EDGES, lam)])
            beads = Group(*[Sphere(radius=0.065, resolution=(15,9), color=BLUE).move_to(v) for v in p])
            beads.apply_depth_test()
            return Group(faces, edges, beads)

        points = np.concatenate([project(tetra_vertices(lam))[2:] for lam in tetra_representatives()])
        destinations = DotCloud(points, radius=0.025, color=GOLD, opacity=0.3, anti_alias_width=0.65)
        current = tetra((0,)*6)
        labels = VGroup(*[Tex(rf"\lambda_{k+1}", font_size=23) for k in range(6)])
        for label, edge in zip(labels, current[1]):
            label.rotate(PI / 2, RIGHT)
            label.set_backstroke(BLACK, 3)
            label.add_updater(lambda m, dt=0, edge=edge: m.move_to(edge.get_center() + 0.16*OUT)
                              .set_color(edge.get_stroke_color()))
        entries = VGroup(*[Integer(0, font_size=25) for _ in range(6)])
        entries.arrange(RIGHT, buff=0.3).to_corner(DL).fix_in_frame()
        title = Text("TETRAHEDRON · edge weights", font_size=24).to_corner(UL).fix_in_frame()
        n_value, e_value = Integer(8, font_size=24), Integer(1, font_size=24)
        parameters = VGroup(Text("n =", font_size=22), n_value,
                            Text("e =", font_size=22), e_value).arrange(RIGHT, buff=0.15)
        parameters.to_corner(UR).fix_in_frame()
        axes = ThreeDAxes((-1, 5), (-1, 5), (-1, 5), width=6, height=6, depth=6)
        axes.shift(project(ORIGIN)-axes.c2p(0, 0, 0)).set_stroke(GREY_B, 0.7, opacity=0.4)
        self.add(axes, destinations, current, labels, entries, title, parameters)
        for lam in reps:
            for entry, value in zip(entries, lam):
                entry.set_value(value).fix_in_frame()
            self.play(Transform(current, tetra(lam)), run_time=2/15, rate_func=linear)
        # The source film then contracts the deformations toward the regular
        # tetrahedron as n grows, followed by denser e-shells of destinations.
        for n in range(8, 18):
            n_value.set_value(n).fix_in_frame()
            target_points = np.concatenate([project(tetra_vertices(lam, n))[2:] for lam in reps])
            self.play(Transform(current, tetra(reps[-1], n)),
                      destinations.animate.set_points(target_points), run_time=0.4, rate_func=linear)
        for e in (2, 3):
            e_value.set_value(e).fix_in_frame()
            dense_reps = tetra_representatives(6*e, walk=False)
            target_points = np.concatenate([project(tetra_vertices(lam, 17))[2:] for lam in dense_reps])
            self.play(destinations.animate.set_points(target_points), run_time=0.8)
        self.wait(1/15)
