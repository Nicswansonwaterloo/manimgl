"""Render with manimgl tests/operatorname_repro.py OperatorNameRepro -w."""
from manimlib import *


class TexFormattingRepro(Scene):
    def construct(self):
        expressions = [
            r'\mathbf{ffi}+\tau_{\mathsf{red}}',
            r'\phantom{a_{bc}}\alpha,\beta',
            r'\{x\}+\sqrt[3]{y}',
            r'\left.x\right|+\underline{ab}',
        ]
        source = VGroup(*(Tex(tex) for tex in expressions)).arrange(DOWN, buff=0.6)
        target = VGroup(*(Tex(tex + '=z') for tex in expressions)).arrange(DOWN, buff=0.6)
        self.add(source)
        self.wait(0.5)
        self.play(*(TransformMatchingStrings(a, b) for a, b in zip(source, target)))
        self.wait(0.5)


class RomanSubscriptRepro(Scene):
    def construct(self):
        a = Tex(r'\tau_{\mathrm{red}}')
        b = Tex(r'\tau_{\mathrm{red}}=x')
        self.add(a)
        self.wait(0.5)
        self.play(TransformMatchingStrings(a, b))
        self.wait(0.5)


class OperatorNameRepro(Scene):
    def construct(self):
        a = Tex(r'\operatorname{disc}(Q)=b^2-4ac')
        b = Tex(r'\operatorname{disc}(Q)=D=-(b^2-4ac)')
        self.add(a)
        self.wait(0.5)
        self.play(TransformMatchingStrings(a, b))
        self.wait(0.5)


class OperatorNameVariants(Scene):
    def construct(self):
        for operator in [r'\operatorname*{disc}', r'\operatorname{diff}',
                         r'\operatorname{ffi}', r'\operatorname*{office}']:
            a = Tex(operator + r'(Q)=b^2-4ac')
            b = Tex(operator + r'(Q)=D=-(b^2-4ac)')
            self.add(a)
            self.wait(0.5)
            self.play(TransformMatchingStrings(a, b))
            self.wait(0.5)
            self.remove(b)
