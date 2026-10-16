"""Analytic cases and hypothesis checks for the scalar stability bound."""

import math
import unittest

from math_to_code.thermal import gap_lower_bound


class ThermalBoundTests(unittest.TestCase):
    def test_equal_grams_and_zero_rows(self):
        self.assertEqual(gap_lower_bound((0.4, 0.1, 0.15, 0.35), 0), 0)
        self.assertEqual(gap_lower_bound((0, 0, 0.3, 0.7), 1), 0)
        self.assertEqual(gap_lower_bound((0.3, 0.7, 0, 0), 1), 0)

    def test_independent_classical_binary_mixture_case(self):
        # alpha=beta=eta=delta=1/4 gives K=0. Orthogonal pure Grams
        # have distance 2, and the exact entropy gap is ln(2).
        bound = gap_lower_bound((0.25, 0.25, 0.25, 0.25), 2)
        self.assertAlmostEqual(bound, 0.5)
        self.assertLess(bound, math.log(2))

    def test_thermal_phase_exchange_symmetry(self):
        self.assertAlmostEqual(gap_lower_bound((0.4, .1, .15, .35), .7),
                               gap_lower_bound((.35, .15, .1, .4), .7))

    def test_quadratic_scaling_in_gram_distance(self):
        coefficient = (0.4, .1, .15, .35)
        self.assertAlmostEqual(gap_lower_bound(coefficient, .6),
                               4 * gap_lower_bound(coefficient, .3))

    def test_invalid_hypotheses_rejected(self):
        cases = [((1, 0, 0), 0), ((.1, .4, .4, .1), .5),
                 ((-.1, .2, .3, .6), .5), ((.2, .2, .2, .2), .5),
                 ((.4, .1, .15, .35), -1), ((.4, .1, .15, .35), 2.01),
                 ((math.nan, .1, .1, .8), 1), ((.4, .1, .15, .35), math.inf)]
        for coefficient, distance in cases:
            with self.subTest(coefficient=coefficient, distance=distance):
                with self.assertRaises(ValueError):
                    gap_lower_bound(coefficient, distance)

    def test_small_row_infeasibility_is_not_accepted_as_roundoff(self):
        with self.assertRaises(ValueError):
            gap_lower_bound((0, 1e-15, .5, .5 - 1e-15), 1)

    def test_subnormal_valid_row_does_not_underflow_bound(self):
        tiny = float.fromhex("0x0.0000000000001p-1022")
        self.assertEqual(gap_lower_bound((tiny, tiny, .5, .5), 2), .5)


if __name__ == "__main__":
    unittest.main()
