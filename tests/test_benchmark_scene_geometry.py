"""Geometry regressions that do not need a graphics adapter."""
import unittest

import numpy as np

from manimlib import ReplacementTransform
from benchmarks.support.algorithms import hilbert_points
from benchmarks.support.hilbert_visuals import rainbow_hilbert, refinement_knots
from benchmarks.support.elliptic_visuals import visible_additions
from benchmarks.support.personal_math import elliptic_multiples


class BenchmarkSceneGeometryTests(unittest.TestCase):
    def test_hilbert_refinement_keeps_every_corner_and_shared_path_topology(self):
        for dimensions, max_order in ((2, 5), (3, 4)):
            knots = refinement_knots(dimensions, max_order)
            topology = None
            for order in range(1, max_order+1):
                paths, sampled = rainbow_hilbert(order, dimensions, knots)
                sites = hilbert_points(order, dimensions)
                parameters = np.linspace(0, 1, len(sites))
                expected = 5.2 * (sites / ((1 << order)-1) - 0.5)
                np.testing.assert_allclose(sampled[np.searchsorted(knots, parameters), :dimensions], expected)
                self.assertEqual(len(paths), 32)
                counts = [len(path.get_points()) for path in paths]
                if topology is not None:
                    self.assertEqual(counts, topology)
                topology = counts
                for first, second in zip(paths, paths[1:]):
                    np.testing.assert_array_equal(first.get_end(), second.get_start())

    def test_hilbert_transform_does_not_realign_or_snap_at_completion(self):
        for dimensions, max_order in ((2, 5), (3, 4)):
            knots = refinement_knots(dimensions, max_order)
            for order in range(1, max_order):
                source, _ = rainbow_hilbert(order, dimensions, knots)
                target, _ = rainbow_hilbert(order+1, dimensions, knots)
                before = [path.get_points().copy() for path in target]
                transform = ReplacementTransform(source, target, path_arc=np.pi/6)
                transform.begin()
                transform.interpolate(1)
                for path, expected in zip(source, before):
                    np.testing.assert_allclose(path.get_points(), expected, atol=1e-6)
                for path, expected in zip(target, before):
                    np.testing.assert_array_equal(path.get_points(), expected)

    def test_elliptic_chords_and_reflections_stay_in_the_visible_window(self):
        steps = visible_additions(elliptic_multiples(1200), 10)
        self.assertEqual(len(steps), 10)
        for q, nxt in steps:
            for x, y in (q, nxt, nxt * [1, -1]):
                self.assertTrue(-1.5 < x < 2.6 and abs(y) < 4)
                self.assertAlmostEqual(y*y, x*x*x-x+1, places=9)


if __name__ == '__main__':
    unittest.main()
