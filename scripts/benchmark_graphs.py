"""Measure the two graph kernels on equal attempted-step budgets."""

import json
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from math_to_code.graphs import GraphSampler


def triangle_count(n, edges):
    neighbors = [set() for _ in range(n)]
    for u, v in edges:
        neighbors[u].add(v)
        neighbors[v].add(u)
    return sum(len(neighbors[u] & neighbors[v]) for u, v in edges) // 3


def main():
    attempts = 20000
    records = []
    for n, degree in ((16, 4), (32, 4), (64, 4), (128, 6)):
        for backend in ("switch", "curveball"):
            sampler = GraphSampler((degree,) * n, seed=1312026, backend=backend)
            initial_triangles = triangle_count(n, sampler.edges)
            start = time.perf_counter()
            sampler.advance(attempts)
            elapsed = time.perf_counter() - start
            observed = [0] * n
            for u, v in sampler.edges:
                observed[u] += 1
                observed[v] += 1
            if observed != [degree] * n:
                raise AssertionError("degree invariant failed")
            record = {**sampler.statistics(), "regular_degree": degree,
                      "seconds": elapsed, "attempts_per_second": attempts / elapsed,
                      "changes_per_second": sampler.changes / elapsed,
                      "initial_triangle_count": initial_triangles,
                      "final_triangle_count": triangle_count(n, sampler.edges),
                      "degree_invariant": True}
            records.append(record)
    report = {"experiment": "Graph-kernel execution benchmark",
              "python": platform.python_version(), "platform": platform.system(),
              "attempts_per_case": attempts, "cases": records,
              "interpretation": "Equal proposal counts measure execution and movement rates, not equal distributional accuracy. Exact small-state TV comparisons are in graph_audit.json."}
    destination = ROOT / "results/graph_benchmark.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
