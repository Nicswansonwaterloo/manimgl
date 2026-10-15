import unittest

import numpy as np

from manimlib.utils.structured_array import StructuredArray


class FieldLookupTests(unittest.TestCase):
    def test_update_only_accepts_visible_field_names(self):
        data = StructuredArray(np.dtype([
            (("alias", "value"), "f4"),
            (("padding_alias", "_pad"), "f4"),
        ]), 2)
        data.update({"value": 3, "_pad": 9, "unknown": 5,
                     "alias": 7, "padding_alias": 8})
        np.testing.assert_array_equal(data["value"], [3, 3])
        np.testing.assert_array_equal(data["_pad"], [0, 0])
        self.assertEqual(tuple(data), ("value",))


if __name__ == "__main__":
    unittest.main()
