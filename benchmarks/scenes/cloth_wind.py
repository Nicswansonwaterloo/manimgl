from manimlib import *
from benchmarks.support.assets import checker_image


class ClothWindSimulation3D(ThreeDScene):
    """15s: 4,617 constrained cloth particles, textured deformation, 138 mesh lines and 513 beads."""
    default_camera_config = dict(background_color="#182A30", light_source_position=[-4, -3, 7])

    def construct(self):
        nu, nv = 81, 57
        x, y = np.meshgrid(np.linspace(-3, 3, nu), np.linspace(-2, 2, nv), indexing="ij")
        rest = np.stack([x, y, np.full_like(x, 2.2)], axis=-1)
        positions, previous = rest.copy(), rest.copy()
        surface = TexturedSurface(ParametricSurface(lambda u, v: [u, v, 2.2],
            u_range=(-3, 3), v_range=(-2, 2), resolution=(nu, nv), shading=(0.5, 0.3, 0.4)), checker_image())
        lines = VGroup(*[VMobject(stroke_color=WHITE, stroke_width=0.5,
                                 stroke_opacity=0.28).apply_depth_test() for _ in range(nu + nv)])
        bead_indices = [(i, j) for i in range(0, nu, 3) for j in range(0, nv, 3)]
        beads = Group(*[Sphere(radius=0.035, resolution=(9, 7), color=GOLD).move_to(rest[i, j])
                        for i, j in bead_indices])
        pins = [(0, 0), (0, nv - 1), (nu - 1, 0), (nu - 1, nv - 1)]
        supports = Group(*[Line3D(rest[i, j] + 3.2 * IN, rest[i, j], width=0.05,
                                  resolution=(9, 2), color=GREY_B) for i, j in pins])
        ground = Square3D(side_length=10, color=GREY_E).shift(1.02 * IN)
        simulation_time = [0.0]

        def constrain(axis, length):
            low, high = (positions[:-1], positions[1:]) if axis == 0 else (positions[:, :-1], positions[:, 1:])
            delta = high - low
            distance = np.maximum(np.linalg.norm(delta, axis=-1, keepdims=True), 1e-8)
            correction = 0.5 * (1 - length / distance) * delta
            low += correction
            high -= correction

        def simulate(_, dt):
            if dt > 0:
                steps = max(1, int(np.ceil(dt * 120 - 1e-8)))
                h = dt / steps
                for _ in range(steps):
                    t = simulation_time[0]
                    velocity = (positions - previous) * 0.995
                    previous[:] = positions
                    wind = np.zeros_like(positions)
                    wind[..., 2] = -2.5 + 3.5 * np.sin(2 * t + x) * np.cos(y + t)
                    wind[..., 0] = 0.5 * np.sin(t + y)
                    positions[:] += velocity + h * h * wind
                    for _ in range(12):
                        constrain(0, 6 / (nu - 1))
                        constrain(1, 4 / (nv - 1))
                        for i, j in pins:
                            positions[i, j] = rest[i, j]
                        positions[..., 2] = np.maximum(positions[..., 2], -0.95)
                    simulation_time[0] += h
            surface.set_points(positions.reshape(-1, 3))
            # Lift stitching along the deformed normal. Coplanar strokes used
            # to shimmer against the surface and show through its folds.
            normals = np.cross(np.gradient(positions, axis=0), np.gradient(positions, axis=1))
            normals /= np.maximum(np.linalg.norm(normals, axis=-1, keepdims=True), 1e-8)
            stitching = positions + 0.012 * normals
            for i in range(nu):
                lines[i].set_points_as_corners(stitching[i])
            for j in range(nv):
                lines[nu + j].set_points_as_corners(stitching[:, j])
            for bead, (i, j) in zip(beads, bead_indices):
                bead.move_to(positions[i, j] + 0.04 * normals[i, j])

        simulate(None, 0)
        controller = Mobject().add_updater(simulate)
        title = Text("CONSTRAINED CLOTH · wind + gravity", font="sans-serif", font_size=25).to_corner(UL)
        title.fix_in_frame()
        self.frame.reorient(-35, 65).set_height(11)
        self.add(ground, supports, surface, lines, beads, controller, title)
        self.play(self.frame.animate.reorient(75, 65),
                  Rotate(self.camera.light_source, angle=PI, axis=OUT, about_point=ORIGIN),
                  run_time=15, rate_func=linear)
