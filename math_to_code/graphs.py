"""Degree-preserving graph sampling with proposal-time Markov clocks.

The switch kernel follows OpenAI math family 131. Curveball is the pair
heat-bath kernel used in its proof. Vertices are labeled 0,...,n-1.
"""

import math
from numbers import Integral
import random


def _integer(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return int(value)


def canonical_edges(n, edges):
    """Validate a simple undirected labeled graph; reject duplicate edges."""
    n = _integer(n, "n")
    result = set()
    for edge in edges:
        try:
            u, v = edge
        except (TypeError, ValueError) as exc:
            raise ValueError("each edge must contain exactly two endpoints") from exc
        u, v = _integer(u, "endpoint"), _integer(v, "endpoint")
        if u >= n or v >= n or u == v:
            raise ValueError("endpoints must be distinct vertex labels in range")
        pair = (min(u, v), max(u, v))
        if pair in result:
            raise ValueError("duplicate undirected edge")
        result.add(pair)
    return tuple(sorted(result))


def realize_degrees(degrees):
    """Deterministic Havel-Hakimi realization, preserving the given labels."""
    degree = tuple(_integer(value, "degree") for value in degrees)
    n = len(degree)
    if any(value >= n for value in degree) or sum(degree) % 2:
        raise ValueError("degree vector is not graphical")
    remaining = [(value, vertex) for vertex, value in enumerate(degree)]
    edges = []
    while remaining:
        remaining.sort(key=lambda item: (-item[0], item[1]))
        count, vertex = remaining.pop(0)
        if count == 0:
            break
        if count > len(remaining) or any(remaining[i][0] == 0 for i in range(count)):
            raise ValueError("degree vector is not graphical")
        for i in range(count):
            residual, neighbor = remaining[i]
            remaining[i] = (residual - 1, neighbor)
            edges.append((min(vertex, neighbor), max(vertex, neighbor)))
    return tuple(sorted(edges))


def mixing_steps_bound(n, epsilon=0.25, backend="curveball", states=None):
    """Conservative source-derived TV bound, measured in attempted steps.

    Uses integer upper bounds on the two logarithms, avoiding rounding a
    large mathematical bound down. `states`, when known exactly, can replace
    the general bound |Omega| <= 2**binom(n,2). Source derivation is in docs.
    """
    n = _integer(n, "n")
    if backend not in ("switch", "curveball"):
        raise ValueError("backend must be 'switch' or 'curveball'")
    try:
        epsilon = float(epsilon)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("epsilon must be finite and in (0, 0.5]") from exc
    if not math.isfinite(epsilon) or not 0 < epsilon <= .5:
        raise ValueError("epsilon must be finite and in (0, 0.5]")
    pairs = n * (n - 1) // 2
    exponent = pairs
    if states is not None:
        states = _integer(states, "states", 1)
        exponent = (states - 1).bit_length()
        if exponent > pairs:
            raise ValueError("state count exceeds the number of labeled simple graphs")
        if states == 1:
            return 0
    if n < 4:
        if states is not None and states > 1:
            raise ValueError("a graphical labeled degree vector on <=3 vertices has one realization")
        return 0  # Every graphical labeled vector on <=3 vertices is unique.
    numerator, denominator = epsilon.as_integer_ratio()
    k = max(0, denominator.bit_length() - numerator.bit_length())
    if (numerator << k) < denominator:
        k += 1
    inverse_gap = pairs if backend == "curveball" else 24 * n * n * math.comb(n, 4)
    # eps >= 2^-k, |Omega| <= 2^exponent and ln(2) < 1.
    return (inverse_gap * (exponent + 2 * k - 2) + 1) // 2


class GraphSampler:
    """A Markov chain on ALL simple labeled realizations of a degree vector.

    Each step includes holds/rejections. `sample` performs burn_in steps,
    then spacing steps BEFORE each returned graph, including the first.
    Connectivity is allowed to change. The initial graph is deterministic
    unless supplied explicitly; reproducibility includes the backend/seed.
    """

    def __init__(self, degrees, seed=0, backend="switch", edges=None):
        self.degrees = tuple(_integer(value, "degree") for value in degrees)
        initial = realize_degrees(self.degrees)
        self.n = len(self.degrees)
        if backend not in ("switch", "curveball"):
            raise ValueError("backend must be 'switch' or 'curveball'")
        if edges is not None:
            initial = canonical_edges(self.n, edges)
            observed = [0] * self.n
            for u, v in initial:
                observed[u] += 1
                observed[v] += 1
            if tuple(observed) != self.degrees:
                raise ValueError("initial edges do not realize the requested labeled degrees")
        self.backend, self.seed = backend, seed
        self._random = random.Random(seed)
        self._edges = set(initial)
        self._neighbors = [set() for _ in range(self.n)]
        for u, v in initial:
            self._neighbors[u].add(v)
            self._neighbors[v].add(u)
        self.attempts, self.changes = 0, 0

    @property
    def edges(self):
        return tuple(sorted(self._edges))

    def _remove(self, u, v):
        self._edges.remove((min(u, v), max(u, v)))
        self._neighbors[u].remove(v)
        self._neighbors[v].remove(u)

    def _add(self, u, v):
        self._edges.add((min(u, v), max(u, v)))
        self._neighbors[u].add(v)
        self._neighbors[v].add(u)

    def _switch(self):
        if self.n < 4 or not self._random.getrandbits(1):
            return False
        a, b, c, d = sorted(self._random.sample(range(self.n), 4))
        matchings = (((a, b), (c, d)), ((a, c), (b, d)), ((a, d), (b, c)))
        first = self._random.randrange(3)
        second = self._random.randrange(2)
        second += second >= first
        old, new = matchings[first], matchings[second]
        if not all(edge in self._edges for edge in old) or any(edge in self._edges for edge in new):
            return False
        for edge in old:
            self._remove(*edge)
        for edge in new:
            self._add(*edge)
        return True

    def _curveball(self):
        if self.n < 2:
            return False
        u, v = sorted(self._random.sample(range(self.n), 2))
        only_u = self._neighbors[u].difference(self._neighbors[v], {v})
        only_v = self._neighbors[v].difference(self._neighbors[u], {u})
        pool = sorted(only_u | only_v)
        new_u = set(self._random.sample(pool, len(only_u)))
        if new_u == only_u:
            return False
        new_v = set(pool) - new_u
        # Keep the u-v edge and common neighbors unchanged.
        for w in only_u:
            self._remove(u, w)
        for w in only_v:
            self._remove(v, w)
        for w in new_u:
            self._add(u, w)
        for w in new_v:
            self._add(v, w)
        return True

    def step(self):
        self.attempts += 1
        changed = self._switch() if self.backend == "switch" else self._curveball()
        self.changes += int(changed)
        return changed

    def advance(self, steps):
        steps = _integer(steps, "steps")
        previous = self.changes
        for _ in range(steps):
            self.step()
        return self.changes - previous

    def sample(self, count, burn_in=0, spacing=1):
        count, burn_in = _integer(count, "count"), _integer(burn_in, "burn_in")
        spacing = _integer(spacing, "spacing", 1)
        if not count:
            return []
        self.advance(burn_in)
        result = []
        for _ in range(count):
            self.advance(spacing)
            result.append(self.edges)
        return result

    def statistics(self):
        return {"vertices": self.n, "edges": len(self._edges), "backend": self.backend,
                "seed": self.seed, "attempted_steps": self.attempts,
                "changed_steps": self.changes,
                "change_rate": self.changes / self.attempts if self.attempts else 0.0,
                "clock": "all attempted steps, including holds and rejections"}
