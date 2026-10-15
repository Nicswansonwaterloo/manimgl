"""A bounded number of colored paths instead of one 3D object per segment."""
from manimlib import *
from benchmarks.support.algorithms import hilbert_points


def refinement_knots(dimensions, max_order):
    """Shared traversal parameters, including every corner of every order.

    Identical knots and color boundaries keep Transform from inserting curves
    differently at each refinement (and then snapping to an unaligned target).
    """
    return np.unique(np.concatenate([
        np.linspace(0, 1, (1 << dimensions) ** level)
        for level in range(1, max_order + 1)
    ] + [np.linspace(0, 1, 33)]))


def rainbow_hilbert(order, dimensions, knots=None):
    sites = hilbert_points(order, dimensions)
    points = np.zeros((len(sites), 3))
    points[:, :dimensions] = 5.2 * (sites / ((1 << order) - 1) - 0.5)
    if knots is None:
        knots = refinement_knots(dimensions, order)
    parameters = np.linspace(0, 1, len(points))
    points = np.column_stack([np.interp(knots, parameters, points[:, axis]) for axis in range(3)])
    bounds = np.searchsorted(knots, np.linspace(0, 1, 33))
    colors = color_gradient([PURPLE, PINK, BLUE, TEAL, YELLOW, GREEN, GOLD], 32)
    paths = VGroup(*[
        VMobject(stroke_color=color, stroke_width=max(1.3, 4.5 - 0.7 * order))
        .set_points_as_corners(points[a:b + 1]).set_flat_stroke(dimensions == 2)
        for a, b, color in zip(bounds[:-1], bounds[1:], colors)
    ])
    if dimensions == 3:
        paths.apply_depth_test()
    return paths, points
