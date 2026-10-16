"""Dependency-free command line interface."""

import argparse
import csv
import json
import math
from pathlib import Path
from .gad import optimize
from .thermal import gap_lower_bound
from .graphs import GraphSampler, mixing_steps_bound


def main() -> None:
    parser = argparse.ArgumentParser(description="Reproduce selected OpenAI math formulas.")
    commands = parser.add_subparsers(dest="command", required=True)
    gad = commands.add_parser("gad", help="GAD signal optimizer; nu = excited-state population")
    gad.add_argument("--gamma", type=float, required=True)
    gad.add_argument("--nu", type=float, required=True)
    gad.add_argument("--tolerance", type=float, default=1e-10)
    sweep = commands.add_parser("sweep", help="Write a GAD parameter grid as CSV")
    sweep.add_argument("--points", type=int, default=41)
    sweep.add_argument("--output", type=Path, required=True)
    thermal = commands.add_parser("thermal-bound", help="Quantitative thermal entropy gap from Gram trace norm")
    thermal.add_argument("--coefficients", type=float, nargs=4, required=True,
                         metavar=("ALPHA", "BETA", "ETA", "DELTA"))
    thermal.add_argument("--gram-trace-norm", type=float, required=True)
    graphs = commands.add_parser("sample-graphs", help="Degree-preserving labeled network samples")
    graphs.add_argument("--degrees", required=True, help="Comma-separated labeled vertex degrees")
    graphs.add_argument("--backend", choices=("switch", "curveball"), default="curveball")
    graphs.add_argument("--count", type=int, default=10)
    graphs.add_argument("--burn-in", type=int, default=1000)
    graphs.add_argument("--spacing", type=int, default=10)
    graphs.add_argument("--seed", type=int, default=131)
    graphs.add_argument("--output", type=Path, required=True)
    bound_parser = commands.add_parser("graph-bound", help="Conservative source-derived attempted-step bound")
    bound_parser.add_argument("--vertices", type=int, required=True)
    bound_parser.add_argument("--backend", choices=("switch", "curveball"), default="curveball")
    bound_parser.add_argument("--epsilon", type=float, default=.25)
    bound_parser.add_argument("--states", type=int)
    args = parser.parse_args()
    try:
        if args.command == "gad":
            print(json.dumps(optimize(args.gamma, args.nu, args.tolerance).as_dict(), indent=2))
        elif args.command == "thermal-bound":
            bound = gap_lower_bound(args.coefficients, args.gram_trace_norm)
            print(json.dumps({"coefficients_alpha_beta_eta_delta": args.coefficients,
                              "gram_difference_trace_norm": args.gram_trace_norm,
                              "gap_lower_bound_nats": bound,
                              "gap_lower_bound_bits": bound / math.log(2.0)}, indent=2))
        elif args.command == "graph-bound":
            print(json.dumps({"vertices": args.vertices, "backend": args.backend,
                              "total_variation_target": args.epsilon,
                              "conservative_attempted_steps": mixing_steps_bound(
                                  args.vertices, args.epsilon, args.backend, args.states)}, indent=2))
        elif args.command == "sample-graphs":
            degree = tuple(int(token.strip()) for token in args.degrees.split(","))
            sampler = GraphSampler(degree, seed=args.seed, backend=args.backend)
            samples = sampler.sample(args.count, args.burn_in, args.spacing)
            payload = {"degree_vector": degree, "vertex_labels": "0,...,n-1",
                       "state_space": "all simple undirected labeled graphs with the supplied degrees",
                       "burn_in_attempts": args.burn_in, "spacing_attempts": args.spacing,
                       "statistics": sampler.statistics(), "samples": samples}
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"samples": len(samples), "output": str(args.output),
                              **sampler.statistics()}, indent=2))
        else:
            if not 2 <= args.points <= 1001:
                parser.error("--points must be between 2 and 1001")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(["gamma", "nu_excited", "optimal_p", "one_use_holevo_bits"])
                for i in range(args.points):
                    for j in range(args.points):
                        result = optimize(i / (args.points - 1), j / (args.points - 1))
                        writer.writerow([result.gamma, result.nu, result.p, result.capacity_bits])
            print(f"Wrote {args.points ** 2} parameter pairs to {args.output}")
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
