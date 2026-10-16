"""Seeded floating-point audit of family 276's rectangular thermal lemma.

This is deliberately independent of math_to_code.gad. It builds the matrix
in the pinned paper directly and evaluates its eigenvalues using NumPy.
Passing sampled tests is not a proof or a formal verification.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import time

import numpy as np


UPSTREAM_COMMIT = "1581d4cbdd69a0faf34b2089614fe2a814316a6a"
SOURCE_PATH = (
    "preprints/Classical-capacity-and-entropy-inequalities-for-"
    "generalized-amplitude-damping-September-24-2026/build/sections/thermal.tex"
)
SOURCE_URL = f"https://github.com/openai/math/blob/{UPSTREAM_COMMIT}/{SOURCE_PATH}"
SOURCE_SHA256 = "52a3470b411125ba69e7f39cc78c611695c895059288e212e3c5407a69882d14"
ROOT = Path(__file__).resolve().parents[1]
SHAPES = ((1, 1), (2, 3), (3, 2), (4, 5), (5, 3), (6, 2))
NUMERIC_TOLERANCE = 2e-10
STATE_TOLERANCE = 2e-12


def unit_hilbert_schmidt(matrix: np.ndarray) -> np.ndarray:
    return matrix / np.linalg.norm(matrix)


def random_matrix(rng: np.random.Generator, shape: tuple[int, int]) -> np.ndarray:
    return unit_hilbert_schmidt(
        rng.standard_normal(shape) + 1j * rng.standard_normal(shape)
    )


def matrix_pair(
    rng: np.random.Generator, shape: tuple[int, int], kind: str
) -> tuple[np.ndarray, np.ndarray]:
    x = random_matrix(rng, shape)
    if kind == "saturation_x_equals_y":
        return x, x.copy()
    if kind == "near_equal":
        perturbation = 10.0 ** rng.uniform(-13.0, -3.0)
        return x, unit_hilbert_schmidt(x + perturbation * random_matrix(rng, shape))
    if kind == "near_rank_one":
        rows, columns = shape
        noise = 10.0 ** rng.uniform(-13.0, -3.0)

        def low_rank() -> np.ndarray:
            left = rng.standard_normal(rows) + 1j * rng.standard_normal(rows)
            right = rng.standard_normal(columns) + 1j * rng.standard_normal(columns)
            return unit_hilbert_schmidt(
                np.outer(left, right.conj()) + noise * random_matrix(rng, shape)
            )

        return low_rank(), low_rank()
    if kind == "orthogonal_hilbert_schmidt" and shape != (1, 1):
        y = random_matrix(rng, shape)
        y = unit_hilbert_schmidt(y - np.vdot(x, y) * x)
        return x, y
    return x, random_matrix(rng, shape)


def random_coefficients(rng: np.random.Generator) -> tuple[float, ...]:
    # Swapping the two columns reverses the determinant without changing
    # nonnegativity or normalization. This covers arbitrary valid coefficients.
    a, b, eta, d = (float(value) for value in rng.dirichlet(np.ones(4)))
    if a * d < b * eta:
        a, b, eta, d = b, a, d, eta
    return a, b, eta, d


def coefficient_boundaries() -> list[tuple[str, tuple[float, ...]]]:
    cases = [
        ("only_alpha", (1.0, 0.0, 0.0, 0.0)),
        ("only_beta", (0.0, 1.0, 0.0, 0.0)),
        ("only_eta", (0.0, 0.0, 1.0, 0.0)),
        ("only_delta", (0.0, 0.0, 0.0, 1.0)),
        ("vanishing_top_row", (0.0, 0.0, 0.25, 0.75)),
        ("vanishing_bottom_row", (0.25, 0.75, 0.0, 0.0)),
        ("u_zero", (0.25, 0.0, 0.0, 0.75)),
        ("u_zero_balanced", (0.5, 0.0, 0.0, 0.5)),
        ("k_zero_maximum_u", (0.25, 0.25, 0.25, 0.25)),
        ("zero_beta", (0.25, 0.0, 0.25, 0.5)),
        ("zero_eta", (0.25, 0.25, 0.0, 0.5)),
    ]
    for epsilon in (1e-14, 1e-10, 1e-6):
        # Positive coefficients with determinant approaching zero.
        cases.append(
            (f"near_k_zero_{epsilon:g}", (0.25 + epsilon, 0.25 - epsilon, 0.25, 0.25))
        )
        # A normalized rank-one coefficient matrix perturbed towards u = 0.
        cases.append(
            (f"near_u_zero_{epsilon:g}", (0.5 - epsilon, epsilon, epsilon, 0.5 - epsilon))
        )
        cases.append(
            (f"near_zero_row_{epsilon:g}", (epsilon, 0.0, 0.25, 0.75 - epsilon))
        )
    return cases


def determinant_entropy(u: float) -> float:
    # Rationalizing the small eigenvalue avoids cancellation near u = 0.
    if not -STATE_TOLERANCE <= u <= 0.25 + STATE_TOLERANCE:
        raise ValueError(f"determinant entropy outside its domain: {u}")
    u = min(0.25, max(0.0, u))
    small = 2.0 * u / (1.0 + math.sqrt(max(0.0, 1.0 - 4.0 * u)))
    large = 1.0 - small
    return sum(-value * math.log(value) for value in (small, large) if value > 0.0)


def entropy_and_checks(matrix: np.ndarray) -> tuple[float, dict[str, float]]:
    trace_error = float(abs(np.trace(matrix) - 1.0))
    hermitian_error = float(np.max(np.abs(matrix - matrix.conj().T)))
    eigenvalues = np.linalg.eigvalsh((matrix + matrix.conj().T) * 0.5)
    minimum_eigenvalue = float(eigenvalues[0])
    if trace_error > STATE_TOLERANCE or hermitian_error > STATE_TOLERANCE:
        raise ValueError("constructed matrix fails trace or Hermiticity checks")
    if minimum_eigenvalue < -STATE_TOLERANCE:
        raise ValueError(f"constructed matrix is not positive semidefinite: {minimum_eigenvalue}")
    # Only eigenvalues already checked to be compatible with roundoff are
    # clipped. No trace renormalization or significant PSD repair is performed.
    positive = eigenvalues[eigenvalues > 0.0]
    entropy = float(-np.sum(positive * np.log(positive)))
    return entropy, {
        "trace_error": trace_error,
        "hermitian_error": hermitian_error,
        "minimum_eigenvalue": minimum_eigenvalue,
    }


def audit_case(x: np.ndarray, y: np.ndarray, coeff: tuple[float, ...]) -> dict:
    a, b, eta, d = coeff
    if min(coeff) < 0.0 or abs(sum(coeff) - 1.0) > STATE_TOLERANCE:
        raise ValueError("coefficients fail nonnegativity or normalization")
    determinant = a * d - b * eta
    if determinant < -STATE_TOLERANCE:
        raise ValueError("coefficient determinant is negative")
    k = math.sqrt(max(0.0, determinant))
    u = (a + b) * (eta + d) - k * k
    xx = x @ x.conj().T
    yy = y @ y.conj().T
    xy = x @ y.conj().T
    full = np.block([[a * xx + b * yy, k * xy], [k * xy.conj().T, eta * xx + d * yy]])
    entropy_full, full_checks = entropy_and_checks(full)
    entropy_xx, x_checks = entropy_and_checks(xx)
    entropy_yy, y_checks = entropy_and_checks(yy)
    rhs = (a + eta) * entropy_xx + (b + d) * entropy_yy + determinant_entropy(u)
    checks = (full_checks, x_checks, y_checks)
    return {
        "lhs_entropy_nats": entropy_full,
        "rhs_entropy_nats": rhs,
        "residual_nats": entropy_full - rhs,
        "coefficients_alpha_beta_eta_delta": list(coeff),
        "K": k,
        "u": u,
        "coefficient_identity_error": abs(a * d - b * eta - k * k),
        "coefficient_sum_error": abs(sum(coeff) - 1.0),
        "maximum_trace_error": max(item["trace_error"] for item in checks),
        "maximum_hermitian_error": max(item["hermitian_error"] for item in checks),
        "minimum_eigenvalue": min(item["minimum_eigenvalue"] for item in checks),
    }


def serialize_matrix(matrix: np.ndarray) -> dict:
    return {"real": matrix.real.tolist(), "imag": matrix.imag.tolist()}


def run_audit(samples: int, seed: int, output: Path) -> dict:
    source_file = ROOT / "research" / "gad-thermal.tex"
    source_sha = hashlib.sha256(source_file.read_bytes()).hexdigest()
    if source_sha != SOURCE_SHA256:
        raise ValueError("pinned thermal source has changed; recheck provenance before running")

    rng = np.random.default_rng(seed)
    started = time.perf_counter()
    types: Counter[str] = Counter()
    shapes: Counter[str] = Counter()
    boundaries: Counter[str] = Counter()
    violations = []
    worst = None
    worst_saturation = None
    max_trace_error = 0.0
    max_hermitian_error = 0.0
    max_coefficient_error = 0.0
    min_eigenvalue = 1.0
    noncommuting_cases = 0
    max_commutator_norm = 0.0

    def record(x: np.ndarray, y: np.ndarray, coeff: tuple[float, ...], kind: str, name: str) -> None:
        nonlocal worst, worst_saturation, max_trace_error, max_hermitian_error
        nonlocal max_coefficient_error, min_eigenvalue, noncommuting_cases, max_commutator_norm
        result = audit_case(x, y, coeff)
        result.update({"sample_type": kind, "case": name, "shape": list(x.shape)})
        types[kind] += 1
        shapes[f"{x.shape[0]}x{x.shape[1]}"] += 1
        max_trace_error = max(max_trace_error, result["maximum_trace_error"])
        max_hermitian_error = max(max_hermitian_error, result["maximum_hermitian_error"])
        max_coefficient_error = max(max_coefficient_error, result["coefficient_identity_error"], result["coefficient_sum_error"])
        min_eigenvalue = min(min_eigenvalue, result["minimum_eigenvalue"])
        xx, yy = x @ x.conj().T, y @ y.conj().T
        commutator = float(np.linalg.norm(xx @ yy - yy @ xx))
        max_commutator_norm = max(max_commutator_norm, commutator)
        noncommuting_cases += int(commutator > 1e-10)
        if worst is None or result["residual_nats"] < worst["residual_nats"]:
            worst = result | {"X": serialize_matrix(x), "Y": serialize_matrix(y)}
        if kind == "saturation_x_equals_y":
            if worst_saturation is None or abs(result["residual_nats"]) > abs(worst_saturation["residual_nats"]):
                worst_saturation = result
        if result["residual_nats"] < -NUMERIC_TOLERANCE:
            violations.append(result | {"X": serialize_matrix(x), "Y": serialize_matrix(y)})
        if kind == "saturation_x_equals_y" and abs(result["residual_nats"]) > NUMERIC_TOLERANCE:
            violations.append(result | {"failure": "expected saturation is not met"})

    # The sample-category schedule is deterministic; matrices and coefficients
    # within each category use the documented PCG64 generator and seed.
    for index in range(samples):
        bucket = index % 20
        if bucket < 13:
            kind = "independent_complex_gaussian"
        elif bucket < 15:
            kind = "near_rank_one"
        elif bucket < 17:
            kind = "near_equal"
        elif bucket < 19:
            kind = "saturation_x_equals_y"
        else:
            kind = "orthogonal_hilbert_schmidt"
        shape = SHAPES[index % len(SHAPES)]
        if kind == "orthogonal_hilbert_schmidt" and shape == (1, 1):
            shape = (2, 3)
        x, y = matrix_pair(rng, shape, kind)
        record(x, y, random_coefficients(rng), kind, f"random_{index}")

    for shape in SHAPES:
        # Deterministic matrix examples supplement the seeded random samples.
        count = shape[0] * shape[1]
        real = np.arange(1, count + 1, dtype=float).reshape(shape)
        imag = np.arange(count, 0, -1, dtype=float).reshape(shape)
        x = unit_hilbert_schmidt(real + 1j * imag)
        y = unit_hilbert_schmidt(np.flip(real, axis=0) - 1j * np.flip(imag, axis=1))
        for name, coeff in coefficient_boundaries():
            record(x, y, coeff, "explicit_coefficient_boundary", name)
            record(x, x, coeff, "saturation_x_equals_y", f"boundary_saturation_{name}")
            boundaries[name] += 2

    report = {
        "schema_version": 1,
        "title": "Numerical audit of the rectangular thermal entropy inequality",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "no_sampled_violation" if not violations else "sampled_violation",
        "claim_limit": "Finite floating-point tests only. This does not prove the lemma, verify its Lean formalization, or establish a new theorem.",
        "source": {
            "repository": "https://github.com/openai/math",
            "commit": UPSTREAM_COMMIT,
            "url": SOURCE_URL,
            "local_path": "research/gad-thermal.tex",
            "sha256": source_sha,
            "theorem_label": "thm:thermal",
            "equation_labels": ["eq:thermal-condition", "eq:thermal-state", "eq:thermal-bound"],
        },
        "implementation": {
            "independent_of_package_capacity_code": True,
            "entropy_units": "nats (natural logarithm)",
            "eigenvalue_solver": "numpy.linalg.eigvalsh",
            "entropy_handling": "Hermitian residual checked before symmetric averaging; eigenvalues below zero are ignored only after PSD tolerance passes; no trace renormalization.",
            "determinant_entropy": "small eigenvalue 2u/(1+sqrt(1-4u)), avoiding subtraction near zero",
            "source_hash_checked_before_run": True,
        },
        "reproducibility": {
            "seed": seed,
            "generator": type(rng.bit_generator).__name__,
            "python": platform.python_version(),
            "numpy": np.__version__,
            "platform": platform.platform(),
            "command": f"python scripts/validate_thermal.py --samples {samples} --seed {seed} --out results/thermal_audit.json",
        },
        "sample_counts": {
            "seeded_random": samples,
            "explicit_boundary": 2 * len(SHAPES) * len(coefficient_boundaries()),
            "total": sum(types.values()),
            "by_type": dict(sorted(types.items())),
            "by_matrix_shape": dict(sorted(shapes.items())),
            "boundary_cases": dict(sorted(boundaries.items())),
            "noncommuting_gram_cases_at_norm_gt_1e_minus_10": noncommuting_cases,
        },
        "tolerances": {"inequality_and_saturation_absolute_nats": NUMERIC_TOLERANCE, "state_and_coefficient_absolute": STATE_TOLERANCE},
        "summary": {
            "violation_count": len(violations),
            "minimum_inequality_residual_nats": worst["residual_nats"],
            "maximum_saturation_absolute_residual_nats": abs(worst_saturation["residual_nats"]),
            "maximum_trace_error": max_trace_error,
            "maximum_hermitian_error": max_hermitian_error,
            "maximum_coefficient_identity_or_sum_error": max_coefficient_error,
            "minimum_eigenvalue_observed": min_eigenvalue,
            "maximum_gram_commutator_frobenius_norm": max_commutator_norm,
            "wall_seconds": time.perf_counter() - started,
        },
        "worst_inequality_case": worst,
        "worst_saturation_case": worst_saturation,
        "violations": violations,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20261017)
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "thermal_audit.json")
    args = parser.parse_args()
    if args.samples < 20:
        parser.error("--samples must be at least 20 to cover every sample category")
    report = run_audit(args.samples, args.seed, args.out)
    print(json.dumps({"status": report["status"], "samples": report["sample_counts"]["total"], "summary": report["summary"], "output": str(args.out)}, indent=2))
    return int(report["summary"]["violation_count"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
