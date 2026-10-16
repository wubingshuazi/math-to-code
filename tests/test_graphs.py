import math
import unittest

from math_to_code.graphs import GraphSampler, canonical_edges, mixing_steps_bound, realize_degrees


def degrees_of(n, edges):
    degrees = [0] * n
    for u, v in edges:
        degrees[u] += 1
        degrees[v] += 1
    return tuple(degrees)


class GraphTests(unittest.TestCase):
    def test_labeled_realizations_and_rejection(self):
        for degree in ((), (0,), (1, 1), (2, 2, 2), (2,) * 6, (3, 2, 2, 2, 1)):
            self.assertEqual(degrees_of(len(degree), realize_degrees(degree)), degree)
        for degree in ((1,), (1, 1, 1), (3, 3, 0, 0), (True, 1), (-1, 1)):
            with self.assertRaises(ValueError):
                realize_degrees(degree)

    def test_initial_edge_validation(self):
        for edges in (((0, 0),), ((0, 4),), ((0, 1), (1, 0))):
            with self.assertRaises(ValueError):
                canonical_edges(4, edges)
        with self.assertRaises(ValueError):
            GraphSampler((1, 1, 1, 1), edges=((0, 1),))

    def test_both_kernels_preserve_graph_and_seeded_trajectory(self):
        for backend in ("switch", "curveball"):
            first = GraphSampler((2,) * 6, seed=131, backend=backend)
            second = GraphSampler((2,) * 6, seed=131, backend=backend)
            snapshots = set()
            for _ in range(1000):
                self.assertEqual(first.step(), second.step())
                self.assertEqual(first.edges, second.edges)
                self.assertEqual(degrees_of(6, first.edges), (2,) * 6)
                self.assertEqual(len(first.edges), len(set(first.edges)))
                snapshots.add(first.edges)
            self.assertEqual(first.attempts, 1000)
            self.assertLess(first.changes, first.attempts)
            self.assertGreater(len(snapshots), 10)

    def test_sampling_counts_rejected_attempts(self):
        sampler = GraphSampler((0,) * 5, seed=1)
        self.assertEqual(sampler.sample(3, burn_in=7, spacing=11), [(), (), ()])
        self.assertEqual(sampler.attempts, 40)
        self.assertEqual(sampler.changes, 0)
        self.assertEqual(sampler.sample(0, burn_in=100), [])
        self.assertEqual(sampler.attempts, 40)

    def test_curveball_keeps_internal_pair_edge_and_labels(self):
        degree = (4, 3, 3, 2, 2, 2)
        for backend in ("switch", "curveball"):
            sampler = GraphSampler(degree, backend=backend, seed=8)
            for graph in sampler.sample(30, burn_in=30, spacing=5):
                self.assertEqual(degrees_of(6, graph), degree)

    def test_degenerate_graphs(self):
        for backend in ("switch", "curveball"):
            for degree in ((), (0,), (1, 1), (2, 2, 2), (4,) * 5):
                sampler = GraphSampler(degree, backend=backend)
                initial = sampler.edges
                sampler.advance(50)
                self.assertEqual(sampler.edges, initial)

    def test_source_bounds_and_accuracy_monotonicity(self):
        self.assertEqual(mixing_steps_bound(3), 0)
        self.assertEqual(mixing_steps_bound(6, states=1), 0)
        self.assertEqual(mixing_steps_bound(6, backend="curveball"), 128)
        self.assertLess(mixing_steps_bound(6, backend="curveball"), mixing_steps_bound(6, backend="switch"))
        self.assertGreaterEqual(mixing_steps_bound(6, .01), mixing_steps_bound(6, .25))
        for backend in ("switch", "curveball"):
            bound = mixing_steps_bound(6, .25, backend, states=70)
            inverse_gap = 15 if backend == "curveball" else 24 * 36 * math.comb(6, 4)
            self.assertLessEqual(.5 * math.sqrt(70) * math.exp(-bound / inverse_gap), .25)

    def test_invalid_counts_and_bound_inputs(self):
        sampler = GraphSampler((1, 1))
        for count in (-1, 1.5, True):
            with self.assertRaises(ValueError):
                sampler.advance(count)
        with self.assertRaises(ValueError):
            sampler.sample(1, spacing=0)
        for epsilon in (0, -1, .6, math.nan, math.inf):
            with self.assertRaises(ValueError):
                mixing_steps_bound(6, epsilon)


if __name__ == "__main__":
    unittest.main()
