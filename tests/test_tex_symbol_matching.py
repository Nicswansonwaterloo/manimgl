"""Compare estimated matching offsets with actual LaTeX-generated paths."""
import unittest
from unittest.mock import patch

from manimlib import Tex, TransformMatchingStrings
from manimlib.utils.tex import num_tex_symbols, get_tex_symbol_substrings


class TexSymbolMatchingTests(unittest.TestCase):
    def test_font_groups_and_ligatures(self):
        for command in ['mathrm', 'mathbf', 'mathit', 'mathsf', 'mathtt',
                        'mathnormal', 'mathfrak', 'boldsymbol', 'text',
                        'textrm', 'textbf', 'textit', 'textsf', 'texttt']:
            for word in ['red', 'ffi']:
                with self.subTest(command=command, word=word):
                    self.check_expression(rf'\{command}{{{word}}}+x')

    def test_syntax_and_invisible_content(self):
        for tex in [
            r'\phantom{a_{bc}}+x', r'\hphantom{\frac{a}{b}}+x',
            r'\vphantom{abc}+x', r'\sqrt[3]{x}+y', r'\{x\}+y',
            r'\alpha,\beta', r'a\!\,b', r'a\ b', r'\left.x\right|+y',
            r'\underline{ab}+x', r'\overline{ab}+x',
            r'\frac{ab}{cd}+x', r'\hat{ab}+x',
            r'\mathop{abc}\limits_{x}+y', r'\mathbin{ab}+x',
            r'\mathrm{a\mathtt{ffi}b}+x', r'\mathbf x+y',
            r'\begin{aligned}a&=b\\c&=d\end{aligned}',
        ]:
            with self.subTest(tex=tex):
                self.check_expression(tex)

    def test_decorations_are_not_split_into_wrong_svg_offsets(self):
        for tex in [r'\underline{ab}', r'\frac{ab}{cd}', r'\sqrt[3]{ab}', r'\hat{ab}']:
            with self.subTest(tex=tex):
                self.assertEqual(get_tex_symbol_substrings(tex), [tex])

    def check_expression(self, tex):
        with patch('manimlib.mobject.svg.tex_mobject.log.warning') as warn:
            source = Tex(tex)
            target = Tex(tex + '=z')
            self.assertEqual(num_tex_symbols(tex), len(source))
            self.assertEqual(sum(map(num_tex_symbols, get_tex_symbol_substrings(tex))), len(source))
            self.assertEqual(list(target['z'][0]), list(target[-1:]))
            blocks = TransformMatchingStrings.matching_blocks(None, source, target, [], {})
            self.assertEqual(list(blocks[0][0]), list(source))
            self.assertEqual(list(blocks[0][1]), list(target[:-2]))
            TransformMatchingStrings(source, target)
            warn.assert_not_called()

    def test_custom_macro_falls_back_without_inventing_offsets(self):
        with patch('manimlib.mobject.svg.tex_mobject.log.warning') as warn:
            source = Tex(r'\custom', additional_preamble=r'\newcommand{\custom}{ab}')
            target = Tex(r'\custom', additional_preamble=r'\newcommand{\custom}{xyz}')
            self.assertEqual((len(source), len(target)), (2, 3))
            self.assertEqual(source.get_symbol_substrings(), [source.string])
            blocks = TransformMatchingStrings.matching_blocks(None, source, target, [], {})
            self.assertEqual(list(blocks[0][0]), list(source))
            self.assertEqual(list(blocks[0][1]), list(target))
            animation = TransformMatchingStrings(source, target)
            self.assertFalse(animation.source_pieces)
            self.assertFalse(animation.target_pieces)
            warn.assert_not_called()

    def test_font_dependent_ligatures_use_fallback(self):
        # The basic template enables text ligatures, unlike the default.
        source = Tex(r'\text{office}', template='basic')
        self.assertEqual(len(source), 4)
        self.assertEqual(source.get_symbol_substrings(), [source.string])
        self.assertEqual(source.substr_to_path_count(source.string), 4)


if __name__ == '__main__':
    unittest.main()
