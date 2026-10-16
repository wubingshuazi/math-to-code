"""Local perturbations of the pinned rectangular thermal entropy expression.

Run with the repository's NumPy environment. X and H are stored explicitly:
Y(epsilon) = (X + epsilon H) / ||X + epsilon H||_HS.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import time

import numpy as np

from validate_thermal import (
    ROOT,
    SOURCE_SHA256,
    SOURCE_URL,
    UPSTREAM_COMMIT,
    audit_case,
    coefficient_boundaries,
    serialize_matrix,
    unit_hilbert_schmidt,
)


SHAPES = ((2, 2), (2, 3), (3, 2))
EPSILONS = tuple(10.0 ** -power for power in range(1, 9))
DEFAULT_SEED = 2026101702
RESOLUTION_MULTIPLIER = 10.0
FLOOR_ROUNDOFF_MULTIPLIER = 64.0


def unitary(rng: np.random.Generator, dimension: int) -> np.ndarray:
    raw = rng.standard_normal((dimension, dimension)) + 1j * rng.standard_normal((dimension, dimension))
    q, r = np.linalg.qr(raw)
    diagonal = np.diag(r)
    phases = np.where(np.abs(diagonal) > 0.0, diagonal / np.abs(diagonal), 1.0)
    return q * phases


def example(rng: np.random.Generator, shape: tuple[int, int], rank_kind: str) -> tuple[np.ndarray, np.ndarray]:
    left, right = unitary(rng, shape[0]), unitary(rng, shape[1])
    singular_values = np.array([1.0, 0.55 if rank_kind == "full_rank" else 1e-4])
    x = unit_hilbert_schmidt(left[:, :2] @ np.diag(singular_values) @ right[:, :2].conj().T)
    raw_h = rng.standard_normal(shape) + 1j * rng.standard_normal(shape)
    # Complex Hilbert-Schmidt orthogonality removes both real radial X and
    # imaginary phase iX components; this is stronger than real tangency alone.
    h = unit_hilbert_schmidt(raw_h - np.vdot(x, raw_h) * x)
    return x, h


def finite_slope(samples: list[dict], floor: float) -> dict:
    selected = [
        sample for sample in samples
        if 1e-4 <= sample["epsilon"] <= 1e-2
        and sample["residual_nats"] > RESOLUTION_MULTIPLIER * floor
    ]
    pairs = []
    for first, second in zip(selected, selected[1:]):
        pairs.append({
            "epsilon_high": first["epsilon"],
            "epsilon_low": second["epsilon"],
            "slope": math.log(first["residual_nats"] / second["residual_nats"]) / math.log(first["epsilon"] / second["epsilon"]),
        })
    slope = None
    if len(selected) >= 2:
        log_epsilon = np.log([sample["epsilon"] for sample in selected])
        log_residual = np.log([sample["residual_nats"] for sample in selected])
        slope = float(np.polyfit(log_epsilon, log_residual, 1)[0])
    return {
        "fit_range_requested": [1e-4, 1e-2],
        "resolved_epsilon_values": [sample["epsilon"] for sample in selected],
        "resolved_point_count": len(selected),
        "estimated_log_log_slope": slope,
        "adjacent_resolved_slopes": pairs,
    }


def hermitian_trace_norm(matrix: np.ndarray) -> float:
    return float(np.sum(np.abs(np.linalg.eigvalsh((matrix + matrix.conj().T) * 0.5))))


def evaluate_path(x: np.ndarray, h: np.ndarray, coefficients: tuple[float, ...]) -> list[dict]:
    samples = []
    a, b, eta, d = coefficients
    u0, u1 = a + b, eta + d
    bound_prefactor = b * eta / (2.0 * u0 * u1) if u0 * u1 > 0.0 else 0.0
    xx = x @ x.conj().T
    for epsilon in EPSILONS:
        y = unit_hilbert_schmidt(x + epsilon * h)
        value = audit_case(x, y, coefficients)
        raw_residual = value["residual_nats"]
        gram_difference_norm = hermitian_trace_norm(xx - y @ y.conj().T)
        quantitative_bound = bound_prefactor * gram_difference_norm * gram_difference_norm
        samples.append({
            "epsilon": epsilon,
            "residual_nats": raw_residual,
            "residual_over_epsilon_squared": raw_residual / (epsilon * epsilon),
            "gram_difference_trace_norm": gram_difference_norm,
            "quantitative_lower_bound_nats": quantitative_bound,
            "residual_minus_quantitative_bound_nats": raw_residual - quantitative_bound,
            "lhs_entropy_nats": value["lhs_entropy_nats"],
            "rhs_entropy_nats": value["rhs_entropy_nats"],
            "minimum_eigenvalue": value["minimum_eigenvalue"],
            "maximum_trace_error": value["maximum_trace_error"],
            "maximum_hermitian_error": value["maximum_hermitian_error"],
        })
    return samples


def run(seed: int, output: Path) -> dict:
    source_sha = hashlib.sha256((ROOT / "research/gad-thermal.tex").read_bytes()).hexdigest()
    if source_sha != SOURCE_SHA256:
        raise ValueError("Pinned thermal source hash mismatch")
    started = time.perf_counter()
    rng = np.random.default_rng(seed)
    coefficient_cases = [
        ("interior_asymmetric", (0.4, 0.1, 0.15, 0.35)),
        ("interior_symmetric", (0.4, 0.1, 0.1, 0.4)),
    ] + coefficient_boundaries()
    paths = []
    selected_ids = []
    for shape in SHAPES:
        for rank_kind in ("full_rank", "near_rank_one"):
            x, generic_h = example(rng, shape, rank_kind)
            directions = {
                "generic_complex_orthogonal_tangent": generic_h,
                "global_phase_gauge": 1j * x,
                "radial_scale_gauge": x.copy(),
            }
            for coefficient_name, coefficients in coefficient_cases:
                baseline = audit_case(x, x, coefficients)
                evaluated = {name: evaluate_path(x, h, coefficients) for name, h in directions.items()}
                gauge_max = max(
                    abs(sample["residual_nats"])
                    for name, samples in evaluated.items()
                    if name != "generic_complex_orthogonal_tangent"
                    for sample in samples
                )
                entropy_scale = max(
                    1.0,
                    abs(baseline["lhs_entropy_nats"]),
                    abs(baseline["rhs_entropy_nats"]),
                )
                roundoff_scale = FLOOR_ROUNDOFF_MULTIPLIER * np.finfo(np.float64).eps * entropy_scale
                floor = max(abs(baseline["residual_nats"]), gauge_max, float(roundoff_scale))
                for direction_name, h in directions.items():
                    path_id = f"{shape[0]}x{shape[1]}__{rank_kind}__{coefficient_name}__{direction_name}"
                    samples = evaluated[direction_name]
                    for sample in samples:
                        sample["numerical_floor_nats"] = floor
                        sample["positive_resolved"] = sample["residual_nats"] > RESOLUTION_MULTIPLIER * floor
                        sample["negative_resolved"] = sample["residual_nats"] < -RESOLUTION_MULTIPLIER * floor
                        bound = sample["quantitative_lower_bound_nats"]
                        bound_resolved = bound > RESOLUTION_MULTIPLIER * floor
                        sample["quantitative_bound_resolved"] = bound_resolved
                        sample["residual_over_quantitative_bound"] = sample["residual_nats"] / bound if bound_resolved else None
                        sample["quantitative_bound_fraction_of_residual"] = bound / sample["residual_nats"] if bound_resolved and sample["positive_resolved"] else None
                        sample["quantitative_bound_violation_resolved"] = sample["residual_minus_quantitative_bound_nats"] < -RESOLUTION_MULTIPLIER * floor
                    derivative = h @ x.conj().T + x @ h.conj().T
                    path = {
                        "path_id": path_id,
                        "shape": list(shape),
                        "rank_kind": rank_kind,
                        "direction": direction_name,
                        "coefficient_regime": coefficient_name,
                        "coefficients_alpha_beta_eta_delta": list(coefficients),
                        "K": baseline["K"],
                        "u": baseline["u"],
                        "X": serialize_matrix(x),
                        "H": serialize_matrix(h),
                        "x_hilbert_schmidt_norm": float(np.linalg.norm(x)),
                        "h_hilbert_schmidt_norm": float(np.linalg.norm(h)),
                        "x_h_complex_inner_product": {"real": float(np.vdot(x, h).real), "imag": float(np.vdot(x, h).imag)},
                        "x_singular_values": np.linalg.svd(x, compute_uv=False).tolist(),
                        "generic_tangent_gram_derivative_trace_norm": hermitian_trace_norm(derivative) if direction_name == "generic_complex_orthogonal_tangent" else None,
                        "quantitative_bound_prefactor": coefficients[1] * coefficients[2] / (2.0 * (coefficients[0] + coefficients[1]) * (coefficients[2] + coefficients[3])) if (coefficients[0] + coefficients[1]) * (coefficients[2] + coefficients[3]) > 0.0 else 0.0,
                        "baseline_residual_nats": baseline["residual_nats"],
                        "baseline_lhs_entropy_nats": baseline["lhs_entropy_nats"],
                        "baseline_rhs_entropy_nats": baseline["rhs_entropy_nats"],
                        "gauge_max_absolute_residual_nats": gauge_max,
                        "roundoff_scale_nats": float(roundoff_scale),
                        "numerical_floor_nats": floor,
                        "samples": samples,
                        "slope_estimate": finite_slope(samples, floor),
                    }
                    paths.append(path)
                    if direction_name == "generic_complex_orthogonal_tangent" and (
                        coefficient_name == "interior_asymmetric"
                        or (coefficient_name == "u_zero_balanced" and rank_kind == "near_rank_one")
                        or (coefficient_name == "k_zero_maximum_u" and rank_kind == "full_rank")
                    ):
                        selected_ids.append(path_id)

    generic = [path for path in paths if path["direction"] == "generic_complex_orthogonal_tangent"]
    gauge = [path for path in paths if path["direction"] != "generic_complex_orthogonal_tangent"]
    resolved_generic = [path for path in generic if path["slope_estimate"]["estimated_log_log_slope"] is not None]
    slopes = [path["slope_estimate"]["estimated_log_log_slope"] for path in resolved_generic]
    summary_by_regime = []
    for coefficient_name, _ in coefficient_cases:
        subset = [path for path in generic if path["coefficient_regime"] == coefficient_name]
        subset_slopes = [path["slope_estimate"]["estimated_log_log_slope"] for path in subset if path["slope_estimate"]["estimated_log_log_slope"] is not None]
        subset_fractions = [sample["quantitative_bound_fraction_of_residual"] for path in subset for sample in path["samples"] if sample["quantitative_bound_fraction_of_residual"] is not None]
        summary_by_regime.append({
            "coefficient_regime": coefficient_name,
            "generic_path_count": len(subset),
            "resolved_fit_count": len(subset_slopes),
            "slope_minimum": min(subset_slopes) if subset_slopes else None,
            "slope_maximum": max(subset_slopes) if subset_slopes else None,
            "maximum_absolute_generic_residual_nats": max(abs(sample["residual_nats"]) for path in subset for sample in path["samples"]),
            "quantitative_bound_resolved_samples": len(subset_fractions),
            "quantitative_bound_fraction_minimum": min(subset_fractions) if subset_fractions else None,
            "quantitative_bound_fraction_median": float(np.median(subset_fractions)) if subset_fractions else None,
            "quantitative_bound_fraction_maximum": max(subset_fractions) if subset_fractions else None,
        })
    all_samples = [sample for path in paths for sample in path["samples"]]
    bound_resolved_samples = [sample for sample in all_samples if sample["quantitative_bound_fraction_of_residual"] is not None]
    bound_fractions = [sample["quantitative_bound_fraction_of_residual"] for sample in bound_resolved_samples]
    report = {
        "schema_version": 2,
        "title": "Local thermal entropy perturbation experiment",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "upstream_commit": UPSTREAM_COMMIT,
        "source_url": SOURCE_URL,
        "source_sha256": source_sha,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "seed": seed,
        "rng": "NumPy default_rng PCG64",
        "method": {
            "path": "Y(epsilon) = normalize_HS(X + epsilon H)",
            "generic_direction": "H = normalize_HS(G - <X,G>_complex_HS X)",
            "full_rank_unscaled_singular_values": [1.0, 0.55],
            "near_rank_one_unscaled_singular_values": [1.0, 1e-4],
            "gauge_directions": {"global_phase_gauge": "H=iX", "radial_scale_gauge": "H=X"},
            "numerical_floor": "max(|baseline residual|, max |phase/scale gauge residual|, 64*float64_epsilon*max(1,|baseline lhs|,|baseline rhs|))",
            "numerical_floor_status": "Declared empirical/roundoff scale, not a rigorous error bound",
            "resolution_rule": "Positive raw residual > 10*numerical_floor",
            "slope": "OLS log(raw positive residual) against log(epsilon), using only resolved epsilon in [1e-4,1e-2] and requiring at least two points",
            "raw_residual_is_not_baseline_subtracted": True,
            "epsilon_values": list(EPSILONS),
            "quantitative_lower_bound": "R >= beta*eta/(2*U0*U1) * ||XX*-YY*||_1^2, in nats, where U0=alpha+beta and U1=eta+delta; use zero bound if U0*U1=0",
            "quantitative_bound_provenance": "Derived corollary from the pinned thermal mixture inequality plus quantum Pinsker; analytic proof and review are separate from this numerical calculation",
            "trace_norm_evaluation": "Sum absolute eigenvalues of the Hermitian Gram difference",
            "bound_ratio_rule": "Report residual/bound and bound/residual only when bound>10*numerical_floor; bound/residual additionally requires positive resolved residual",
            "generic_tangent_gram_derivative": "D=HX*+XH*; ||D||_1 is recorded per generic complex-HS-orthogonal tangent path",
        },
        "summary": {
            "matrix_examples": len(SHAPES) * 2,
            "coefficient_regimes": len(coefficient_cases),
            "paths": len(paths),
            "samples": len(all_samples),
            "generic_paths": len(generic),
            "generic_paths_with_resolved_slope": len(resolved_generic),
            "minimum_resolved_slope": min(slopes) if slopes else None,
            "maximum_resolved_slope": max(slopes) if slopes else None,
            "maximum_absolute_gauge_residual_nats": max(abs(sample["residual_nats"]) for path in gauge for sample in path["samples"]),
            "minimum_raw_residual_nats": min(sample["residual_nats"] for sample in all_samples),
            "negative_resolved_sample_count": sum(sample["negative_resolved"] for sample in all_samples),
            "maximum_trace_error": max(sample["maximum_trace_error"] for sample in all_samples),
            "minimum_eigenvalue": min(sample["minimum_eigenvalue"] for sample in all_samples),
            "minimum_residual_minus_quantitative_bound_nats": min(sample["residual_minus_quantitative_bound_nats"] for sample in all_samples),
            "quantitative_bound_violation_resolved_sample_count": sum(sample["quantitative_bound_violation_resolved"] for sample in all_samples),
            "quantitative_bound_resolved_samples": len(bound_resolved_samples),
            "quantitative_bound_fraction_minimum": min(bound_fractions) if bound_fractions else None,
            "quantitative_bound_fraction_median": float(np.median(bound_fractions)) if bound_fractions else None,
            "quantitative_bound_fraction_maximum": max(bound_fractions) if bound_fractions else None,
            "elapsed_seconds": time.perf_counter() - started,
        },
        "summary_by_coefficient_regime": summary_by_regime,
        "selected_high_precision_replay_path_ids": selected_ids,
        "paths": paths,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    selected_output = output.with_name(output.stem + "_selected.json")
    selected_output.write_text(json.dumps({
        "title": "Selected normalized thermal perturbation paths for high precision replay",
        "source_url": SOURCE_URL,
        "source_sha256": source_sha,
        "path_definition": report["method"]["path"],
        "paths": [path for path in paths if path["path_id"] in selected_ids],
    }, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    csv_output = output.with_suffix(".csv")
    with csv_output.open("w", newline="", encoding="utf-8") as stream:
        sample_fields = ["epsilon", "residual_nats", "residual_over_epsilon_squared", "gram_difference_trace_norm", "quantitative_lower_bound_nats", "residual_minus_quantitative_bound_nats", "numerical_floor_nats", "positive_resolved", "negative_resolved", "quantitative_bound_resolved", "residual_over_quantitative_bound", "quantitative_bound_fraction_of_residual", "quantitative_bound_violation_resolved"]
        fieldnames = ["path_id", "shape", "rank_kind", "direction", "coefficient_regime", "generic_tangent_gram_derivative_trace_norm", *sample_fields, "estimated_log_log_slope"]
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for path in paths:
            for sample in path["samples"]:
                writer.writerow({
                    "path_id": path["path_id"],
                    "shape": "x".join(map(str, path["shape"])),
                    "rank_kind": path["rank_kind"],
                    "direction": path["direction"],
                    "coefficient_regime": path["coefficient_regime"],
                    "generic_tangent_gram_derivative_trace_norm": path["generic_tangent_gram_derivative_trace_norm"],
                    **{key: sample[key] for key in sample_fields},
                    "estimated_log_log_slope": path["slope_estimate"]["estimated_log_log_slope"],
                })
    return report


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output", type=Path, default=ROOT / "results/thermal_perturbations.json")
    args = parser.parse_args()
    report = run(args.seed, args.output)
    print(json.dumps({"summary": report["summary"], "summary_by_coefficient_regime": report["summary_by_coefficient_regime"], "selected_high_precision_replay_path_ids": report["selected_high_precision_replay_path_ids"]}, indent=2))


if __name__ == "__main__":
    main()
