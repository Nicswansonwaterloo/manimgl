"""Check that the shortened workloads retain the source scenes' mathematics."""
import unittest
import numpy as np
from benchmarks.support.personal_math import (
    EDGES, elliptic_multiples, prime_flags, reduced_forms,
    tetra_representatives, tetra_vertices,
)


class PersonalMathTests(unittest.TestCase):
    def test_elliptic_orbit_and_chord_reflection(self):
        points = elliptic_multiples(100)
        x, y = points.T
        np.testing.assert_allclose(y*y, x*x*x-x+1, rtol=1e-12)
        for q, nxt in zip(points[1:], points[2:]):
            # P, Q and -(P+Q) lie on one line.
            reflected = nxt * [1, -1]
            cross = q[0]*(reflected[1]-1) - (q[1]-1)*reflected[0]
            self.assertAlmostEqual(cross / max(1, np.linalg.norm(q)*np.linalg.norm(nxt)), 0)

    def test_reduced_forms_obey_walls_and_prime_classification(self):
        points, prime = reduced_forms(4)
        self.assertEqual(len(points), len(prime))
        self.assertTrue(len(points) > 0)
        self.assertTrue(np.all(points[:, 1:] >= 0))
        self.assertTrue(np.all(points[:, 1:] <= 1))
        np.testing.assert_array_equal(prime_flags([1,2,3,4,17,25]), [False,True,True,False,True,False])

    def test_tetrahedra_realize_edge_lengths_and_converge(self):
        reps = tetra_representatives()
        self.assertEqual(len(set(reps)), len(reps))
        reference = tetra_vertices((0,)*6)
        for lam in reps:
            points = tetra_vertices(lam)
            for (i, j), weight in zip(EDGES, lam):
                self.assertAlmostEqual(np.sum((points[i]-points[j])**2), 1 + weight/8)
            self.assertLessEqual(np.linalg.norm(tetra_vertices(lam, 80)-reference),
                                 np.linalg.norm(points-reference))

    def test_expanded_tetrahedron_clouds_contain_the_original_walk(self):
        original = set(tetra_representatives())
        expanded = set(tetra_representatives(12, walk=False))
        self.assertEqual(len(original), 70)
        self.assertTrue(original < expanded)
        self.assertTrue(all(sum(lam) <= 12 and min(lam) == 0 for lam in expanded))
        for lam in expanded:
            points = tetra_vertices(lam, 17)
            self.assertTrue(np.isfinite(points).all())

    def test_dense_concentration_retains_bounds_and_prime_highlights(self):
        sparse, _ = reduced_forms(17)
        dense, prime = reduced_forms(17, 3)
        self.assertGreater(len(dense), len(sparse))
        self.assertGreater(int(prime.sum()), 0)
        self.assertTrue(np.all(np.abs(dense[:, 0]) <= 2))
        self.assertTrue(np.all((dense[:, 1:] >= 0) & (dense[:, 1:] <= 1)))


if __name__ == '__main__':
    unittest.main()
