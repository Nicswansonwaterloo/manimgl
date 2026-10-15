from manimlib import *


class LinearRankCollapse(ThreeDScene):
    """8s: basis/cube transforms through ranks 2, 1 and 0, restores and camera motion."""

    def construct(self):
        self.frame.reorient(30, 65)
        self.frame.add_updater(lambda m, dt: m.increment_theta(0.08*dt))
        axes = ThreeDAxes((-3,3), (-3,3), (-3,3))
        basis = VGroup(*[Arrow(ORIGIN, 2*v, buff=0, fill_color=c)
                         for v, c in zip((RIGHT, UP, OUT), (BLUE, GREEN, RED))])
        cube = Cube(side_length=2, color=BLUE, opacity=0.25)
        basis.save_state()
        cube.save_state()
        self.add(axes, cube, basis)
        matrices = [np.array([[1,0,1], [1,0,0], [0.5,0,0]]),
                    np.array([[0.5,0,1], [0.5,0,1], [0.5,0,1]]), np.zeros((3,3))]
        for rank, matrix in zip((2,1,0), matrices):
            title = Tex(rf"\operatorname{{rank}}L={rank}", font_size=30).to_corner(UL).fix_in_frame()
            self.add(title)
            images = VGroup(*[Arrow(ORIGIN, 2*v, buff=0, fill_color=c) if np.linalg.norm(v) else
                              Dot(ORIGIN, radius=0.07, fill_color=c)
                              for v, c in zip(matrix.T, (BLUE,GREEN,RED))])
            self.play(Transform(basis, images),
                      Transform(cube, cube.copy().apply_matrix(matrix, about_point=ORIGIN)), run_time=2)
            self.play(Restore(basis), Restore(cube), run_time=2/3)
            self.remove(title)
