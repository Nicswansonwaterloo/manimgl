from manimlib import *


def part_endpoints():
    """Four corresponding states: block assembly, sphere, helix, exploded assembly."""
    grid = np.array(list(np.ndindex(10, 10, 10)), dtype=np.float32) / 9 - 0.5
    sphere = grid / np.maximum(np.linalg.norm(grid, axis=1, keepdims=True), 1e-6) * 0.45
    count = 96
    states = [[] for _ in range(4)]
    for i, cell in enumerate(np.ndindex(8, 4, 3)):
        center = (np.array(cell) - [3.5, 1.5, 1]) * 1.05
        angle = i * PI * (3 - np.sqrt(5))
        z = 1 - 2 * (i + 0.5) / count
        shell_center = 3.8 * np.array([np.sqrt(1-z*z) * np.cos(angle),
                                      np.sqrt(1-z*z) * np.sin(angle), z])
        theta = i * TAU * 3 / count
        helix_center = np.array([2.8 * np.cos(theta), 2.8 * np.sin(theta),
                                 6.5 * (i / (count - 1) - 0.5)])
        rotation = rotation_matrix(angle * 0.35, np.array([1, 2, 3]))
        states[0].append((0.65 * grid + center).astype(np.float32))
        states[1].append((0.7 * sphere @ rotation.T + shell_center).astype(np.float32))
        states[2].append(((grid * [0.8, 0.25, 0.65]) @ rotation.T + helix_center).astype(np.float32))
        states[3].append((0.65 * grid @ rotation.T + 1.15 * center).astype(np.float32))
    return states


class MovingParts3D(ThreeDScene):
    """8 seconds: 96 shaded parts, 96,000 points, three morphs, orbit and zoom."""

    def construct(self):
        states = part_endpoints()
        palette = color_gradient([BLUE, TEAL, GOLD, RED], 96)
        parts = [DotCloud(start, radius=0.022, color=color).make_3d()
                 for start, color in zip(states[0], palette)]
        self.frame.set_height(11).reorient(-35, 65)
        self.add(*parts)
        for phase, (azimuth, elevation, height) in enumerate(
                [(65, 75, 11), (175, 55, 11), (285, 70, 10)], start=1):
            animations = []
            for i, cloud in enumerate(parts):
                delay = (i % 12) / 60

                def easing(t, delay=delay):
                    return smooth(np.clip((t - delay) / (1 - delay), 0, 1))

                animations.append(Transform(
                    cloud, cloud.copy().set_points(states[phase][i]), rate_func=easing,
                ))
            self.play(*animations,
                      self.frame.animate.reorient(azimuth, elevation).set_height(height),
                      run_time=2.6)
        self.wait(0.2)
