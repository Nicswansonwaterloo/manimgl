"""Render with manimgl tests/operatorname_repro.py OperatorNameRepro -w."""
from manimlib import *


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
