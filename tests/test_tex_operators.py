"""Operator glyph counts and matching, checked against actual LaTeX output."""
import unittest
from unittest.mock import patch

from manimlib import Tex, TransformMatchingStrings
from manimlib.utils.tex import num_tex_symbols


class TexOperatorTests(unittest.TestCase):
    def test_counts_match_rendered_paths(self):
        for name, count in [('disc', 4), ('diff', 3), ('ff', 1), ('fi', 1),
                            ('fl', 1), ('ffi', 1), ('ffl', 1), ('office', 4)]:
            for star in ['', '*']:
                with self.subTest(name=name, star=star):
                    tex = rf'\operatorname{star}{{{name}}}(Q)=b^2-4ac'
                    mob = Tex(tex)
                    self.assertEqual(num_tex_symbols(tex), count + 10)
                    self.assertEqual(num_tex_symbols(tex), len(mob))
                    self.assertEqual(sum(map(num_tex_symbols, mob.get_symbol_substrings())), len(mob))
        self.assertEqual(num_tex_symbols('ffi*'), 4)
        self.assertEqual(len(Tex('ffi')), 3)
        self.assertEqual(num_tex_symbols(r'\operatorname'), 0)
        self.assertEqual(num_tex_symbols(r'\operatorname*'), 0)
        self.assertEqual(num_tex_symbols(r'\operatornameExtra'), 1)

    def test_matching_preserves_operator_and_polynomial(self):
        for operator in [r'\operatorname{disc}', r'\operatorname*{disc}',
                         r'\operatorname{diff}', r'\operatorname{ffi}', r'\operatorname*{office}']:
            with self.subTest(operator=operator), patch('manimlib.mobject.svg.tex_mobject.log.warning') as warn:
                source = Tex(operator + r'(Q)=b^2-4ac')
                target = Tex(operator + r'(Q)=D=-(b^2-4ac)')
                blocks = TransformMatchingStrings.matching_blocks(None, source, target, [], {})
                blocks.sort(key=lambda pair: list(source).index(pair[0][0]))
                n = num_tex_symbols(operator) + 4
                self.assertEqual(list(blocks[0][0]), list(source[:n]))
                self.assertEqual(list(blocks[0][1]), list(target[:n]))
                self.assertEqual(list(blocks[1][0]), list(source[n:]))
                self.assertEqual(list(blocks[1][1]), list(target[n + 4:-1]))
                self.assertEqual(list(source['b^2'][0]), list(source[n:n + 2]))
                TransformMatchingStrings(source, target)
                warn.assert_not_called()

    def test_explicit_matches_use_glyph_offsets(self):
        source = Tex(r'\operatorname{office}(x)+y')
        target = Tex(r'\operatorname{office}(x)+z')
        blocks = TransformMatchingStrings.matching_blocks(None, source, target, ['x'], {})
        for side in [0, 1]:
            paths = [id(path) for block in blocks for path in block[side]]
            self.assertEqual(len(paths), len(set(paths)))


if __name__ == '__main__':
    unittest.main()
