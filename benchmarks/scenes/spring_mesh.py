from manimlib import *


class SpringMesh(Scene):
    """224 nodes and 418 connecting lines updated as one deforming elastic sheet."""
    default_camera_config = dict(background_color="#092B32")

    def construct(self):
        rows, cols = 14, 16
        homes = np.array([[(c / (cols - 1) - 0.5) * 9.35, (r / (rows - 1) - 0.5) * 5.25, 0]
                          for r in range(rows) for c in range(cols)])
        edges = [(r * cols + c, r * cols + c + 1) for r in range(rows) for c in range(cols - 1)]
        edges += [(r * cols + c, (r + 1) * cols + c) for r in range(rows - 1) for c in range(cols)]
        nodes = VGroup(*[Dot(p, radius=0.04, color=GOLD) for p in homes])
        springs = VGroup(*[Line(homes[a], homes[b], stroke_width=1.5, color=TEAL) for a, b in edges])

        def deform(_):
            positions = homes.copy()
            distance = np.linalg.norm(homes[:, :2], axis=1)
            positions[:, 1] += 0.5 * np.sin(2 * distance - 4 * self.time)
            positions[:, 0] += 0.2 * np.cos(homes[:, 1] + 3 * self.time)
            for node, point in zip(nodes, positions):
                node.move_to(point)
            for spring, (a, b) in zip(springs, edges):
                spring.put_start_and_end_on(positions[a], positions[b])

        controller = Mobject().add_updater(deform)
        self.add(springs, nodes, controller)
        self.wait(4)
