"""Reference tests; optional audit libraries are not runtime dependencies."""

from pathlib import Path
from fractions import Fraction
import sys
import unittest

try:
    import mpmath as mp
    import numpy as np
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from thermal_reference import reference_residual, singular_residual
    HAS_AUDIT = True
except ImportError:
    HAS_AUDIT = False


@unittest.skipUnless(HAS_AUDIT, "optional NumPy and mpmath audit dependencies are unavailable")
class ThermalReferenceTests(unittest.TestCase):
    def setUp(self):
        self.x = {"real": [["1", "2", "-1"], ["0", "3", "1"]], "imag": [["0", "1", "2"], ["-2", "1", "0"]]}
        self.y = {"real": [["2", "-1", "0"], ["1", "0", "3"]], "imag": [["1", "0", "-1"], ["2", "1", "-2"]]}
        self.coeff = ("0.4", "0.1", "0.2", "0.3")

    def assertFactorAgreement(self, result):
        self.assertLess(result["reconstruction_max_abs_error"], 1e-12)
        self.assertLess(result["maximum_spectrum_abs_difference"], 1e-12)
        self.assertLess(abs(result["residual_difference_nats"]), 1e-12)
        self.assertGreaterEqual(result["minimum_direct_eigenvalue"], -1e-12)

    def test_generic_complex_rectangle_factor_and_high_precision_agree(self):
        result = singular_residual(self.x, self.y, self.coeff)
        self.assertFactorAgreement(result)
        self.assertEqual(result["factor_branch"], "weighted_source_endpoint_factors")
        reference = reference_residual(self.x, self.y, self.coeff, dps=80)
        self.assertLess(abs(float(reference["residual_nats"]) - result["singular_residual_nats"]), 1e-12)
        self.assertTrue(reference["feasibility"]["accepted"])
        self.assertGreater(float(reference["residual_nats"]), 0.0)
        self.assertGreater(float(reference["pinsker_lower_bound_nats"]), 0.0)
        self.assertGreater(float(reference["pinsker_margin_nats"]), 0.0)

    def test_x_equals_y_saturates_at_80_and_160_digits(self):
        for dps in (80, 160):
            result = reference_residual(self.x, self.x, self.coeff, dps=dps)
            with mp.workdps(dps):
                self.assertLess(abs(mp.mpf(result["residual_nats"])), mp.mpf(10) ** (-(dps - 10)))
                self.assertLess(mp.mpf(result["maximum_trace_error"]), mp.mpf(10) ** (-(dps - 10)))
        result = singular_residual(self.x, self.x, self.coeff)
        self.assertFactorAgreement(result)
        self.assertLess(abs(result["residual_nats"]), 1e-12)

    def test_u_zero_and_vanishing_row_factors(self):
        for coeff, branch in ((("0.25", "0", "0", "0.75"), "u_zero_shared_column_factor"), (("0.25", "0.75", "0", "0"), "vanishing_row_diagonal_factors"), (("0", "0", "0.25", "0.75"), "vanishing_row_diagonal_factors")):
            with self.subTest(coeff=coeff):
                result = singular_residual(self.x, self.y, coeff)
                self.assertFactorAgreement(result)
                self.assertEqual(result["factor_branch"], branch)
                reference = reference_residual(self.x, self.y, coeff)
                self.assertLess(abs(float(reference["residual_nats"]) - result["residual_nats"]), 1e-12)

    def test_rank_deficient_tall_rectangles_pad_singular_spectra(self):
        x = np.array([[1 + 1j], [2 - 1j], [-1 + 2j]])
        y = np.array([[0 + 2j], [1 + 1j], [3 - 1j]])
        result = singular_residual(x, y, self.coeff)
        self.assertFactorAgreement(result)
        self.assertEqual(len(result["factor_full_spectrum"]), 6)
        reference = reference_residual(x, y, self.coeff)
        self.assertLess(abs(float(reference["residual_nats"]) - result["residual_nats"]), 1e-12)

    def test_exact_decimal_direction_is_preserved(self):
        x = {"real": [["1", "0.0000000000000000000000000000000000000001"]], "imag": [["0", "0"]]}
        result = reference_residual(x, x, ("0.5", "0", "0", "0.5"), dps=160)
        # Its norm differs from one at order 1e-80; a binary64 conversion
        # before high precision would lose the distinction completely.
        with mp.workdps(160):
            self.assertGreater(mp.mpf(result["original_hilbert_schmidt_norms"][0]), 1)
            self.assertLess(abs(mp.mpf(result["residual_nats"])), mp.mpf("1e-140"))

    def test_rational_constructions_and_exact_zero_determinant(self):
        x = [[Fraction(1, 3), Fraction(2, 3)]]
        # The reconstructed coefficient determinant is exactly zero. It must
        # stay feasible at both precisions without clipping mp subtraction.
        coeff = ("0.1", "0.2", "0.23333333333333", "0.46666666666666")
        for dps in (80, 160):
            result = reference_residual(x, x, coeff, dps=dps)
            self.assertEqual(result["feasibility"]["exact_rational_determinant"], "0")
            self.assertLess(abs(float(result["residual_nats"])), 1e-70)
        self.assertFactorAgreement(singular_residual(x, x, (Fraction(1, 10), Fraction(1, 5), Fraction(7, 30), Fraction(7, 15))))

    def test_infeasible_coefficients_are_rejected_without_clipping(self):
        for function in (singular_residual, reference_residual):
            with self.subTest(function=function.__name__), self.assertRaises(ValueError):
                function(self.x, self.y, ("0.1", "0.4", "0.4", "0.1"))
            with self.subTest(function=function.__name__), self.assertRaises(ValueError):
                function(self.x, self.y, ("0.4", "0.1", "0.2", "0.4"))
            with self.subTest(function=function.__name__), self.assertRaises(ValueError):
                function([[0]], [[1]], self.coeff)


if __name__ == "__main__":
    unittest.main()
