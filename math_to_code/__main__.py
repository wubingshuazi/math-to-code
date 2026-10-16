"""Dependency-free command line interface."""

import argparse
import csv
import json
from pathlib import Path
from .gad import optimize


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
    args = parser.parse_args()
    try:
        if args.command == "gad":
            print(json.dumps(optimize(args.gamma, args.nu, args.tolerance).as_dict(), indent=2))
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
