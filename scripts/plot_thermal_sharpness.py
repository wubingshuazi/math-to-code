"""Render the recorded thermal perturbations without recomputing experiments."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import LogLocator, NullFormatter, PercentFormatter
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DIRECTION = "generic_complex_orthogonal_tangent"
COLORS = {"2x2": "#2166AC", "2x3": "#D17A22", "3x2": "#237C66", "interior": "#8064A2"}
RESIDUAL_SELECTION = [
    ("2x2", "interior_asymmetric", r"$2\times2$: full row rank"),
    ("2x3", "interior_asymmetric", r"$2\times3$: full row rank"),
    ("3x2", "interior_asymmetric", r"$3\times2$: rank-deficient Gram"),
]
BOUND_SELECTION = [
    ("2x2", "k_zero_maximum_u", r"$2\times2$, balanced $K=0$", COLORS["2x2"]),
    ("2x3", "k_zero_maximum_u", r"$2\times3$, balanced $K=0$", COLORS["2x3"]),
    ("3x2", "k_zero_maximum_u", r"$3\times2$, balanced $K=0$", COLORS["3x2"]),
    ("2x2", "interior_asymmetric", r"$2\times2$, asymmetric interior", COLORS["interior"]),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def path_id(shape: str, regime: str) -> str:
    return f"{shape}__full_rank__{regime}__{DIRECTION}"


def high_precision_points(path: dict | None, panel: str) -> list[dict]:
    points = []
    if path is None:
        return points
    for sample in path["samples"]:
        reference = sample["at_160_digits"]["reference"]
        residual = float(reference["residual_nats"])
        bound = float(reference["pinsker_lower_bound_nats"])
        if residual <= 0.0 or (panel == "bound_fraction" and bound <= 0.0):
            continue
        if not sample["precision_comparison"]["precision_agreement_passed"]:
            raise ValueError(f"Unconfirmed high-precision point: {path['path_id']}")
        points.append({
            "epsilon": float(sample["epsilon_exact_decimal"]),
            "epsilon_exact_decimal": sample["epsilon_exact_decimal"],
            "residual_nats_exact_decimal": reference["residual_nats"],
            "bound_nats_exact_decimal": reference["pinsker_lower_bound_nats"],
            "plot_y": residual if panel == "residual" else bound / residual,
            "dps": 160,
        })
    return sorted(points, key=lambda point: point["epsilon"])


def make_figure(perturbations: Path, high_precision: Path, output: Path, manifest_path: Path) -> dict:
    data = json.loads(perturbations.read_text(encoding="utf-8"))
    paths = {path["path_id"]: path for path in data["paths"]}
    hp_data = json.loads(high_precision.read_text(encoding="utf-8")) if high_precision.exists() else None
    hp_paths = {path["path_id"]: path for path in hp_data["perturbation_paths"]} if hp_data else {}
    selected_hp_source = None
    if hp_data:
        for source in hp_data["source_files"]:
            if source["path"].replace("\\", "/").endswith("thermal_perturbations_selected.json"):
                actual_file = ROOT / source["path"].replace("\\", "/")
                selected_hp_source = {
                    "recorded_sha256": source["sha256"],
                    "actual_sha256": digest(actual_file),
                    "matches": source["sha256"] == digest(actual_file),
                }
                if not selected_hp_source["matches"]:
                    raise ValueError("High-precision replay input hash no longer matches selected perturbation inputs")

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.edgecolor": "#60666C",
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.color": "#41474D",
        "ytick.color": "#41474D",
        "legend.fontsize": 10,
        "legend.frameon": False,
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
        "svg.fonttype": "none",
        "mathtext.fontset": "dejavusans",
    })
    figure, axes = plt.subplots(1, 2, figsize=(16, 7), dpi=100)
    figure.subplots_adjust(left=0.075, right=0.975, bottom=0.235, top=0.845, wspace=0.235)
    figure.suptitle("Local thermal entropy sharpness", x=0.075, y=0.962, ha="left", fontsize=20, fontweight="bold", color="#202A33")
    figure.text(0.075, 0.906, "Normalized generic matrix perturbations  |  recorded float64 evaluations and independent 160-digit replay", fontsize=11, color="#58636E")
    residual_ax, bound_ax = axes
    residual_ax.set_title("(a) Entropy residual near equality", loc="left", pad=13)
    bound_ax.set_title("(b) Fraction captured by the quantitative bound", loc="left", pad=13)

    manifest = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": data["upstream_commit"],
        "inputs": {"perturbations": {"path": str(perturbations.relative_to(ROOT)), "sha256": digest(perturbations)}},
        "high_precision_replay_input_hash": selected_hp_source,
        "figure": {"size_inches": [16, 7], "png_pixels": [1600, 700], "dpi": 100, "matplotlib_version": matplotlib.__version__},
        "residual_panel": {"x_scale": "log", "y_scale": "log", "selected_paths": []},
        "bound_fraction_panel": {"x_scale": "log", "y_scale": "linear", "selected_paths": []},
        "selection_rule": "Prespecified full-rank rectangular X examples, generic complex-HS-orthogonal tangent directions; labels distinguish full-row-rank from rank-deficient XX*",
        "float_filter": "Residual points require positive_resolved and residual>0; ratios additionally require quantitative_bound_resolved and bound/residual>0. Omitted values are never clipped to a positive plotting value.",
        "high_precision_rule": "160-digit reference results with successful 80/160-digit agreement; stored exact decimal strings retained in this manifest",
    }
    if hp_data:
        manifest["inputs"]["high_precision"] = {"path": str(high_precision.relative_to(ROOT)), "sha256": digest(high_precision)}

    resolution_top = max(10.0 * paths[path_id(shape, regime)]["numerical_floor_nats"] for shape, regime, _ in RESIDUAL_SELECTION)
    residual_ax.axhspan(1e-18, resolution_top, facecolor="#E8EBEE", zorder=0)
    residual_ax.axhline(resolution_top, color="#B4BCC4", linewidth=0.8, zorder=1)
    residual_ax.text(0.975, 0.215, "float64 resolution band", transform=residual_ax.transAxes, ha="right", va="center", color="#73808B", fontsize=9)
    for shape, regime, label in RESIDUAL_SELECTION:
        identifier = path_id(shape, regime)
        path = paths[identifier]
        included, omitted = [], []
        for sample in sorted(path["samples"], key=lambda item: item["epsilon"]):
            point = {key: sample[key] for key in ("epsilon", "residual_nats", "numerical_floor_nats")}
            if sample["positive_resolved"] and sample["residual_nats"] > 0.0:
                included.append(point)
            else:
                omitted.append(point | {"reason": "nonpositive_or_at_float_resolution"})
        residual_ax.plot([point["epsilon"] for point in included], [point["residual_nats"] for point in included], color=COLORS[shape], marker="o", markersize=4.5, linewidth=1.8, label=label, zorder=3)
        hp = high_precision_points(hp_paths.get(identifier), "residual")
        if hp:
            residual_ax.plot([point["epsilon"] for point in hp], [point["plot_y"] for point in hp], linestyle="none", marker="D", markersize=7, markerfacecolor="white", markeredgecolor=COLORS[shape], markeredgewidth=1.6, zorder=5)
        manifest["residual_panel"]["selected_paths"].append({
            "path_id": identifier,
            "label": label,
            "float64_points": included,
            "omitted_float64_points": omitted,
            "high_precision_points": hp,
            "recorded_finite_range_slope": path["slope_estimate"],
        })
    reference_x = np.logspace(-8, -1, 100)
    residual_ax.plot(reference_x, 0.5 * reference_x ** 2, linestyle=(0, (5, 3)), color="#727A82", linewidth=1.3, label=r"$0.5\,\varepsilon^2$ reference", zorder=2)
    manifest["residual_panel"]["quadratic_reference"] = {"formula": "0.5*epsilon^2", "epsilon": reference_x.tolist(), "y": (0.5 * reference_x ** 2).tolist()}
    manifest["residual_panel"]["float_resolution_band_top_nats"] = resolution_top
    handles, labels = residual_ax.get_legend_handles_labels()
    if hp_paths:
        handles.append(Line2D([], [], linestyle="none", marker="D", markersize=6.5, markerfacecolor="white", markeredgecolor="#303A43", markeredgewidth=1.4))
        labels.append("160-digit replay")
    residual_ax.legend(handles, labels, loc="upper left", borderaxespad=0.4, labelspacing=0.55)
    residual_ax.set_yscale("log")
    residual_ax.set_ylim(1e-17, 5e-2)
    residual_ax.set_ylabel(r"Residual $R$ (nats)")

    for shape, regime, label, color in BOUND_SELECTION:
        identifier = path_id(shape, regime)
        path = paths[identifier]
        included, omitted = [], []
        for sample in sorted(path["samples"], key=lambda item: item["epsilon"]):
            point = {key: sample[key] for key in ("epsilon", "residual_nats", "quantitative_lower_bound_nats", "quantitative_bound_fraction_of_residual", "numerical_floor_nats")}
            fraction = sample["quantitative_bound_fraction_of_residual"]
            if sample["positive_resolved"] and sample["quantitative_bound_resolved"] and fraction is not None and fraction > 0.0:
                included.append(point)
            else:
                omitted.append(point | {"reason": "unresolved_or_nonpositive_bound_or_residual"})
        bound_ax.plot([point["epsilon"] for point in included], [point["quantitative_bound_fraction_of_residual"] for point in included], color=color, marker="o", markersize=4.5, linewidth=1.8, label=label, zorder=3)
        hp = high_precision_points(hp_paths.get(identifier), "bound_fraction")
        if hp:
            bound_ax.plot([point["epsilon"] for point in hp], [point["plot_y"] for point in hp], linestyle="none", marker="D", markersize=7, markerfacecolor="white", markeredgecolor=color, markeredgewidth=1.6, zorder=5)
        manifest["bound_fraction_panel"]["selected_paths"].append({
            "path_id": identifier,
            "label": label,
            "coefficients_alpha_beta_eta_delta": path["coefficients_alpha_beta_eta_delta"],
            "float64_points": included,
            "omitted_float64_points": omitted,
            "high_precision_points": hp,
        })
    bound_ax.axhline(1.0, color="#A3ABB2", linewidth=1.0, linestyle=(0, (3, 3)), zorder=1)
    bound_ax.set_ylim(0, 1.04)
    bound_ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
    bound_ax.set_ylabel(r"Lower bound / residual $B\,/\,R$")
    bound_ax.legend(loc="center left", bbox_to_anchor=(0.015, 0.55), borderaxespad=0, labelspacing=0.65)
    for ax in axes:
        ax.set_xscale("log")
        ax.set_xlim(7e-9, 0.15)
        ax.set_xlabel(r"Perturbation size $\varepsilon$", labelpad=8)
        ax.xaxis.set_major_locator(LogLocator(base=10, numticks=9))
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.grid(which="major", axis="both", linewidth=0.55, color="#DCE1E5", alpha=0.7)
        ax.tick_params(which="both", direction="out", length=4)
        ax.tick_params(which="minor", length=2)
        ax.set_axisbelow(True)
    caption_lines = [
        r"Generic directions remove radial and global-phase components. The dashed $\varepsilon^2$ curve is a reference; finite-range slopes do not establish an asymptotic law.",
        "Float64 points and ratios at/below their resolution tests are omitted. Open diamonds show 160-digit replay, including positive residuals below the float64 band.",
        r"Asymmetric interior: $(\alpha,\beta,\eta,\delta)=(0.40,0.10,0.15,0.35)$; balanced $K=0$: $(0.25,0.25,0.25,0.25)$. Bounds and residuals use natural-log entropy.",
    ]
    for index, line in enumerate(caption_lines):
        figure.text(0.075, 0.124 - index * 0.038, line, ha="left", va="center", fontsize=10, color="#56616B")
    manifest["caption"] = caption_lines
    manifest["residual_panel"]["axis_limits"] = {"x": [7e-9, 0.15], "y": [1e-17, 5e-2]}
    manifest["bound_fraction_panel"]["axis_limits"] = {"x": [7e-9, 0.15], "y": [0, 1.04]}
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output.with_suffix(".png"), dpi=100)
    figure.savefig(output.with_suffix(".svg"))
    plt.close(figure)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--perturbations", type=Path, default=ROOT / "results/thermal_perturbations.json")
    parser.add_argument("--high-precision", type=Path, default=ROOT / "results/thermal_high_precision.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results/thermal_sharpness")
    parser.add_argument("--manifest", type=Path, default=ROOT / "results/thermal_plot_manifest.json")
    args = parser.parse_args()
    manifest = make_figure(args.perturbations, args.high_precision, args.output, args.manifest)
    print(json.dumps({"outputs": [str(args.output.with_suffix(".png")), str(args.output.with_suffix(".svg")), str(args.manifest)], "input_hashes": manifest["inputs"]}, indent=2))


if __name__ == "__main__":
    main()
