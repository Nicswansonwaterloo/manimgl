"""Numerical helpers for long workloads; no Manim imports or extra dependencies."""
from collections import deque

import numpy as np


def breadth_first_events(adjacency, start):
    """Return actual FIFO pops, discovery events and post-pop queue snapshots."""
    parents = np.full(len(adjacency), -1, dtype=int)
    distances = np.full(len(adjacency), -1, dtype=int)
    distances[start] = 0
    queue = deque([start])
    events = []
    while queue:
        node = queue.popleft()
        discovered = []
        for neighbor in adjacency[node]:
            if distances[neighbor] < 0:
                parents[neighbor] = node
                distances[neighbor] = distances[node] + 1
                queue.append(neighbor)
                discovered.append(neighbor)
        events.append((node, discovered, tuple(queue)))
    return events, parents, distances


def hilbert_points_3d(order):
    """Vectorized Skilling transpose/Gray decode, returning integer lattice sites.

    Algorithm background and original public-domain construction:
    https://github.com/galtay/hilbertcurve#references
    """
    return hilbert_points(order, 3)


def hilbert_points_2d(order):
    return hilbert_points(order, 2)


def hilbert_points(order, dimensions):
    """Integer Hilbert lattice sites in 2D or 3D, with adjacent parent cells."""
    if order < 1 or dimensions not in (2, 3):
        raise ValueError("Positive order and two or three dimensions required")
    distances = np.arange(1 << (dimensions * order), dtype=np.int64)
    points = np.zeros((len(distances), dimensions), dtype=np.int64)
    for bit in range(order):
        for axis in range(dimensions):
            points[:, axis] |= ((distances >> (dimensions * bit + dimensions - 1 - axis)) & 1) << bit
    gray_carry = points[:, -1] >> 1
    for axis in range(dimensions - 1, 0, -1):
        points[:, axis] ^= points[:, axis - 1]
    points[:, 0] ^= gray_carry
    for bit in range(1, order):
        mask = (1 << bit) - 1
        for axis in reversed(range(dimensions)):
            invert = (points[:, axis] & (1 << bit)) != 0
            exchange = (points[:, 0] ^ points[:, axis]) & mask
            exchange[invert] = 0
            points[:, 0] ^= exchange
            points[:, axis] ^= exchange
            points[invert, 0] ^= mask
    return points


def softened_acceleration(positions, masses, gravity=0.15, softening=0.08, block=128):
    """Direct all-pairs gravity with bounded temporary storage, not a tree approximation."""
    acceleration = np.zeros_like(positions)
    for start in range(0, len(positions), block):
        delta = positions[None, :, :] - positions[start:start + block, None, :]
        radius2 = np.einsum("ijk,ijk->ij", delta, delta) + softening**2
        weights = masses[None, :] * radius2**-1.5
        acceleration[start:start + block] = gravity * np.einsum("ij,ijk->ik", weights, delta)
    return acceleration


def gray_scott_step(a, b, feed=0.035, kill=0.062):
    """One explicit unit-time Gray–Scott step with periodic boundary conditions."""
    def laplacian(field):
        return (np.roll(field, 1, 0) + np.roll(field, -1, 0)
                + np.roll(field, 1, 1) + np.roll(field, -1, 1) - 4 * field)

    reaction = a * b * b
    next_a = a + 0.16 * laplacian(a) - reaction + feed * (1 - a)
    next_b = b + 0.08 * laplacian(b) + reaction - (kill + feed) * b
    return np.clip(next_a, 0, 1), np.clip(next_b, 0, 1)
