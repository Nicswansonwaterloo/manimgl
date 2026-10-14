import unittest

import numpy as np
from colour import Color

from manimlib.utils.color import color_to_rgb, hex_to_rgb


class ColorConversionTests(unittest.TestCase):
    def test_mutated_color_uses_current_values(self):
        color = Color(rgb=(0.2, 0.3, 0.4))
        color_to_rgb(color)
        color.set_rgb((0.9, 0.1, 0.5))
        np.testing.assert_allclose(color_to_rgb(color), [0.9, 0.1, 0.5])
        color.set_hsl((0.5, 0.7, 0.3))
        np.testing.assert_array_equal(color_to_rgb(color), color.get_rgb())

    def test_returned_arrays_are_independent(self):
        for convert, color in [(hex_to_rgb, "#abc"), (color_to_rgb, "#abc"),
                               (color_to_rgb, Color("#abc"))]:
            with self.subTest(convert=convert, color=color):
                expected = convert(color).copy()
                convert(color)[:] = -1
                np.testing.assert_array_equal(convert(color), expected)

    def test_subclass_can_override_rgb_conversion(self):
        class CustomColor(Color):
            def get_rgb(self):
                return (0.1, 0.2, 0.3)

        np.testing.assert_array_equal(color_to_rgb(CustomColor()), [0.1, 0.2, 0.3])


if __name__ == "__main__":
    unittest.main()
