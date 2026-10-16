"""Check the thermal gap API against matrix entropies and exact families.

The matrix calculation and scalar reference cases are independent of the
gap_lower_bound implementation. All entropy quantities are in nats.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from math_to_code.thermal import gap_lower_bound  # noqa: E402

PIN = "1581d4cbdd69a0faf34b2089614fe2a814316a6a"
THERMAL_SOURCE_HASH = "52a3470b411125ba69e7f39cc78c611695c895059288e212e3c5407a69882d14"
TOLERANCE = 2e-10
STATE_TOLERANCE = 2e-12
SHAPES = ((2, 2), (2, 3), (3, 2), (3, 3))


def normalize(matrix: np.ndarray) -> np.ndarray:
    return matrix / np.linalg.norm(matrix, axis=(-2, -1), keepdims=True)


def random_complex(rng: np.random.Generator, shape: tuple) -> np.ndarray:
    return rng.standard_normal(shape) + 1j * rng.standard_normal(shape)


def unitary(rng: np.random.Generator, dimension: int) -> np.ndarray:
    q, _ = np.linalg.qr(random_complex(rng, (dimension, dimension)))
    return q


def binary_entropy(p: float) -> float:
    return sum(-value * math.log(value) for value in (p, 1.0 - p) if value > 0.0)


def entropy_from_eigenvalues(values: np.ndarray) -> np.ndarray:
    # Negativity is checked independently before these rounding-level values
    # are ignored. No density matrix is renormalized during evaluation.
    positive = np.maximum(values, 0.0)
    return -np.sum(positive * np.log(np.maximum(positive, np.finfo(float).tiny)), axis=-1)


def evaluate(x: np.ndarray, y: np.ndarray, coefficients: np.ndarray) -> dict:
    """Vectorized direct matrix calculation; leading axis indexes cases."""
    adj = lambda matrix: matrix.conj().swapaxes(-1, -2)
    a, b, eta, d = coefficients.T
    determinant = a * d - b * eta
    k = np.sqrt(np.maximum(determinant, 0.0))
    u = (a + b) * (eta + d) - k * k
    xx, yy, xy = x @ adj(x), y @ adj(y), x @ adj(y)
    top = np.concatenate((a[:, None, None] * xx + b[:, None, None] * yy, k[:, None, None] * xy), axis=-1)
    bottom = np.concatenate((k[:, None, None] * adj(xy), eta[:, None, None] * xx + d[:, None, None] * yy), axis=-1)
    full = np.concatenate((top, bottom), axis=-2)
    eig_x = np.linalg.eigvalsh(xx)
    eig_y = np.linalg.eigvalsh(yy)
    eig_full = np.linalg.eigvalsh(full)
    trace_errors = np.maximum.reduce([
        np.abs(np.trace(matrix, axis1=-2, axis2=-1) - 1.0) for matrix in (xx, yy, full)
    ])
    hermitian_errors = np.maximum.reduce([
        np.max(np.abs(matrix - adj(matrix)), axis=(-2, -1)) for matrix in (xx, yy, full)
    ])
    minimum_eigenvalues = np.minimum.reduce([eig_x[:, 0], eig_y[:, 0], eig_full[:, 0]])
    if np.any(np.min(coefficients, axis=1) < 0.0) or np.any(np.abs(coefficients.sum(axis=1) - 1.0) > STATE_TOLERANCE):
        raise ValueError("invalid coefficient normalization or sign")
    if np.any(determinant < -STATE_TOLERANCE) or np.any(u < -STATE_TOLERANCE) or np.any(u > 0.25 + STATE_TOLERANCE):
        raise ValueError("invalid coefficient determinant or scalar entropy parameter")
    if np.any(trace_errors > STATE_TOLERANCE) or np.any(hermitian_errors > STATE_TOLERANCE) or np.any(minimum_eigenvalues < -STATE_TOLERANCE):
        raise ValueError("matrix trace, Hermiticity, or positivity check failed")
    # This uses the two scalar eigenvalues, separate from the public gap API.
    small = 2.0 * np.maximum(u, 0.0) / (1.0 + np.sqrt(np.maximum(1.0 - 4.0 * u, 0.0)))
    scalar_entropy = entropy_from_eigenvalues(np.stack((small, 1.0 - small), axis=-1))
    residual = entropy_from_eigenvalues(eig_full) - (a + eta) * entropy_from_eigenvalues(eig_x) - (b + d) * entropy_from_eigenvalues(eig_y) - scalar_entropy
    trace_norm = np.sum(np.abs(np.linalg.eigvalsh(xx - yy)), axis=-1)
    bound = np.array([gap_lower_bound(coeff, distance) for coeff, distance in zip(coefficients, trace_norm)])
    commutator = np.linalg.norm(xx @ yy - yy @ xx, axis=(-2, -1))
    return {
        "residual_nats": residual,
        "gram_trace_norm": trace_norm,
        "lower_bound_nats": bound,
        "margin_nats": residual - bound,
        "trace_error": trace_errors,
        "hermitian_error": hermitian_errors,
        "minimum_eigenvalue": minimum_eigenvalues,
        "gram_commutator_norm": commutator,
        "K": k,
        "u": u,
        "scalar_entropy_nats": scalar_entropy,
    }


def encode_matrix(matrix: np.ndarray) -> dict:
    return {"real": matrix.real.tolist(), "imag": matrix.imag.tolist()}


def case_record(x: np.ndarray, y: np.ndarray, coeff: np.ndarray, results: dict, index: int, **metadata) -> dict:
    return {
        **metadata,
        "shape": list(x.shape),
        "coefficients_alpha_beta_eta_delta": coeff.tolist(),
        "X": encode_matrix(x),
        "Y": encode_matrix(y),
        **{key: float(values[index]) for key, values in results.items()},
    }


def run(samples: int, seed: int, output: Path) -> dict:
    started = time.perf_counter()
    source = ROOT / "research" / "gad-thermal.tex"
    if hashlib.sha256(source.read_bytes()).hexdigest() != THERMAL_SOURCE_HASH:
        raise ValueError("pinned thermal source hash mismatch")
    worst = None
    violations = []
    random_counts = {}
    maximum_trace_error = 0.0
    maximum_hermitian_error = 0.0
    minimum_eigenvalue = 1.0
    minimum_random_margin = math.inf
    random_noncommuting = 0

    for shape_index, (rows, columns) in enumerate(SHAPES):
        count = samples // len(SHAPES) + int(shape_index < samples % len(SHAPES))
        if not count:
            continue
        rng = np.random.default_rng(np.random.SeedSequence([seed, 0, shape_index]))
        x = normalize(random_complex(rng, (count, rows, columns)))
        y = normalize(random_complex(rng, (count, rows, columns)))
        coefficients = rng.dirichlet(np.ones(4), size=count)
        reverse = coefficients[:, 0] * coefficients[:, 3] < coefficients[:, 1] * coefficients[:, 2]
        coefficients[reverse] = coefficients[reverse][:, [1, 0, 3, 2]]
        result = evaluate(x, y, coefficients)
        random_counts[f"{rows}x{columns}"] = count
        maximum_trace_error = max(maximum_trace_error, float(np.max(result["trace_error"])))
        maximum_hermitian_error = max(maximum_hermitian_error, float(np.max(result["hermitian_error"])))
        minimum_eigenvalue = min(minimum_eigenvalue, float(np.min(result["minimum_eigenvalue"])))
        random_noncommuting += int(np.count_nonzero(result["gram_commutator_norm"] > 1e-10))
        index = int(np.argmin(result["margin_nats"]))
        minimum_random_margin = min(minimum_random_margin, float(result["margin_nats"][index]))
        candidate = case_record(x[index], y[index], coefficients[index], result, index, sample_type="independent_seeded_random", seed_sequence=[seed, 0, shape_index], batch_index=index)
        if worst is None or candidate["margin_nats"] < worst["margin_nats"]:
            worst = candidate
        for bad in np.flatnonzero(result["margin_nats"] < -TOLERANCE):
            violations.append(case_record(x[bad], y[bad], coefficients[bad], result, int(bad), sample_type="random_bound_violation", seed_sequence=[seed, 0, shape_index], batch_index=int(bad)))

    structured = []
    maximum_equality_residual = 0.0
    maximum_column_gram_error = 0.0
    arbitrary_unitary_noncommuting = 0
    rng = np.random.default_rng(np.random.SeedSequence([seed, 1]))

    def add_structured(x, y, coeff, label, expected_residual, expected_bound=0.0, **extra):
        nonlocal maximum_equality_residual, maximum_trace_error, maximum_hermitian_error, minimum_eigenvalue, worst
        coeff = np.asarray(coeff, dtype=float)
        result = evaluate(x[None], y[None], coeff[None])
        record = case_record(x, y, coeff, result, 0, sample_type=label, **extra)
        record["expected_residual_nats"] = expected_residual
        record["expected_lower_bound_nats"] = expected_bound
        record["absolute_residual_reference_error_nats"] = abs(record["residual_nats"] - expected_residual)
        record["absolute_bound_reference_error_nats"] = abs(record["lower_bound_nats"] - expected_bound)
        structured.append(record)
        maximum_trace_error = max(maximum_trace_error, record["trace_error"])
        maximum_hermitian_error = max(maximum_hermitian_error, record["hermitian_error"])
        minimum_eigenvalue = min(minimum_eigenvalue, record["minimum_eigenvalue"])
        if expected_residual == 0.0:
            maximum_equality_residual = max(maximum_equality_residual, abs(record["residual_nats"]))
        if worst is None or record["margin_nats"] < worst["margin_nats"]:
            worst = record
        if record["margin_nats"] < -TOLERANCE or record["absolute_residual_reference_error_nats"] > TOLERANCE or record["absolute_bound_reference_error_nats"] > TOLERANCE:
            violations.append(record)
        return record

    # A nontrivial exact family: phases in a covariance eigenbasis, and
    # arbitrary unitaries inside a completely degenerate covariance.
    interior = (0.36, 0.14, 0.09, 0.41)
    for rows, columns in ((2, 2), (2, 3), (3, 3), (3, 4)):
        for index in range(6):
            q = unitary(rng, rows)
            values = np.full(rows, 1.0 / rows) if index % 2 == 0 else np.arange(1, rows + 1, dtype=float) / (rows * (rows + 1) / 2.0)
            x = q @ np.pad(np.diag(np.sqrt(values)), ((0, 0), (0, columns - rows)))
            if index % 2 == 0:
                u_matrix = unitary(rng, rows)
            else:
                u_matrix = q @ np.diag(np.exp(1j * rng.uniform(-math.pi, math.pi, rows))) @ q.conj().T
            y = u_matrix @ x
            a = x @ x.conj().T
            commutation_error = float(np.linalg.norm(u_matrix @ a - a @ u_matrix))
            if commutation_error > STATE_TOLERANCE:
                raise ValueError("structured commuting-unitary hypothesis failed")
            add_structured(x, y, interior, "commuting_unitary_interior_equality", 0.0, U=encode_matrix(u_matrix), covariance_spectrum=values.tolist(), unitary_covariance_commutator_norm=commutation_error, seed_sequence=[seed, 1])

    for rows, columns in SHAPES:
        for index in range(6):
            x = normalize(random_complex(rng, (rows, columns)))
            u_matrix = unitary(rng, rows)
            y = u_matrix @ x
            column_error = float(np.linalg.norm(x.conj().T @ x - y.conj().T @ y))
            maximum_column_gram_error = max(maximum_column_gram_error, column_error)
            if column_error > STATE_TOLERANCE:
                raise ValueError("u=0 column-Gram equality hypothesis failed")
            alpha = (0.25, 0.4, 0.6, 0.75)[index % 4]
            record = add_structured(x, y, (alpha, 0.0, 0.0, 1.0 - alpha), "u_zero_arbitrary_left_unitary_equality", 0.0, U=encode_matrix(u_matrix), column_gram_error=column_error, seed_sequence=[seed, 1])
            arbitrary_unitary_noncommuting += int(record["gram_commutator_norm"] > 1e-10)

    # Same output Grams alone do not imply equality. The two covariance
    # modes contribute h(U0) and g(u), respectively, giving the reference.
    root_half = math.sqrt(0.5)
    x = np.array([[root_half, 0.0, 0.0], [0.0, root_half, 0.0]], dtype=complex)
    y = np.array([[0.0, 0.0, root_half], [0.0, root_half, 0.0]], dtype=complex)
    a, b, eta, d = interior
    u_value = (a + b) * (eta + d) - (a * d - b * eta)
    small = (1.0 - math.sqrt(1.0 - 4.0 * u_value)) / 2.0
    expected_gap = 0.5 * (binary_entropy(a + b) - binary_entropy(small))
    counterexample = add_structured(x, y, interior, "equal_output_grams_not_sufficient", expected_gap, analytic_reference="R = (h(U0) - g(u))/2; XX*=YY*=I/2; XY*=diag(0,1/2)")
    if counterexample["gram_trace_norm"] > STATE_TOLERANCE or counterexample["residual_nats"] <= 1e-6:
        raise ValueError("same-Gram counterexample lost its defining behavior")

    # Independent classical reference: K=0, orthogonal pure output states.
    # The residual is h(r), and the Bernoulli Pinsker lower term is 2*r*(1-r).
    r = 0.75
    x = np.array([[1.0], [0.0]], dtype=complex)
    y = np.array([[0.0], [1.0]], dtype=complex)
    classical = add_structured(x, y, (0.375, 0.125, 0.375, 0.125), "classical_two_state_reference", binary_entropy(r), 2.0 * r * (1.0 - r), analytic_reference="R=h(3/4), lower term=2*(3/4)*(1/4)=3/8; coefficients are a product distribution")

    # The scalar API's zero-row extension has an independent exact zero.
    for coeff in ((0.0, 0.0, 0.25, 0.75), (0.25, 0.75, 0.0, 0.0)):
        actual = gap_lower_bound(coeff, 2.0)
        if actual != 0.0:
            violations.append({"sample_type": "scalar_zero_row_reference", "coefficients": list(coeff), "actual": actual, "expected": 0.0})

    report = {
        "schema_version": 1,
        "title": "Thermal stability lower-bound checks and exact equality families",
        "status": "checks_passed" if not violations else "check_failure",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": PIN,
        "source_thermal_sha256": THERMAL_SOURCE_HASH,
        "derivation": "docs/thermal-stability-derivation.md",
        "reproducibility": {"seed": seed, "generator": "PCG64", "seed_sequences": "random batches [seed,0,shape_index]; structured matrices [seed,1]", "python": platform.python_version(), "numpy": np.__version__, "platform": platform.platform(), "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "package_thermal_sha256": hashlib.sha256((ROOT / "math_to_code" / "thermal.py").read_bytes()).hexdigest(), "command": f"python scripts/check_thermal_stability.py --samples {samples} --seed {seed} --output results/thermal_stability.json"},
        "sample_counts": {"random_source_lemma_cases": samples, "random_by_shape": random_counts, "random_noncommuting_gram_cases": random_noncommuting, "commuting_unitary_interior_equality": 24, "u_zero_arbitrary_left_unitary_equality": 24, "u_zero_noncommuting_output_gram_equality": arbitrary_unitary_noncommuting, "equal_output_grams_not_sufficient": 1, "classical_two_state_reference": 1, "scalar_zero_row_references": 2, "total_matrix_cases": samples + len(structured)},
        "tolerances": {"bound_margin_and_exact_reference_absolute_nats": TOLERANCE, "state_and_hypothesis_absolute": STATE_TOLERANCE},
        "summary": {"violation_count": len(violations), "minimum_random_strengthened_margin_nats": minimum_random_margin, "minimum_strengthened_margin_nats": worst["margin_nats"], "maximum_exact_equality_absolute_residual_nats": maximum_equality_residual, "same_gram_counterexample_gap_nats": counterexample["residual_nats"], "same_gram_counterexample_bound_nats": counterexample["lower_bound_nats"], "classical_reference_bound_nats": classical["lower_bound_nats"], "classical_reference_residual_nats": classical["residual_nats"], "maximum_column_gram_equality_error": maximum_column_gram_error, "maximum_trace_error": maximum_trace_error, "maximum_hermitian_error": maximum_hermitian_error, "minimum_eigenvalue": minimum_eigenvalue, "wall_seconds": time.perf_counter() - started},
        "worst_margin_case": worst,
        "structured_cases": structured,
        "violations": violations,
        "scope": "Tests the scalar API against direct finite-dimensional matrix calculations and algebraic reference families; the derivation is documented separately. All finite numerical checks use floating-point tolerances.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=20261017)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "thermal_stability.json")
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("--samples must be positive")
    report = run(args.samples, args.seed, args.output)
    print(json.dumps({"status": report["status"], "sample_counts": report["sample_counts"], "summary": report["summary"], "output": str(args.output)}, indent=2))
    return int(report["summary"]["violation_count"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
