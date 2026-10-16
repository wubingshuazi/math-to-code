"""Independent, reproducible matrix audit of the GAD scalar calculator.

Requires NumPy, which is intentionally optional for the runtime package.
Run from any directory with: python scripts/validate_quantum.py
This audit tests numerical consistency. It does not prove the paper's
additivity claim or independently certify its mathematical proof.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from math_to_code.gad import objective, optimize  # noqa: E402


def kraus_operators(gamma: float, nu: float) -> tuple[np.ndarray, ...]:
    """Convention: nu is the stationary excited-state population."""
    k = math.sqrt(1.0 - gamma)
    return (
        math.sqrt(1.0 - nu) * np.diag([1.0, k]).astype(complex),
        np.array([[0.0, math.sqrt(gamma * (1.0 - nu))], [0.0, 0.0]], dtype=complex),
        math.sqrt(nu) * np.diag([k, 1.0]).astype(complex),
        np.array([[0.0, 0.0], [math.sqrt(gamma * nu), 0.0]], dtype=complex),
    )


def entropy_bits(rho: np.ndarray) -> float:
    """Hermitian eigensolver; no determinant/scalar entropy formula used."""
    eigenvalues = np.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    if float(eigenvalues.min()) < -1e-10:
        raise ValueError("Channel output is not positive semidefinite")
    if abs(float(np.trace(rho).real) - 1.0) > 1e-10:
        raise ValueError("Channel output is not trace one")
    positive = eigenvalues[eigenvalues > 0.0]
    return float(-np.sum(positive * np.log2(positive)))


def tensor_channel(rho: np.ndarray, gamma: float, nu: float, n: int) -> np.ndarray:
    """Apply local Kraus maps successively, without a scalar channel shortcut."""
    output = np.asarray(rho, dtype=complex)
    for site in range(n):
        operators = [
            np.kron(np.kron(np.eye(2**site), operator), np.eye(2 ** (n - site - 1)))
            for operator in kraus_operators(gamma, nu)
        ]
        output = sum(operator @ output @ operator.conj().T for operator in operators)
    return output


def pure_density(vector: np.ndarray) -> np.ndarray:
    return np.outer(vector, vector.conj())


def random_pure(rng: np.random.Generator, dimension: int) -> np.ndarray:
    vector = rng.normal(size=dimension) + 1j * rng.normal(size=dimension)
    return vector / np.linalg.norm(vector)


def phase_pair(p: float, phase: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    excited = math.sqrt(p) * np.exp(1j * phase)
    return tuple(np.array([math.sqrt(1.0 - p), sign * excited]) for sign in (1, -1))


def ensemble_holevo(vectors, weights, gamma: float, nu: float, n: int) -> float:
    outputs = [tensor_channel(pure_density(vector), gamma, nu, n) for vector in vectors]
    average = sum(weight * output for weight, output in zip(weights, outputs))
    return entropy_bits(average) - sum(weight * entropy_bits(output) for weight, output in zip(weights, outputs))


def populations(vector: np.ndarray, n: int) -> list[float]:
    probabilities = np.abs(vector.reshape((2,) * n)) ** 2
    return [float(np.take(probabilities, 1, axis=site).sum()) for site in range(n)]


def single_pure_output_entropy(p: float, gamma: float, nu: float) -> float:
    vector = phase_pair(p)[0]
    return entropy_bits(tensor_channel(pure_density(vector), gamma, nu, 1))


def audit(seed: int, samples: int) -> dict:
    rng = np.random.default_rng(seed)
    tolerance = 2e-10
    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "scope": "Numerical consistency audit only; not a proof of additivity, capacity, or correctness of the source paper.",
        "parameter_convention": "nu is stationary excited-state population; all information and entropy values in bits",
        "method": "Four Kraus matrices and Hermitian eigenvalue entropies; no scalar determinant entropy formula in the reference calculation",
        "seed": seed,
        "samples_per_random_check": samples,
        "absolute_tolerance": tolerance,
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "platform": platform.platform()},
        "checks": {},
        "failures": [],
    }

    def check(label, error, allowed=tolerance):
        if error > allowed:
            report["failures"].append({"check": label, "error": float(error), "allowed": allowed})

    parameters = [(g, v) for g in (0.0, 0.2, 0.7, 1.0) for v in (0.0, 0.5, 1.0)]
    parameters += [(float(rng.random()), float(rng.random())) for _ in range(samples)]

    max_trace_error = 0.0
    max_channel_error = 0.0
    max_output_trace_error = 0.0
    min_output_eigenvalue = math.inf
    for gamma, nu in parameters:
        operators = kraus_operators(gamma, nu)
        completeness = sum(operator.conj().T @ operator for operator in operators)
        max_trace_error = max(max_trace_error, float(np.max(np.abs(completeness - np.eye(2)))))
        state = pure_density(random_pure(rng, 2))
        output = tensor_channel(state, gamma, nu, 1)
        max_output_trace_error = max(max_output_trace_error, abs(complex(np.trace(output)) - 1.0))
        min_output_eigenvalue = min(min_output_eigenvalue, float(np.linalg.eigvalsh(output).min()))
        p = float(state[1, 1].real)
        t = (1.0 - gamma) * p + gamma * nu
        direct = np.array([[1.0 - t, math.sqrt(1.0 - gamma) * state[0, 1]], [math.sqrt(1.0 - gamma) * state[1, 0], t]])
        max_channel_error = max(max_channel_error, float(np.max(np.abs(output - direct))))
    report["checks"]["kraus_completeness_and_channel_definition"] = {"cases": len(parameters), "max_completeness_error": max_trace_error, "max_channel_entry_error": max_channel_error, "max_output_trace_error": max_output_trace_error, "minimum_output_eigenvalue": min_output_eigenvalue}
    check("kraus completeness", max_trace_error)
    check("Kraus channel definition", max_channel_error)
    check("channel output trace preservation", max_output_trace_error)
    check("channel output positive semidefiniteness", -min_output_eigenvalue)

    max_pair_error = 0.0
    max_optimum_pair_error = 0.0
    max_grid_excess = 0.0
    for gamma, nu in parameters:
        p = float(rng.random())
        matrix_value = ensemble_holevo(phase_pair(p, float(rng.uniform(0.0, 2.0 * math.pi))), [0.5, 0.5], gamma, nu, 1)
        max_pair_error = max(max_pair_error, abs(matrix_value - objective(p, gamma, nu)))
        optimum = optimize(gamma, nu)
        optimum_matrix = ensemble_holevo(phase_pair(optimum.p), [0.5, 0.5], gamma, nu, 1)
        max_optimum_pair_error = max(max_optimum_pair_error, abs(optimum_matrix - optimum.capacity_bits))
        grid_best = max(ensemble_holevo(phase_pair(float(q)), [0.5, 0.5], gamma, nu, 1) for q in np.linspace(0.0, 1.0, 201))
        max_grid_excess = max(max_grid_excess, grid_best - optimum.capacity_bits)
    report["checks"]["phase_pair_and_optimizer"] = {"cases": len(parameters), "grid_points_per_case": 201, "max_scalar_matrix_error_bits": max_pair_error, "max_optimum_matrix_error_bits": max_optimum_pair_error, "max_grid_excess_bits": max_grid_excess}
    check("phase-pair objective", max_pair_error)
    check("optimized phase-pair objective", max_optimum_pair_error)
    check("independent grid above optimizer", max_grid_excess)

    max_analytic_error = 0.0
    max_symmetry_error = 0.0
    for gamma in (0.0, 0.01, 0.2, 0.5, 0.9, 0.999, 1.0):
        # At nu=1/2, the equatorial output has eigenvalues
        # (1 +/- sqrt(1-gamma))/2; calculate entropy directly.
        equatorial_output = np.array([[0.5, math.sqrt(1.0 - gamma) / 2.0], [math.sqrt(1.0 - gamma) / 2.0, 0.5]])
        expected = 1.0 - entropy_bits(equatorial_output)
        max_analytic_error = max(max_analytic_error, abs(optimize(gamma, 0.5).capacity_bits - expected))
    for gamma, nu in parameters:
        max_symmetry_error = max(max_symmetry_error, abs(optimize(gamma, nu).capacity_bits - optimize(gamma, 1.0 - nu).capacity_bits))
        max_analytic_error = max(max_analytic_error, abs(optimize(0.0, nu).capacity_bits - 1.0), abs(optimize(1.0, nu).capacity_bits))
    report["checks"]["analytic_limits_and_thermal_symmetry"] = {"max_analytic_error_bits": max_analytic_error, "max_complement_capacity_error_bits": max_symmetry_error}
    check("analytic endpoint and unital capacities", max_analytic_error)
    check("thermal complement symmetry", max_symmetry_error)

    min_entropy_slack = math.inf
    max_random_ensemble_excess = 0.0
    max_product_pair_error = 0.0
    block_cases = []
    for n in (2, 3):
        count = 0
        for gamma, nu in parameters:
            optimum = optimize(gamma, nu)
            random_vectors = [random_pure(rng, 2**n) for _ in range(4)]
            # Include maximally entangled/GHZ and a product state, where the
            # latter is an equality case of the population entropy bound.
            ghz = np.zeros(2**n, dtype=complex)
            ghz[0] = ghz[-1] = 1.0 / math.sqrt(2.0)
            local = random_pure(rng, 2)
            product = local
            for _ in range(n - 1):
                product = np.kron(product, local)
            for vector in random_vectors + [ghz, product]:
                lhs = entropy_bits(tensor_channel(pure_density(vector), gamma, nu, n))
                rhs = sum(single_pure_output_entropy(p, gamma, nu) for p in populations(vector, n))
                min_entropy_slack = min(min_entropy_slack, lhs - rhs)
                count += 1
            weights = rng.dirichlet(np.ones(len(random_vectors)))
            random_holevo = ensemble_holevo(random_vectors, weights, gamma, nu, n)
            max_random_ensemble_excess = max(max_random_ensemble_excess, random_holevo - n * optimum.capacity_bits)
            product_signals = [np.array([1.0 + 0.0j])]
            for _ in range(n):
                product_signals = [np.kron(prefix, vector) for prefix in product_signals for vector in phase_pair(optimum.p)]
            product_holevo = ensemble_holevo(product_signals, [1.0 / 2**n] * 2**n, gamma, nu, n)
            max_product_pair_error = max(max_product_pair_error, abs(product_holevo - n * optimum.capacity_bits))
        block_cases.append({"qubits": n, "pure_entropy_bound_cases": count, "random_ensemble_cases": len(parameters), "product_phase_pair_cases": len(parameters)})
    report["checks"]["entangled_blocks_and_ensembles"] = {"cases": block_cases, "minimum_entropy_bound_slack_bits": min_entropy_slack, "max_random_ensemble_above_capacity_bits": max_random_ensemble_excess, "max_product_phase_pair_error_bits": max_product_pair_error, "limitation": "Finite random samples cannot establish any universal inequality or exclude unsampled counterexamples."}
    check("population-preserving entangled-input entropy lower bound", -min_entropy_slack)
    check("random block ensemble above stated capacity", max_random_ensemble_excess)
    check("product phase-pair block attainment", max_product_pair_error)

    report["status"] = "passed" if not report["failures"] else "failed"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=276)
    parser.add_argument("--samples", type=int, default=24, help="Random parameter pairs in addition to 12 boundary/reference pairs")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "results" / "quantum_audit.json")
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("--samples must be positive")
    report = audit(args.seed, args.samples)
    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Numerical consistency audit: {report['status']}; report: {output_path}")
    print("Finite numerical checks are not a proof of additivity or a certification of the source paper.")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
