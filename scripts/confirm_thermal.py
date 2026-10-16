"""Replay selected sharpness candidates and paths at 80 and 160 digits.

Inputs are interpreted as the exact decimal strings saved in the JSON files.
The factor-spectrum calculation is an independent binary64 cross-check;
high-precision eigensolver calculations are consistency evidence, not a proof.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import time

import mpmath as mp
import numpy as np

from thermal_reference import reference_residual, singular_residual


ROOT = Path(__file__).resolve().parents[1]
PRECISION_COMPARISON_TOLERANCE = "1e-65"


def _read_exact(path):
    return json.loads(path.read_text(encoding="utf-8"), parse_float=str)


def _comparison(low, high):
    with mp.workdps(max(low["dps"], high["dps"]) + 10):
        delta = abs(mp.mpf(low["residual_nats"]) - mp.mpf(high["residual_nats"]))
        margin_delta = abs(mp.mpf(low["pinsker_margin_nats"]) - mp.mpf(high["pinsker_margin_nats"]))
        tolerance = mp.mpf(PRECISION_COMPARISON_TOLERANCE)
        return {
            "residual_absolute_difference_nats": mp.nstr(delta, 30),
            "pinsker_margin_absolute_difference_nats": mp.nstr(margin_delta, 30),
            "absolute_comparison_tolerance_nats": PRECISION_COMPARISON_TOLERANCE,
            "precision_agreement_passed": bool(delta < tolerance and margin_delta < tolerance),
            "positive_residual_at_both_precisions": bool(mp.mpf(low["residual_nats"]) > 0 and mp.mpf(high["residual_nats"]) > 0),
            "pinsker_margin_nonnegative_within_comparison_tolerance": bool(mp.mpf(low["pinsker_margin_nats"]) >= -tolerance and mp.mpf(high["pinsker_margin_nats"]) >= -tolerance),
        }


def _path_pair(path, epsilon, dps):
    """Reconstruct this precise path entirely inside an mpmath context."""
    with mp.workdps(dps):
        def matrix(data):
            return mp.matrix([[mp.mpc(mp.mpf(str(real)), mp.mpf(str(imag))) for real, imag in zip(real_row, imag_row)] for real_row, imag_row in zip(data["real"], data["imag"])])
        def norm(value):
            return mp.sqrt(mp.fsum(abs(entry)**2 for entry in value))
        def serialize(value):
            return {"real": [[mp.nstr(value[i, j].real, dps) for j in range(value.cols)] for i in range(value.rows)], "imag": [[mp.nstr(value[i, j].imag, dps) for j in range(value.cols)] for i in range(value.rows)]}
        x, h = matrix(path["X"]), matrix(path["H"])
        original_x_norm, original_h_norm = norm(x), norm(h)
        x, h = x / original_x_norm, h / original_h_norm
        tangent_inner = mp.fsum(mp.conj(left) * right for left, right in zip(x, h))
        y = x + mp.mpf(epsilon) * h
        y /= norm(y)
        return serialize(x), serialize(y), {
            "original_x_hilbert_schmidt_norm": mp.nstr(original_x_norm, dps),
            "original_h_hilbert_schmidt_norm": mp.nstr(original_h_norm, dps),
            "normalized_x_h_inner_product_real": mp.nstr(tangent_inner.real, dps),
            "normalized_x_h_inner_product_imag": mp.nstr(tangent_inner.imag, dps),
            "tangent_reprojection_performed": False,
        }


def run_confirmation(search_path, paths_path, per_shape=3):
    started = time.perf_counter()
    search = _read_exact(search_path)
    perturbations = _read_exact(paths_path)
    groups = {}
    for start in search["starts"]:
        best = start.get("best")
        if best is None or not best.get("feasible", False):
            continue
        shape = "x".join(str(value) for value in start["shape"])
        groups.setdefault(shape, []).append(start)
    selected = []
    for shape in sorted(groups):
        group = sorted(groups[shape], key=lambda item: float(item["best"]["residual_nats"]))
        if len(group) < per_shape:
            raise ValueError(f"not enough feasible candidates for shape {shape}")
        selected.extend(group[:per_shape])
    if not selected:
        raise ValueError("no feasible saved search candidates")

    candidates = []
    for start in selected:
        best = start["best"]
        x, y, coeff = best["X"], best["Y"], best["coefficient"]
        low = reference_residual(x, y, coeff, dps=80)
        high = reference_residual(x, y, coeff, dps=160)
        factor = singular_residual(x, y, coeff)
        factor_pass = bool(factor["reconstruction_max_abs_error"] < 1e-12 and factor["maximum_spectrum_abs_difference"] < 1e-12 and abs(factor["residual_difference_nats"]) < 1e-12)
        candidates.append({
            "start_id": start["start_id"],
            "shape": start["shape"],
            "selection": f"one of {per_shape} lowest saved feasible residuals in its shape",
            "search_termination": start["termination"],
            "search_optimizer_success": start["optimizer_success"],
            "reported_search_residual_nats": best["residual_nats"],
            "exact_saved_decimal_inputs": {"X": x, "Y": y, "coefficients_alpha_beta_eta_delta": coeff},
            "at_80_digits": low,
            "at_160_digits": high,
            "precision_comparison": _comparison(low, high),
            "independent_factor_spectrum": factor,
            "factor_consistency_passed": factor_pass,
        })

    paths = []
    for path in perturbations["paths"]:
        samples = []
        coeff = path["coefficients_alpha_beta_eta_delta"]
        for epsilon in ("0.0001", "0.000001", "0.00000001"):
            confirmations = []
            for dps in (80, 160):
                x, y, reconstruction = _path_pair(path, epsilon, dps)
                value = reference_residual(x, y, coeff, dps=dps)
                with mp.workdps(dps):
                    scaled = mp.mpf(value["residual_nats"]) / mp.mpf(epsilon)**2
                    bound_scaled = mp.mpf(value["pinsker_lower_bound_nats"]) / mp.mpf(epsilon)**2
                    value["residual_over_epsilon_squared"] = mp.nstr(scaled, dps)
                    value["pinsker_bound_over_epsilon_squared"] = mp.nstr(bound_scaled, dps)
                confirmations.append({"reference": value, "path_reconstruction": reconstruction})
            samples.append({"epsilon_exact_decimal": epsilon, "at_80_digits": confirmations[0], "at_160_digits": confirmations[1], "precision_comparison": _comparison(confirmations[0]["reference"], confirmations[1]["reference"])})
        paths.append({
            "path_id": path["path_id"],
            "shape": path["shape"],
            "rank_kind": path["rank_kind"],
            "coefficient_regime": path["coefficient_regime"],
            "exact_saved_decimal_inputs": {"X": path["X"], "H": path["H"], "coefficients_alpha_beta_eta_delta": coeff},
            "samples": samples,
        })

    comparisons = [item["precision_comparison"] for item in candidates] + [sample["precision_comparison"] for path in paths for sample in path["samples"]]
    passed = all(item["precision_agreement_passed"] and item["pinsker_margin_nonnegative_within_comparison_tolerance"] for item in comparisons) and all(item["factor_consistency_passed"] for item in candidates)
    return {
        "schema_version": 1,
        "experiment": "Independent factor-spectrum and 80/160-digit confirmation of thermal sharpness candidates",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "numerical_consistency_passed" if passed else "confirmation_requires_review",
        "scope": "Finite high-precision numerical consistency only. Neither an interval proof nor proof of the lemma/corollary. Search points are best saved feasible points, not certified or necessarily converged minima.",
        "input_reconstruction": "JSON floating-point tokens read as exact decimal strings. Candidate X,Y normalized in each high-precision evaluation. Path X,H each normalized in requested precision, then Y=normalize_HS(X+epsilon H); H direction preserved without reprojection. Coefficients receive explicit near-unit common normalization, never determinant-sign repair.",
        "source_files": [{"path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in (search_path, paths_path)],
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "mpmath": mp.__version__, "platform": platform.platform()},
        "settings": {"precisions_decimal_digits": [80, 160], "search_candidates_per_shape": per_shape, "epsilon_exact_decimals": ["0.0001", "0.000001", "0.00000001"], "factor_consistency_absolute_tolerance": 1e-12},
        "summary": {"search_candidates": len(candidates), "candidate_shapes": sorted(groups), "perturbation_paths": len(paths), "perturbation_points": sum(len(path["samples"]) for path in paths), "total_high_precision_evaluations": 2 * len(comparisons), "precision_comparisons_passed": sum(item["precision_agreement_passed"] for item in comparisons), "positive_residual_comparisons": sum(item["positive_residual_at_both_precisions"] for item in comparisons), "pinsker_margin_comparisons_passed": sum(item["pinsker_margin_nonnegative_within_comparison_tolerance"] for item in comparisons), "factor_comparisons_passed": sum(item["factor_consistency_passed"] for item in candidates), "wall_seconds": time.perf_counter() - started},
        "search_candidates": candidates,
        "perturbation_paths": paths,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search", type=Path, default=ROOT / "results" / "sharpness_search.json")
    parser.add_argument("--paths", type=Path, default=ROOT / "results" / "thermal_perturbations_selected.json")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "thermal_high_precision.json")
    parser.add_argument("--per-shape", type=int, default=3)
    args = parser.parse_args()
    if args.per_shape < 1:
        parser.error("--per-shape must be positive")
    report = run_confirmation(args.search.resolve(), args.paths.resolve(), args.per_shape)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "summary": report["summary"], "output": str(args.out)}, indent=2))
    return int(report["status"] != "numerical_consistency_passed")


if __name__ == "__main__":
    raise SystemExit(main())
