"""Plot finite-state mixing and accepted-only sampling bias."""

import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / "results/graph_audit.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    case = next(item for item in data["cases"] if item["name"] == "six_vertex_two_regular")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [1.5, 1]})
    fig.subplots_adjust(left=.075, right=.97, bottom=.21, top=.78, wspace=.27)
    fig.text(.075, .925, "The sampling clock changes the null model", fontsize=23, weight="bold", color="#1C2933")
    fig.text(.075, .872, "Six labeled vertices, every degree = 2  |  all 70 realizations enumerated", color="#566573")
    for backend, label, color in (("switch", "Paper switch", "#2367A2"), ("curveball", "Curveball", "#14866D")):
        kernel = case["kernels"][backend]
        curve = kernel["trajectory"]
        axes[0].plot([point["step"] for point in curve], [point["worst_tv"] for point in curve],
                     label=label, color=color, linewidth=2.2)
        step = kernel["mixing_steps"]
        value = next(point["worst_tv"] for point in curve if point["step"] == step)
        axes[0].scatter([step], [value], color=color, s=45, zorder=4)
        axes[0].annotate(f"{step} steps", (step, value), xytext=(7, 10), textcoords="offset points", color=color)
    axes[0].axhline(.25, color="#7C8792", linestyle="--", linewidth=1)
    axes[0].text(20, .275, "TV target = 1/4", color="#65727E")
    axes[0].set(title="(a) Worst-start distance from uniform", xlabel="Attempted steps (holds and rejections included)", ylabel="Total-variation distance")
    axes[0].set_ylim(0, 1)
    axes[0].legend(loc="upper right", frameon=False)
    axes[0].grid(alpha=.15)
    bias = data["jump_chain_bias"]
    probabilities = [bias["uniform_two_triangles_probability"]["decimal"], bias["jump_two_triangles_probability"]["decimal"]]
    bars = axes[1].bar([0, 1], probabilities, color=["#2367A2", "#D77A3A"], width=.58)
    axes[1].set_xticks([0, 1], ["All attempted steps\n(correct uniform target)", "Only changed states\n(jump-chain target)"])
    axes[1].set(title="(b) Probability of two disjoint triangles", ylabel="Stationary probability")
    axes[1].set_ylim(0, .25)
    axes[1].yaxis.set_major_formatter(PercentFormatter(1))
    for bar, fraction in zip(bars, ("1/7 = 14.3%", "1/5 = 20.0%")):
        axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + .008,
                     fraction, ha="center", fontsize=12, weight="bold")
    axes[1].grid(axis="y", alpha=.15)
    axes[1].set_axisbelow(True)
    fig.text(.075, .105, "Transition probabilities and stationary identities use exact rational arithmetic; TV curves use the complete finite transition matrices.", fontsize=10, color="#566573")
    empirical = {item["backend"]: item["empirical_two_triangles_probability"] for item in data["empirical_runs"]}
    fig.text(.075, .06, f"Independent 5,000-sample runs: switch {empirical['switch']:.2%}, Curveball {empirical['curveball']:.2%}. Vertex labels and degrees stay fixed.", fontsize=10, color="#566573")
    destination = ROOT / "results/graph_sampling.png"
    fig.savefig(destination, dpi=100)
    fig.savefig(destination.with_suffix(".svg"), metadata={"Date": None})
    plt.close(fig)
    manifest = {"input": "results/graph_audit.json", "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "case": case["name"], "states": case["state_count"],
                "mixing_steps_to_tv_quarter": {backend: value["mixing_steps"] for backend, value in case["kernels"].items()},
                "stationary_two_triangles_probabilities": probabilities,
                "figure": "results/graph_sampling.png", "matplotlib": matplotlib.__version__}
    (ROOT / "results/graph_plot_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
