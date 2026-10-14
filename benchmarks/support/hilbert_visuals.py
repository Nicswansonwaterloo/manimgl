"""A bounded number of colored paths instead of one 3D object per segment."""
from manimlib import *
from benchmarks.support.algorithms import hilbert_points


def rainbow_hilbert(order, dimensions):
    sites = hilbert_points(order, dimensions)
    points = np.zeros((len(sites), 3))
    points[:, :dimensions] = 5.2 * (sites / ((1 << order) - 1) - 0.5)
    knots = np.unique(np.r_[np.arange(len(points)), np.linspace(0, len(points) - 1, 65)])
    points = np.column_stack([np.interp(knots, np.arange(len(points)), points[:, axis]) for axis in range(3)])
    bounds = np.linspace(0, len(points) - 1, 33, dtype=int)
    colors = color_gradient([PURPLE, PINK, BLUE, TEAL, YELLOW, GREEN, GOLD], 32)
    paths = VGroup(*[
        VMobject(stroke_color=color, stroke_width=max(1.3, 4.5 - 0.7 * order))
        .set_points_as_corners(points[a:b + 1]).set_flat_stroke(dimensions == 2)
        for a, b, color in zip(bounds[:-1], bounds[1:], colors)
    ])
    return paths, points
