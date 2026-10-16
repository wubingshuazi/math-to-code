"""Record bounded throughput and near-boundary optimizer checks, not speedup claims."""

import json
import math
import os
from pathlib import Path
import platform
import random
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from math_to_code.gad import objective, optimize


def main() -> None:
    rng = random.Random(2762026)
    cases = [(i / 40, j / 40) for i in range(41) for j in range(41)]
    boundary = [0.0, 1e-14, 1e-10, 1e-6, .2, .5, 1 - 1e-6, 1 - 1e-10, 1 - 1e-14, 1.0]
    cases += [(gamma, nu) for gamma in boundary for nu in boundary]
    cases += [(rng.random(), rng.random()) for _ in range(2500)]
    durations = []
    for _ in range(3):
        start = time.perf_counter()
        results = [optimize(gamma, nu) for gamma, nu in cases]
        durations.append(time.perf_counter() - start)
    max_grid_excess = 0.0
    # Different search strategy: an evenly spaced dense grid on a fixed
    # reproducible subset, including the full set of difficult boundaries.
    checked = cases[1681:1781] + cases[1781:1981]
    for gamma, nu in checked:
        value = optimize(gamma, nu).capacity_bits
        grid = max(objective(k / 2048, gamma, nu) for k in range(2049))
        max_grid_excess = max(max_grid_excess, grid - value)
    if max_grid_excess > 1e-12:
        raise AssertionError(f"Independent grid exceeds optimizer: {max_grid_excess}")
    for result in results:
        if not (math.isfinite(result.capacity_bits) and 0 <= result.capacity_bits <= 1
                and 0 <= result.bracket_low <= result.p <= result.bracket_high <= 1):
            raise AssertionError(f"Invalid optimizer result: {result}")
    report = {
        "seed": 2762026,
        "python": platform.python_version(),
        "platform": platform.system(),
        "machine": platform.machine(),
        "logical_cpus_available": os.cpu_count(),
        "parameter_pairs_per_run": len(cases),
        "runs_seconds": durations,
        "median_seconds": statistics.median(durations),
        "dense_grid_comparisons": len(checked),
        "points_per_dense_grid": 2049,
        "max_dense_grid_excess_bits": max_grid_excess,
        "status": "PASS",
        "limitations": "Local wall time only; no comparison with another package or speedup claim. Floating-point consistency is not a proof."
    }
    destination = ROOT / "results" / "benchmark.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
