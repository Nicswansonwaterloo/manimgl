import unittest

import numpy as np

from manimlib.utils.structured_array import StructuredArray


class FieldLookupTests(unittest.TestCase):
    def test_update_ignores_padding_and_unknown_fields(self):
        data = StructuredArray(np.dtype([("value", "f4"), ("_pad", "f4")]), 2)
        data.update({"value": 3, "_pad": 9, "unknown": 5})
        np.testing.assert_array_equal(data["value"], [3, 3])
        np.testing.assert_array_equal(data["_pad"], [0, 0])
        self.assertEqual(tuple(data), ("value",))

    def test_update_between_different_layouts_copies_common_fields(self):
        source = StructuredArray(np.dtype([("a", "f4"), ("b", "f4")]), 2)
        target = StructuredArray(np.dtype([("b", "f4"), ("c", "f4")]), 2)
        source.update(a=1, b=2)
        target.update(c=3)
        target.update(source)
        np.testing.assert_array_equal(target["b"], [2, 2])
        np.testing.assert_array_equal(target["c"], [3, 3])


if __name__ == "__main__":
    unittest.main()
