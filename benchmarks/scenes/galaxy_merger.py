from collections import deque

from manimlib import *
from benchmarks.support.algorithms import softened_acceleration


class GalaxyMergerNBody3D(ThreeDScene):
    """15s: direct 1,026-body gravity, fixed simulation steps, 32 live trails and orbiting camera."""
    default_camera_config = dict(background_color="#030611")

    def construct(self):
        rng = np.random.default_rng(1026)
        positions, velocities = [], []
        for sign in [-1, 1]:
            radius = rng.uniform(0.15, 1.65, 512)
            theta = rng.uniform(0, TAU, 512)
            disk = np.column_stack([radius * np.cos(theta), radius * np.sin(theta), rng.normal(0, 0.035, 512)])
            speed = np.sqrt(0.15 * 12 / radius)
            motion = np.column_stack([-speed * np.sin(theta), speed * np.cos(theta), np.zeros(512)])
            tilt = rotation_matrix(sign * 25 * DEGREES, RIGHT)
            positions.extend(disk @ tilt.T + [sign * 2.5, 0, 0])
            velocities.extend(motion @ tilt.T + [-sign * 0.22, sign * 0.12, 0])
        positions = np.array([*positions, [-2.5, 0, 0], [2.5, 0, 0]], dtype=float)
        velocities = np.array([*velocities, [0.22, -0.12, 0], [-0.22, 0.12, 0]], dtype=float)
        masses = np.array([*np.full(1024, 4 / 512), 12, 12])
        stars = DotCloud(positions[:1024], radius=0.035, color=BLUE)
        stars.set_rgba_array(np.array([*([color_to_rgba(BLUE)] * 512), *([color_to_rgba(GOLD)] * 512)]))
        cores = DotCloud(positions[-2:], radius=0.075, color=WHITE)
        core_halos = GlowDots(positions[-2:], radius=0.25, color=GOLD)
        tracked = np.arange(0, 1024, 32)
        histories = [deque(maxlen=120) for _ in tracked]
        trails = VGroup(*[VMobject(stroke_color=TEAL if i < 16 else GOLD, stroke_width=1,
                                  stroke_opacity=0.6) for i in range(len(tracked))])
        state = dict(accumulator=0.0, acceleration=softened_acceleration(positions, masses))
        step = 1 / 120

        def integrate(_, dt):
            state["accumulator"] += dt
            while state["accumulator"] >= step - 1e-9:
                # Velocity Verlet: reuse the previous acceleration, evaluate all
                # pairs again after the drift, then finish the symmetric kick.
                velocities[:] += 0.5 * step * state["acceleration"]
                positions[:] += step * velocities
                state["acceleration"] = softened_acceleration(positions, masses)
                velocities[:] += 0.5 * step * state["acceleration"]
                state["accumulator"] -= step
            stars.set_points(positions[:1024])
            cores.set_points(positions[-2:])
            core_halos.set_points(positions[-2:])
            if dt > 0:
                for trail, history, index in zip(trails, histories, tracked):
                    history.append(positions[index].copy())
                    if len(history) >= 2:
                        trail.set_points_as_corners(history)

        controller = Mobject().add_updater(integrate)
        label = Text("GALAXY MERGER · direct all-pairs gravity", font="sans-serif", font_size=25).to_corner(UL)
        label.fix_in_frame()
        self.frame.set_height(11).reorient(-20, 50)
        self.add(stars, core_halos, cores, trails, controller, label)
        self.play(self.frame.animate.reorient(60, 70), run_time=15, rate_func=linear)
