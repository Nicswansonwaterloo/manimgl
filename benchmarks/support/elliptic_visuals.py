"""Visible real branch and bounded additions for the elliptic-curve scenes."""
from manimlib import *


def elliptic_curve(plane, xmax=2.6):
    root = min(np.roots([1, 0, -1, 1]).real)
    return VGroup(*[
        ParametricCurve(lambda t, sign=sign: plane.c2p(
            root + t*t, sign * np.sqrt(max(0, (root + t*t)**3 - (root + t*t) + 1))),
            t_range=(0, np.sqrt(xmax-root), 0.008), stroke_color=BLUE,
            stroke_width=2.5, stroke_opacity=0.8)
        for sign in (1, -1)
    ])


def visible_additions(coords, count, x_range=(-1.5, 2.6), y_limit=4):
    return [(q, nxt) for q, nxt in zip(coords, coords[1:])
            if all(x_range[0] < p[0] < x_range[1] and abs(p[1]) < y_limit
                   for p in (q, nxt))][:count]
