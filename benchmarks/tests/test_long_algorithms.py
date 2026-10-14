"""Algorithm invariants: these workloads should show real computations."""
import unittest

import numpy as np

from benchmarks.support.algorithms import (
    breadth_first_events, gray_scott_step, hilbert_points_3d, hilbert_points_2d, softened_acceleration,
)


class LongAlgorithmTests(unittest.TestCase):
    def test_2d_hilbert_is_continuous_unique_and_refines_parent_cells(self):
        for order in range(1, 6):
            points = hilbert_points_2d(order)
            self.assertEqual(points.shape, (4**order, 2))
            self.assertEqual(len(np.unique(points, axis=0)), len(points))
            np.testing.assert_array_equal(np.abs(np.diff(points, axis=0)).sum(axis=1), 1)
            if order > 1:
                parents = (points // 2).reshape(-1, 4, 2)
                np.testing.assert_array_equal(parents[:, 0], hilbert_points_2d(order - 1))
                np.testing.assert_array_equal(parents, np.repeat(parents[:, :1], 4, axis=1))

    def test_bfs_uses_fifo_and_shortest_distances(self):
        graph = [[1, 2], [0, 3], [0, 3, 4], [1, 2, 5], [2, 5], [3, 4]]
        events, parents, distance = breadth_first_events(graph, 0)
        self.assertEqual([event[0] for event in events], [0, 1, 2, 3, 4, 5])
        np.testing.assert_array_equal(distance, [0, 1, 1, 2, 2, 3])
        self.assertEqual(events[0][2], (1, 2))
        for vertex in range(1, len(graph)):
            self.assertIn(parents[vertex], graph[vertex])
            self.assertEqual(distance[parents[vertex]] + 1, distance[vertex])

    def test_hilbert_visits_each_voxel_once_with_face_adjacent_steps(self):
        for order in range(1, 7):
            points = hilbert_points_3d(order)
            self.assertEqual(points.shape, (8**order, 3))
            self.assertEqual(len(np.unique(points, axis=0)), len(points))
            self.assertEqual(points.min(), 0)
            self.assertEqual(points.max(), 2**order - 1)
            np.testing.assert_array_equal(np.abs(np.diff(points, axis=0)).sum(axis=1), 1)
            if order > 1:
                parents = (points // 2).reshape(-1, 8, 3)
                np.testing.assert_array_equal(parents[:, 0], hilbert_points_3d(order - 1))
                np.testing.assert_array_equal(parents, np.repeat(parents[:, :1], 8, axis=1))

    def test_gravity_preserves_force_symmetry_and_handles_coincident_points(self):
        positions = np.array([[-1.0, 0, 0], [1.0, 0, 0], [1.0, 0, 0]])
        masses = np.array([2.0, 3.0, 4.0])
        acceleration = softened_acceleration(positions, masses, block=2)
        self.assertTrue(np.isfinite(acceleration).all())
        self.assertGreater(acceleration[0, 0], 0)
        self.assertLess(acceleration[1, 0], 0)
        np.testing.assert_allclose((acceleration * masses[:, None]).sum(axis=0), 0, atol=1e-12)

    def test_reaction_diffusion_equilibrium_and_evolution(self):
        a, b = np.ones((20, 24)), np.zeros((20, 24))
        next_a, next_b = gray_scott_step(a, b)
        np.testing.assert_array_equal(next_a, a)
        np.testing.assert_array_equal(next_b, b)
        a[7:13, 9:15], b[7:13, 9:15] = 0.5, 0.25
        initial_b = b.copy()
        for _ in range(200):
            a, b = gray_scott_step(a, b)
        self.assertTrue(np.isfinite(a).all() and np.isfinite(b).all())
        self.assertTrue((a >= 0).all() and (a <= 1).all())
        self.assertTrue((b >= 0).all() and (b <= 1).all())
        self.assertFalse(np.allclose(b, initial_b))


if __name__ == "__main__":
    unittest.main()
