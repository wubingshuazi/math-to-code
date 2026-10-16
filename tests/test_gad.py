"""Standard-library regression checks for the GAD capacity calculator.

The phase-pair checks construct the channel from Kraus matrices, independently
of the scalar expression implemented by the runtime package.
"""

import math
import random
import unittest

from math_to_code.gad import binary_entropy, objective, optimize, output_entropy


def _matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(2)) for j in range(2)] for i in range(2)]


def _adjoint(a):
    return [[complex(a[j][i]).conjugate() for j in range(2)] for i in range(2)]


def _output(rho, gamma, nu):
    k = math.sqrt(1.0 - gamma)
    kraus = (
        [[math.sqrt(1.0 - nu), 0.0], [0.0, math.sqrt(1.0 - nu) * k]],
        [[0.0, math.sqrt(gamma * (1.0 - nu))], [0.0, 0.0]],
        [[math.sqrt(nu) * k, 0.0], [0.0, math.sqrt(nu)]],
        [[0.0, 0.0], [math.sqrt(gamma * nu), 0.0]],
    )
    terms = [_matmul(_matmul(operator, rho), _adjoint(operator)) for operator in kraus]
    return [[sum(term[i][j] for term in terms) for j in range(2)] for i in range(2)]


def _entropy(rho):
    # Eigenvalues of a Hermitian 2x2 matrix, using its entries directly.
    trace = (rho[0][0] + rho[1][1]).real
    gap = math.hypot((rho[0][0] - rho[1][1]).real, 2.0 * abs(rho[0][1]))
    eigenvalues = ((trace + gap) / 2.0, (trace - gap) / 2.0)
    return -sum(value * math.log2(value) for value in eigenvalues if value > 0.0)


def _phase_pair_holevo(p, gamma, nu, phase=0.0):
    coherence = math.sqrt(p * (1.0 - p)) * complex(math.cos(phase), math.sin(phase))
    outputs = [
        _output([[1.0 - p, sign * coherence], [sign * coherence.conjugate(), p]], gamma, nu)
        for sign in (1.0, -1.0)
    ]
    average = [[sum(output[i][j] for output in outputs) / 2.0 for j in range(2)] for i in range(2)]
    return _entropy(average) - sum(_entropy(output) for output in outputs) / 2.0


class BinaryEntropyTests(unittest.TestCase):
    def test_exact_endpoints_and_midpoint(self):
        self.assertEqual(binary_entropy(0.0), 0.0)
        self.assertEqual(binary_entropy(1.0), 0.0)
        self.assertEqual(binary_entropy(0.5), 1.0)

    def test_complement_symmetry(self):
        for p in (1e-12, 0.01, 0.2, 0.49999, 0.9):
            self.assertAlmostEqual(binary_entropy(p), binary_entropy(1.0 - p), places=13)

    def test_rejects_invalid_probabilities(self):
        for p in (-0.01, 1.01, math.nan, math.inf, -math.inf):
            with self.subTest(p=p), self.assertRaises(ValueError):
                binary_entropy(p)


class ObjectiveTests(unittest.TestCase):
    def test_pure_output_entropy_matches_kraus_eigenspectrum(self):
        for p in (0.0, 1e-12, 0.2, 0.5, 1.0 - 1e-12, 1.0):
            for gamma, nu in ((0.0, 0.3), (1e-12, 0.0), (0.25, 0.75), (0.7, 0.5), (1.0, 0.2)):
                coherence = math.sqrt(p * (1.0 - p))
                rho = [[1.0 - p, coherence], [coherence, p]]
                expected = _entropy(_output(rho, gamma, nu))
                self.assertAlmostEqual(output_entropy(p, gamma, nu), expected, places=12)

    def test_identity_and_reset_channels(self):
        for p in (0.0, 0.1, 0.5, 0.9, 1.0):
            for nu in (0.0, 0.3, 0.5, 1.0):
                self.assertAlmostEqual(objective(p, 0.0, nu), binary_entropy(p), places=13)
                self.assertAlmostEqual(objective(p, 1.0, nu), 0.0, places=13)

    def test_pure_energy_eigenstate_has_zero_holevo_information(self):
        for gamma in (0.01, 0.4, 0.99):
            for nu in (0.0, 0.25, 0.5, 1.0):
                for p in (0.0, 1.0):
                    self.assertAlmostEqual(objective(p, gamma, nu), 0.0, places=12)

    def test_phase_pair_matches_independent_kraus_calculation(self):
        rng = random.Random(276)
        parameters = [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0.5, 0.5, 0.5)]
        parameters.extend((rng.random(), rng.random(), rng.random()) for _ in range(100))
        for p, gamma, nu in parameters:
            with self.subTest(p=p, gamma=gamma, nu=nu):
                self.assertAlmostEqual(objective(p, gamma, nu), _phase_pair_holevo(p, gamma, nu, rng.random() * math.tau), places=12)

    def test_excitation_relabeling_symmetry(self):
        for p, gamma, nu in ((0.1, 0.2, 0.3), (0.78, 0.9, 0.01), (0.5, 0.6, 1.0)):
            self.assertAlmostEqual(objective(p, gamma, nu), objective(1.0 - p, gamma, 1.0 - nu), places=13)

    def test_rejects_invalid_parameters(self):
        for position in range(3):
            for invalid in (-0.01, 1.01, math.nan, math.inf):
                args = [0.5, 0.3, 0.2]
                args[position] = invalid
                with self.subTest(args=args), self.assertRaises(ValueError):
                    objective(*args)
                with self.subTest(args=args), self.assertRaises(ValueError):
                    output_entropy(*args)


class OptimizerTests(unittest.TestCase):
    def test_identity_capacity(self):
        for nu in (0.0, 0.25, 0.5, 1.0):
            result = optimize(0.0, nu)
            self.assertAlmostEqual(result.capacity_bits, 1.0, places=12)
            self.assertAlmostEqual(result.p, 0.5, places=7)

    def test_reset_capacity(self):
        for nu in (0.0, 0.25, 0.5, 1.0):
            self.assertAlmostEqual(optimize(1.0, nu).capacity_bits, 0.0, places=12)

    def test_unital_closed_form(self):
        for gamma in (0.0, 0.01, 0.2, 0.7, 0.99, 1.0):
            expected = 1.0 - binary_entropy((1.0 + math.sqrt(1.0 - gamma)) / 2.0)
            result = optimize(gamma, 0.5)
            self.assertAlmostEqual(result.capacity_bits, expected, places=12)
            if gamma < 1.0:
                self.assertAlmostEqual(result.p, 0.5, places=6)

    def test_result_and_independent_grid(self):
        for gamma, nu in ((0.05, 0.0), (0.2, 0.3), (0.5, 0.8), (0.9, 1.0), (0.999, 0.1)):
            result = optimize(gamma, nu, tolerance=1e-8)
            self.assertEqual(result.gamma, gamma)
            self.assertEqual(result.nu, nu)
            self.assertGreaterEqual(result.bracket_low, 0.0)
            self.assertLessEqual(result.bracket_high, 1.0)
            self.assertLessEqual(result.bracket_low, result.p)
            self.assertLessEqual(result.p, result.bracket_high)
            self.assertGreater(result.evaluations, 0)
            self.assertAlmostEqual(result.capacity_bits, _phase_pair_holevo(result.p, gamma, nu), places=11)
            grid_best = max(_phase_pair_holevo(i / 1000.0, gamma, nu) for i in range(1001))
            self.assertGreaterEqual(result.capacity_bits + 1e-11, grid_best)
            self.assertLessEqual(result.capacity_bits, 1.0 + 1e-12)
            self.assertGreaterEqual(result.capacity_bits, -1e-12)

    def test_thermal_complement_capacity_symmetry(self):
        for gamma, nu in ((0.1, 0.0), (0.5, 0.2), (0.9, 0.15)):
            left = optimize(gamma, nu)
            right = optimize(gamma, 1.0 - nu)
            self.assertAlmostEqual(left.capacity_bits, right.capacity_bits, places=12)
            # Floating-point plateaus can move the maximizer by a few ulps in
            # the objective; population comparisons use a practical tolerance.
            self.assertAlmostEqual(left.p, 1.0 - right.p, delta=2e-6)

    def test_rejects_invalid_parameters(self):
        for gamma, nu in ((-0.1, 0.5), (1.1, 0.5), (0.5, -0.1), (0.5, 1.1), (math.nan, 0.5), (0.5, math.inf)):
            with self.subTest(gamma=gamma, nu=nu), self.assertRaises(ValueError):
                optimize(gamma, nu)
        for tolerance in (0.0, -1e-4, math.nan, math.inf):
            with self.subTest(tolerance=tolerance), self.assertRaises(ValueError):
                optimize(0.5, 0.5, tolerance=tolerance)


if __name__ == "__main__":
    unittest.main()
