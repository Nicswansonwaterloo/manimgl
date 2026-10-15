import unittest

import numpy as np

from manimlib.utils.paths import path_along_arc


class ArcPathTests(unittest.TestCase):
    def test_3d_arc_reaches_both_endpoints_for_arbitrary_axes(self):
        rng = np.random.default_rng(12)
        start, end = rng.normal(size=(2, 20, 3))
        for axis in ([0, 0, 1], [1, 2, -3], [0, 0, 0]):
            for angle in (np.pi/6, -np.pi/2, np.pi, (0.1, 1.2)):
                path = path_along_arc(angle, axis=np.array(axis))
                np.testing.assert_allclose(path(start, end, 0), start, atol=1e-12)
                np.testing.assert_allclose(path(start, end, 1), end, atol=1e-12)

    def test_motion_along_axis_is_linear_throughout_arc(self):
        axis = np.array([1, 2, 3]) / np.sqrt(14)
        start = np.array([[1., -2., 3.], [-1., 4., 1.]])
        end = np.array([[3., 2., -4.], [5., -2., 2.]])
        path = path_along_arc(np.pi/3, axis)
        for alpha in np.linspace(0, 1, 11):
            actual = path(start, end, alpha) @ axis
            expected = ((1-alpha)*start + alpha*end) @ axis
            np.testing.assert_allclose(actual, expected, atol=1e-12)

    def test_pure_axial_motion_stays_straight_and_stationary_points_stay_put(self):
        start = np.array([[1., 2., 3.]])
        path = path_along_arc(np.pi/2)
        for alpha in np.linspace(0, 1, 11):
            np.testing.assert_allclose(path(start, start, alpha), start)
            np.testing.assert_allclose(path(start, start+[0, 0, 4], alpha), start+[0, 0, 4*alpha])

    def test_single_point_retains_its_shape(self):
        start, end = np.array([1., 2., 3.]), np.array([2., -1., 5.])
        path = path_along_arc(np.pi/4)
        self.assertEqual(path(start, end, 0.5).shape, (3,))
        np.testing.assert_allclose(path(start, end, 1), end)
