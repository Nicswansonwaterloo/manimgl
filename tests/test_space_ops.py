import unittest

import numpy as np
from scipy.spatial.transform import Rotation

from manimlib.constants import OUT
from manimlib.utils.space_ops import normalize, rotate_vector, rotation_matrix


class RotationTests(unittest.TestCase):
    def test_matrices_match_general_rotation(self):
        for axis in ([0, 0, 1], [0, 0, -3], [0, 0, 0], [1, -2, 3]):
            for angle in (0, 1e-10, -0.7, np.pi, 10 * np.pi):
                with self.subTest(axis=axis, angle=angle):
                    expected = Rotation.from_rotvec(angle * normalize(axis)).as_matrix()
                    np.testing.assert_allclose(rotation_matrix(angle, axis), expected, atol=1e-14)

    def test_vector_shapes_and_inputs_are_preserved(self):
        vectors = np.random.default_rng(92).normal(size=(7, 3)).astype(np.float32)
        original = vectors.copy()
        for axis in (OUT, [0, 0, -2], [0, 0, 0], [2, 3, -1]):
            matrix = Rotation.from_rotvec(-0.3 * normalize(axis)).as_matrix()
            for vector in (vectors[0], vectors[0].tolist(), vectors, vectors[:0]):
                actual = rotate_vector(vector, -0.3, axis)
                np.testing.assert_allclose(actual, np.dot(vector, matrix.T), atol=1e-14)
                self.assertEqual(actual.shape, np.shape(vector))
        np.testing.assert_array_equal(vectors, original)


def test_rotate_single_2d_vector():
    result = rotate_vector(np.array([1.0, 0.0]), np.pi / 2)

    np.testing.assert_allclose(result, [0.0, 1.0], atol=1e-8)


def test_rotate_batch_of_2d_vectors():
    vectors = np.array([
        [1.0, 0.0],
        [0.0, 1.0],
    ])

    result = rotate_vector(vectors, np.pi / 2)

    np.testing.assert_allclose(result, [[0.0, 1.0], [-1.0, 0.0]], atol=1e-8)


def test_rotate_single_3d_vector():
    result = rotate_vector(np.array([1.0, 0.0, 0.0]), np.pi / 2, OUT)

    np.testing.assert_allclose(result, [0.0, 1.0, 0.0], atol=1e-8)


def test_rotate_batch_of_3d_vectors():
    vectors = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
    ])

    result = rotate_vector(vectors, np.pi / 2, OUT)

    np.testing.assert_allclose(
        result,
        [[0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]],
        atol=1e-8,
    )
