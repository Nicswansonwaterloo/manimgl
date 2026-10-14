import unittest
from unittest.mock import patch

import numpy as np

from manimlib.mobject.geometry import Line, Square
from manimlib.mobject.mobject import Mobject
from manimlib.mobject.types.vectorized_mobject import VGroup


class LineEndpointTests(unittest.TestCase):
    def test_endpoints_style_and_parent_bounds(self):
        line = Line().set_stroke(width=[1, 4, 2], opacity=[0.2, 0.5, 0.8])
        parent = VGroup(line)
        style = line.data.array.copy()
        targets = [
            ([3, 2, 0], [-2, -1, 0]),
            ([1, -3, 2], [4, 2, -1]),
            ([0, 0, 2], [0, 0, -2]),
            ([2, 2, 2], [2, 2, 2]),
            ([-1, 1, 0], [3, 1, 0]),
        ]
        for start, end in targets:
            with self.subTest(start=start, end=end):
                parent.get_bounding_box()
                version = line.data.version
                with patch.object(Mobject, "put_start_and_end_on", side_effect=AssertionError("fallback")):
                    self.assertIs(line.put_start_and_end_on(start, end), line)
                expected = np.array([start, 0.5 * (np.array(start) + end), end])
                np.testing.assert_allclose(line.get_points(), expected)
                self.assertGreater(line.data.version, version)
                np.testing.assert_allclose(parent.get_bounding_box()[[0, 2]],
                                           [expected.min(0), expected.max(0)])
                for field in ("stroke_width", "stroke_rgba", "subpath_range"):
                    np.testing.assert_array_equal(line.data[field], style[field])
                self.assertTrue(np.isfinite(line.uniforms["unit_normal"]).all())
                direction = expected[2] - expected[0]
                self.assertAlmostEqual(float(np.dot(line.uniforms["unit_normal"], direction)),
                                       0, places=5)

    def test_endpoints_can_alias_existing_points(self):
        line = Line([1, 2, 3], [4, 5, 6])
        expected = line.get_points()[::-1].copy()
        line.put_start_and_end_on(line.get_end(), line.get_start())
        np.testing.assert_array_equal(line.get_points(), expected)

    def test_new_null_line_can_grow(self):
        line = Line(np.zeros(3), np.zeros(3))
        line.put_start_and_end_on(np.zeros(3), np.array([1, 2, 3]))
        np.testing.assert_array_equal(line.get_end(), [1, 2, 3])
        np.testing.assert_array_equal(line.data["subpath_range"], [[0, 2], [1, 1], [2, 0]])

    def test_matches_general_transform_in_plane(self):
        line = Line([-2, 1, 0], [3, -1, 0])
        reference = line.copy()
        for start, end in [([0.3, -1.2, 0], [-2.7, 0.8, 0]),
                           ([1.1, 0.2, 0], [2.6, -2.3, 0])]:
            start, end = np.array(start), np.array(end)
            Mobject.put_start_and_end_on(reference, start, end)
            line.put_start_and_end_on(start, end)
            np.testing.assert_allclose(line.get_points(), reference.get_points(), atol=2e-6)
            np.testing.assert_allclose(line.uniforms["unit_normal"], reference.uniforms["unit_normal"])

    def test_unsupported_lines_use_general_transform(self):
        class SpecialLine(Line):
            pass

        non_midpoint = Line()
        non_midpoint.data["point"] = [[-1, 0, 0], [0.2, 0, 0], [1, 0, 0]]
        bent = Line()
        bent.data["point"] = [[-1, 0, 0], [0, 0.01, 0], [1, 0, 0]]
        candidates = [
            Line(path_arc=0.5), Line().insert_n_curves(3),
            Line().add_tip(), Line().add(Square()),
            Line().set_fill(["#ff0000", "#0000ff"], opacity=1),
            SpecialLine(), non_midpoint, bent,
        ]
        for line in candidates:
            with self.subTest(line=line), patch.object(Mobject, "put_start_and_end_on", return_value=line) as fallback:
                line.put_start_and_end_on(np.zeros(3), np.ones(3))
                fallback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
