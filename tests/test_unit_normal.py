import unittest

import numpy as np

from manimlib.utils.space_ops import get_unit_normal


class UnitNormalTests(unittest.TestCase):
    def test_general_vectors_match_normalized_cross_product(self):
        rng = np.random.default_rng(2048)
        pairs = rng.normal(size=(8, 2, 3))
        for dtype in [np.float32, np.float64]:
            for first, second in pairs.astype(dtype):
                expected = np.cross(first.astype(float), second.astype(float))
                expected /= np.linalg.norm(expected)
                np.testing.assert_allclose(get_unit_normal(first, second), expected, atol=1e-12)

    def test_parallel_zero_and_vertical_fallbacks(self):
        for first, second, expected in [
            ([1, 0, 0], [2, 0, 0], [0, 0, 1]),
            ([1, 0, 0], [-2, 0, 0], [0, 0, 1]),
            ([1, 0, 1], [2, 0, 2], np.array([-1, 0, 1]) / np.sqrt(2)),
            ([0, 0, 1], [0, 0, 2], [0, -1, 0]),
            ([0, 0, 0], [1, 0, 0], [0, -1, 0]),
            ([1, 0, 0], [0, 0, 0], [0, 0, 1]),
        ]:
            with self.subTest(first=first, second=second):
                np.testing.assert_allclose(get_unit_normal(first, second), expected, atol=1e-12)

    def test_tolerance_is_independent_of_vector_length(self):
        for scale in [1e-100, 1, 1e100]:
            for angle, expected in [(-0.5e-6, [0, 0, 1]), (-2e-6, [0, 0, -1])]:
                first = np.array([scale, 0, 0])
                second = scale * np.array([np.cos(angle), np.sin(angle), 0])
                np.testing.assert_array_equal(get_unit_normal(first, second), expected)
        np.testing.assert_array_equal(get_unit_normal([1, 0, 0], [1, -1e-4, 0], tol=1e-3), [0, 0, 1])


if __name__ == "__main__":
    unittest.main()
