"""Independent small-state reference tests, with optional NumPy dependency."""

from fractions import Fraction
from pathlib import Path
import sys
import unittest

try:
    import numpy as np
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from audit_graphs import enumerate_realizations, switch_kernel, curveball_kernel, exact_checks, mixing_trajectory, scripted_core_row, jump_chain_audit
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


@unittest.skipUnless(HAS_NUMPY, "optional NumPy audit dependency is unavailable")
class GraphReferenceTests(unittest.TestCase):
    def test_independent_labeled_enumeration_counts(self):
        for degrees, count in (((1,) * 4, 3), ((2,) * 6, 70), ((1,) * 6, 15), ((2,) * 5, 12), ((0,) * 5, 1), ((4,) * 5, 1), ((3, 1, 1, 1), 1), ((), 1)):
            with self.subTest(degrees=degrees):
                states = enumerate_realizations(degrees)
                self.assertEqual(len(states), count)
                self.assertEqual(len(set(states)), count)
                for state in states:
                    observed = [0] * len(degrees)
                    for u, v in state:
                        observed[u] += 1
                        observed[v] += 1
                    self.assertEqual(tuple(observed), degrees)
        self.assertEqual(enumerate_realizations((3, 3, 0, 0)), [])

    def test_four_vertex_closed_form_matrices_and_clock(self):
        degrees = (1,) * 4
        states = enumerate_realizations(degrees)
        for backend, builder, off, diagonal, expected_time, eigen in (("switch", switch_kernel, Fraction(1, 12), Fraction(5, 6), 4, .75), ("curveball", curveball_kernel, Fraction(1, 6), Fraction(2, 3), 2, .5)):
            matrix = builder(4, states)
            self.assertTrue(all(exact_checks(matrix).values()))
            for row in range(3):
                for col in range(3):
                    self.assertEqual(matrix[row][col], diagonal if row == col else off)
            trajectory = mixing_trajectory(matrix)
            self.assertEqual(trajectory["mixing_steps"], expected_time)
            for item in trajectory["trajectory"]:
                self.assertAlmostEqual(item["worst_tv"], (2 / 3) * eigen ** item["step"], places=13)
            for index, state in enumerate(states):
                expected = {target: matrix[index][j] for j, target in enumerate(states) if matrix[index][j]}
                self.assertEqual(scripted_core_row(degrees, state, backend), expected)

    def test_six_vertex_exact_jump_bias(self):
        states = enumerate_realizations((2,) * 6)
        switch = switch_kernel(6, states)
        result = jump_chain_audit(states, switch)
        self.assertTrue(result["expected_identities_hold"])
        self.assertTrue(result["jump_detailed_balance_exactly"])
        self.assertEqual(result["uniform_two_triangles_probability"]["fraction"], "1/7")
        self.assertEqual(result["jump_two_triangles_probability"]["fraction"], "1/5")
        self.assertEqual(result["uniform_expected_triangles"]["fraction"], "2/7")
        self.assertEqual(result["jump_expected_triangles"]["fraction"], "2/5")

    def test_nontrivial_reference_kernels_and_production_steps(self):
        for degrees in ((2,) * 6, (3, 2, 2, 2, 1)):
            states = enumerate_realizations(degrees)
            for backend, builder in (("switch", switch_kernel), ("curveball", curveball_kernel)):
                matrix = builder(len(degrees), states)
                self.assertTrue(all(exact_checks(matrix).values()))
                self.assertGreaterEqual(mixing_trajectory(matrix)["minimum_eigenvalue"], -1e-12)
                for index in (0, len(states) - 1):
                    expected = {state: matrix[index][j] for j, state in enumerate(states) if matrix[index][j]}
                    self.assertEqual(scripted_core_row(degrees, states[index], backend), expected)

    def test_unique_graphs_include_all_holding_probability(self):
        for degrees in ((), (1, 1), (2, 2, 2), (0,) * 5, (4,) * 5, (3, 1, 1, 1)):
            states = enumerate_realizations(degrees)
            for builder in (switch_kernel, curveball_kernel):
                matrix = builder(len(degrees), states)
                self.assertEqual(matrix, [[Fraction(1)]])
                self.assertEqual(mixing_trajectory(matrix)["mixing_steps"], 0)


if __name__ == "__main__":
    unittest.main()
