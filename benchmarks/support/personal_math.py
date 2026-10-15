"""Small deterministic numerical counterparts of the supplied Sage scenes."""
from decimal import Decimal, localcontext
from itertools import combinations, permutations
from math import isqrt
import numpy as np


def elliptic_multiples(count):
    """Real coordinates of k*(0,1) on y²=x³-x+1; high precision avoids pole drift."""
    with localcontext() as ctx:
        ctx.prec = 80
        x, y = Decimal(0), Decimal(1)
        points = []
        for k in range(count):
            points.append((float(x), float(y)))
            slope = -Decimal(1) / 2 if k == 0 else (y - 1) / x
            nx = slope * slope - x
            x, y = nx, -1 - slope * nx
    return np.array(points)


def prime_flags(values):
    limit = max(values, default=1)
    sieve = np.ones(limit + 1, dtype=bool)
    sieve[:2] = False
    for p in range(2, isqrt(limit) + 1):
        if sieve[p]:
            sieve[p * p::p] = False
    return sieve[np.asarray(values, dtype=int)]


def reduced_forms(n, e=1):
    """Same reduction walls and discriminant cutoff as TernaryQFConvergence."""
    points, discs = [], []
    a = 0
    while n * (n + a)**2 < (n + e)**3:
        b = a
        while n * (n + a) * (n + b) < (n + e)**3:
            for x in range(-n - a, n + a + 1):
                for y in range(n + 1):
                    for z in range(n + 1):
                        if y + z - x > 2 * n + a:
                            continue
                        disc = (4*n*(n+a)*(n+b) + x*y*z
                                - n*x*x - (n+a)*y*y - (n+b)*z*z)
                        if 0 < disc < 2 * (n + e)**3:
                            points.append((x/n, y/n, z/n))
                            discs.append(disc)
            b += 1
        a += 1
    return np.array(points).reshape(-1, 3), prime_flags(discs)


EDGES = list(combinations(range(4), 2))


def tetra_representatives(max_weight=6, walk=True):
    """Weight 1..max_weight representatives modulo vertex permutations.

    The animated walk uses nearest-first ordering. Dense destination clouds
    only need a deterministic enumeration, avoiding a quadratic path search.
    """
    maps = [[EDGES.index(tuple(sorted((p[i], p[j])))) for i, j in EDGES]
            for p in permutations(range(4))]

    def compositions(total, size):
        if size == 1:
            yield (total,)
        else:
            for k in range(total + 1):
                for tail in compositions(total - k, size - 1):
                    yield (k,) + tail

    result, previous = [], (0,) * 6
    for weight in range(1, max_weight + 1):
        remaining = {min(tuple(lam[i] for i in m) for m in maps)
                     for lam in compositions(weight, 6) if 0 in lam}
        if not walk:
            result.extend(sorted(remaining))
            continue
        while remaining:
            lam = min(remaining, key=lambda v: (
                sum(abs(a-b) for a, b in zip(v, previous)),
                sum((a-b)**2 for a, b in zip(v, previous)), v))
            result.append(lam)
            remaining.remove(lam)
            previous = lam
    return result


def tetra_vertices(lam, n=8):
    a, b, c = (n + lam[i] for i in range(3))
    r, s, t = (n+lam[1]+lam[2]-lam[5], n+lam[0]+lam[2]-lam[4],
               n+lam[0]+lam[1]-lam[3])
    gram = np.array([[a, t/2, s/2], [t/2, b, r/2], [s/2, r/2, c]])
    return np.vstack((np.zeros(3), np.linalg.cholesky(gram) / np.sqrt(n)))
