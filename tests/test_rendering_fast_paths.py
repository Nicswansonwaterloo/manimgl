import itertools
import unittest
from unittest.mock import patch

import numpy as np

from manimlib.mobject.geometry import Line, Square
from manimlib.mobject.mobject import Mobject
from manimlib.mobject.types.vectorized_mobject import VGroup, VMobject


class BoundingBoxPointTests(unittest.TestCase):
    def test_directions_select_the_same_corners_and_edges(self):
        mob = VGroup(Square().shift([2, -3, 1]), Square().shift([-4, 1, -2]))
        box = mob.get_bounding_box().copy()
        for direction in itertools.product((-2, 0, 3), repeat=3):
            indices = (np.sign(direction) + 1).astype(int)
            expected = np.array([box[indices[i], i] for i in range(3)])
            for value in (direction, list(direction), np.array(direction, dtype=np.float32)):
                actual = mob.get_bounding_box_point(value)
                np.testing.assert_array_equal(actual, expected)
                actual[:] = 123
                np.testing.assert_array_equal(mob.get_bounding_box(), box)


class AffineBoundsTests(unittest.TestCase):
    def test_ordered_transforms_match_corner_reordering(self):
        shift = np.array([0.3, -0.7, 1.2])
        factors = np.array([0.4, 2.0, 1.5])
        about = np.array([1.0, -2.0, 0.5])
        cases = [
            (lambda m: m.shift(shift), lambda p: p + shift, dict(about_edge=None)),
            (lambda m: m.scale(factors), lambda p: factors * p, {}),
            (lambda m: m.scale(0, min_scale_factor=0), lambda p: 0 * p, {}),
            (lambda m: m.scale(2, about_point=about), lambda p: 2 * p, dict(about_point=about)),
            (lambda m: m.stretch(0.2, 1), lambda p: p * [1, 0.2, 1], {}),
        ]
        for transform, function, kwargs in cases:
            with self.subTest(transform=transform):
                actual = VGroup(VGroup(Square().set_fill(["#ff0000", "#0000ff"])),
                                Square().shift([3, 1, 0]))
                reference = actual.copy()
                parent, reference_parent = VGroup(actual), VGroup(reference)
                parent.get_bounding_box()
                reference_parent.get_bounding_box()
                transform(actual)
                reference.apply_points_function(function, works_on_bounding_box=True, **kwargs)
                self.assertTrue(parent._needs_new_bounding_box)
                for mob, expected in zip(actual.get_family(), reference.get_family()):
                    np.testing.assert_array_equal(mob.data.array, expected.data.array)
                    np.testing.assert_array_equal(mob.uniforms.array, expected.uniforms.array)
                    np.testing.assert_array_equal(mob.get_bounding_box(), expected.get_bounding_box())
                np.testing.assert_array_equal(parent.get_bounding_box(), reference_parent.get_bounding_box())

    def test_negative_factors_keep_bounds_ordered(self):
        transforms = [
            lambda m: m.stretch(-2, 0),
            lambda m: m.scale(-2, min_scale_factor=-3, about_point=np.array([1, 2, 3])),
            lambda m: m.scale([-2, 0, 3], min_scale_factor=-3),
        ]
        for transform in transforms:
            with self.subTest(transform=transform):
                square = Square().shift([1, 2, 3])
                parent = VGroup(square)
                parent.get_bounding_box()
                transform(square)
                points = square.get_points()
                low, high = points.min(0), points.max(0)
                expected = np.array([low, (low + high) / 2, high])
                np.testing.assert_allclose(square.get_bounding_box(), expected)
                np.testing.assert_allclose(parent.get_bounding_box(), expected)


class ShortPathNormalTests(unittest.TestCase):
    def test_short_paths_have_zero_anchor_area_and_keep_their_normal(self):
        cases = [
            ([], [0, 0, 1]),
            ([[1, 2, 3]], [0, 0, 1]),
            ([[-1, 0, 0], [0, 0, 0], [1, 0, 0]], [0, 0, 1]),
            ([[0, 0, -1], [0, 0, 0], [0, 0, 1]], [0, -1, 0]),
            ([[-1, 0, 0], [0, 1, 0], [1, 0, 0]], [0, 0, -1]),
            ([[0, 0, 0], [1, 0, 0], [1, 1, 1]], [0, -2**-0.5, 2**-0.5]),
            ([[2, 2, 2]] * 3, [0, -1, 0]),
        ]
        for points, normal in cases:
            with self.subTest(points=points):
                path = VMobject().set_points(np.array(points).reshape((-1, 3)))
                np.testing.assert_array_equal(path.get_area_vector(), np.zeros(3))
                np.testing.assert_allclose(path.get_unit_normal(refresh=True), normal)

    def test_polygon_area_still_determines_the_normal(self):
        path = VMobject().set_points_as_corners([[0, 0, 0], [2, 0, 0], [0, 3, 0], [0, 0, 0]])
        np.testing.assert_allclose(path.get_area_vector(), [0, 0, 3])
        np.testing.assert_allclose(path.get_unit_normal(refresh=True), [0, 0, 1])


class FillColorTests(unittest.TestCase):
    def test_partial_updates_preserve_other_components(self):
        square = Square().set_fill(["#ff0000", "#0000ff"], [0.2, 0.8])
        version = square.uniforms.version
        square.set_fill(opacity=0.5)
        np.testing.assert_allclose(square.uniforms["fill_rgba"], [1, 0, 0, 0.5])
        np.testing.assert_allclose(square.uniforms["fill_rgba_end"], [0, 0, 1, 0.5])
        self.assertGreater(square.uniforms.version, version)
        square.set_fill("#00ff00")
        for name in ("fill_rgba", "fill_rgba_end"):
            np.testing.assert_allclose(square.uniforms[name], [0, 1, 0, 0.5])

    def test_family_updates_keep_individual_opacities(self):
        squares = VGroup(Square().set_fill(opacity=0.2), Square().set_fill(opacity=0.8))
        squares.set_fill(["#ff0000", "#0000ff", "#00ff00"])
        for square, opacity in zip(squares, [0.2, 0.8]):
            np.testing.assert_allclose(square.uniforms["fill_rgba"], [1, 0, 0, opacity])
            np.testing.assert_allclose(square.uniforms["fill_rgba_end"], [0, 0, 1, opacity])
        squares.set_fill("#00ff00", recurse=False)
        np.testing.assert_allclose(squares[0].uniforms["fill_rgba"][:3], [1, 0, 0])

    def test_gradient_points_follow_explicit_direction(self):
        square = Square().set_fill("#ffffff", [0.1, 0.9, 0.4], gradient_direction=[0, 1, 0])
        np.testing.assert_allclose(square.uniforms["gradient_start"], [0, -1, 0])
        np.testing.assert_allclose(square.uniforms["gradient_end"], [0, 1, 0])
        self.assertAlmostEqual(float(square.uniforms["fill_rgba"][3]), 0.1)
        self.assertAlmostEqual(float(square.uniforms["fill_rgba_end"][3]), 0.9)

    def test_solid_fill_replaces_gradient_and_honors_explicit_direction(self):
        for color, opacity in [("#00ff00", 0.4), ("#00ff00", np.float32(0.4)),
                               (["#00ff00"], [0.4])]:
            with self.subTest(color=color, opacity=opacity):
                square = Square().set_fill(["#ff0000", "#0000ff"], [0.2, 0.8],
                                           gradient_direction=[0, 1, 0])
                square.set_fill(color, opacity)
                for key in ("fill_rgba", "fill_rgba_end"):
                    np.testing.assert_allclose(square.uniforms[key], [0, 1, 0, 0.4])
                square.set_fill(color, opacity, gradient_direction=[1, 0, 0])
                np.testing.assert_allclose(square.uniforms["gradient_start"], [-1, 0, 0])
                np.testing.assert_allclose(square.uniforms["gradient_end"], [1, 0, 0])


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
