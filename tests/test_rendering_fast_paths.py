import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

from manimlib.mobject.geometry import Line, Square
from manimlib.mobject.mobject import Mobject
from manimlib.mobject.types.vectorized_mobject import VGroup
from manimlib.renderer.drawing import VDrawing
from manimlib.renderer.renderer import Bundling


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


class StrokeVisibilityTests(unittest.TestCase):
    def drawing(self, mob, cls=VDrawing):
        material = SimpleNamespace(
            data_buffer=Mock(claim=Mock(return_value=0)),
            uniform_buffer=Mock(claim=Mock(return_value=0)),
            record_size=mob.data.dtype.itemsize,
        )
        drawing = cls(material, mob)
        drawing.draw_pass = Mock()
        return drawing

    def prepare(self, leader):
        for drawing in leader.members or [leader]:
            drawing.write_uniforms()
        leader.write_records()

    def modules(self, drawing):
        drawing.draw_pass.reset_mock()
        drawing.draw_passes(None)
        return [call.args[1] for call in drawing.draw_pass.call_args_list]

    def test_invisible_stroke_keeps_all_fill_passes(self):
        for behind in (False, True):
            drawing = self.drawing(Square().set_fill(opacity=1).set_stroke(width=0, behind=behind))
            self.prepare(drawing)
            self.assertEqual(self.modules(drawing), ["fill", "border", "fill"])

    def test_width_and_opacity_each_hide_strokes(self):
        for kwargs in ({"width": 0}, {"opacity": 0}):
            drawing = self.drawing(Line().set_stroke(**kwargs))
            self.prepare(drawing)
            self.assertEqual(self.modules(drawing), [])

    def test_interpolated_visibility_is_conservative(self):
        line = Line().set_stroke(width=[2, 0, 0], opacity=[0, 0, 1])
        drawing = self.drawing(line)
        self.prepare(drawing)
        self.assertEqual(self.modules(drawing), ["stroke"])

    def test_unchanged_data_does_not_rescan(self):
        drawing = self.drawing(Line().set_stroke(width=0))
        self.prepare(drawing)
        with patch("manimlib.renderer.drawing.np.any", side_effect=AssertionError("rescan")):
            self.prepare(drawing)
        drawing.mobject.set_stroke(width=3)
        self.prepare(drawing)
        self.assertTrue(drawing.has_stroke)

    def test_merged_visibility_and_bundle_transitions(self):
        first = self.drawing(Line().set_stroke(width=0))
        second = self.drawing(Line().set_stroke(opacity=0))
        first.members = [first, second]
        bundling = Bundling()

        def frame():
            self.prepare(first)
            if first.invalidated:
                bundling.invalidate()
            bundle = bundling.take(lambda: tuple(self.modules(first)))
            return tuple(self.modules(first)) if bundle is None else bundle

        for _ in range(4):
            self.assertEqual(frame(), ())
        self.assertIsNotNone(bundling.bundle)
        second.mobject.set_stroke(opacity=1)
        self.assertEqual(frame(), ("stroke",))
        self.assertIsNone(bundling.bundle)
        for _ in range(3):
            self.assertEqual(frame(), ("stroke",))
        second.mobject.set_stroke(opacity=0)
        self.assertEqual(frame(), ())
        self.assertIsNone(bundling.bundle)

    def test_leader_own_cache_survives_regrouping(self):
        hidden = self.drawing(Line().set_stroke(width=0))
        visible = self.drawing(Line())
        hidden.members = [hidden, visible]
        self.prepare(hidden)
        self.assertTrue(hidden.has_stroke)
        hidden.members = None
        self.prepare(hidden)
        self.assertFalse(hidden.has_stroke)
        self.assertTrue(hidden.invalidated)

    def test_array_interpolation_refreshes_visibility(self):
        line = Line().set_stroke(opacity=0)
        source = line.copy()
        target = line.copy().set_stroke(opacity=1)
        drawing = self.drawing(line)
        self.prepare(drawing)
        line.data.interpolate(source.data, target.data, 0.5)
        self.prepare(drawing)
        self.assertTrue(drawing.has_stroke)
        self.assertTrue(drawing.invalidated)

    def test_custom_shaders_keep_existing_draw(self):
        custom = Line().set_stroke(width=0)
        custom.shader_code_replacements = {"some code": "custom code"}

        class CustomDrawing(VDrawing):
            pass

        for drawing in (self.drawing(custom), self.drawing(Line().set_stroke(width=0), CustomDrawing)):
            self.prepare(drawing)
            self.assertEqual(self.modules(drawing), ["stroke"])


if __name__ == "__main__":
    unittest.main()
