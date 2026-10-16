"""Independent labeled-state and rational-kernel audit for graph samplers."""

from __future__ import annotations

import argparse
from collections import Counter, deque
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
from itertools import combinations, permutations
import json
import math
from pathlib import Path
import platform
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from math_to_code.graphs import GraphSampler, mixing_steps_bound  # noqa: E402

ZERO, ONE = Fraction(0), Fraction(1)
PIN = "1581d4cbdd69a0faf34b2089614fe2a814316a6a"


def enumerate_realizations(degrees, max_states=105):
    """Enumerate labeled realizations by fixing each vertex's future edges.

    This does not use the production Havel-Hakimi implementation. Each
    simple graph is generated once; residual-degree pruning avoids the full
    2**binom(n,2) adjacency-mask scan.
    """
    degree = tuple(degrees)
    n = len(degree)
    if any(type(value) is not int or value < 0 or value >= n for value in degree) or sum(degree) % 2:
        return []
    states = []

    def visit(vertex, remaining, edges):
        if vertex == n:
            if not any(remaining):
                states.append(tuple(edges))
                if len(states) > max_states:
                    raise ValueError(f"state cap {max_states} exceeded")
            return
        needed = remaining[vertex]
        available = [other for other in range(vertex + 1, n) if remaining[other] > 0]
        if needed > len(available):
            return
        for chosen in combinations(available, needed):
            next_remaining = list(remaining)
            next_remaining[vertex] = 0
            for other in chosen:
                next_remaining[other] -= 1
            if any(value < 0 or value > n - vertex - 2 for value in next_remaining[vertex + 1:]):
                continue
            visit(vertex + 1, next_remaining, edges + [(vertex, other) for other in chosen])

    visit(0, list(degree), [])
    return sorted(states)


def four_matchings(vertices):
    a, b, c, d = vertices
    return (((a, b), (c, d)), ((a, c), (b, d)), ((a, d), (b, c)))


def singleton_choices(n, graph, pair):
    first, second = pair
    only_first, pool = [], []
    for vertex in range(n):
        if vertex in pair:
            continue
        first_edge = tuple(sorted((first, vertex)))
        second_edge = tuple(sorted((second, vertex)))
        left, right = first_edge in graph, second_edge in graph
        if left != right:
            pool.append(vertex)
            if left:
                only_first.append(vertex)
    return pool, len(only_first)


def switch_kernel(n, states):
    """Exact paper kernel: half-hold, uniform four-set, six ordered pairs."""
    lookup = {state: index for index, state in enumerate(states)}
    matrix = [[ZERO] * len(states) for _ in states]
    if n < 4:
        for index in range(len(states)):
            matrix[index][index] = ONE
        return matrix
    probability = Fraction(1, 12 * math.comb(n, 4))
    for index, state in enumerate(states):
        graph = frozenset(state)
        matrix[index][index] += Fraction(1, 2)
        for vertices in combinations(range(n), 4):
            for old, new in permutations(four_matchings(vertices), 2):
                if all(edge in graph for edge in old) and all(edge not in graph for edge in new):
                    target = tuple(sorted((graph - set(old)) | set(new)))
                else:
                    target = state
                matrix[index][lookup[target]] += probability
    return matrix


def curveball_kernel(n, states):
    """Exact heat bath: average every pair and every feasible q-subset."""
    lookup = {state: index for index, state in enumerate(states)}
    matrix = [[ZERO] * len(states) for _ in states]
    if n < 2:
        for index in range(len(states)):
            matrix[index][index] = ONE
        return matrix
    for index, state in enumerate(states):
        graph = frozenset(state)
        for pair in combinations(range(n), 2):
            pool, size = singleton_choices(n, graph, pair)
            probability = Fraction(1, math.comb(n, 2) * math.comb(len(pool), size))
            fixed = {edge for edge in graph if not any(endpoint in pair and other in pool for endpoint, other in (edge, edge[::-1]))}
            for subset in combinations(pool, size):
                assigned_first = set(subset)
                added = {tuple(sorted((pair[0] if vertex in assigned_first else pair[1], vertex))) for vertex in pool}
                target = tuple(sorted(fixed | added))
                matrix[index][lookup[target]] += probability
    return matrix


def exact_checks(matrix):
    size = len(matrix)
    rows = all(sum(row, ZERO) == ONE for row in matrix)
    columns = all(sum((matrix[i][j] for i in range(size)), ZERO) == ONE for j in range(size))
    symmetric = all(matrix[i][j] == matrix[j][i] for i in range(size) for j in range(size))
    nonnegative = all(value >= 0 for row in matrix for value in row)
    reached, queue = {0}, deque([0])
    while queue:
        source = queue.popleft()
        for target, probability in enumerate(matrix[source]):
            if probability > 0 and target not in reached:
                reached.add(target)
                queue.append(target)
    return {"row_sums_exactly_one": rows, "column_sums_exactly_one": columns, "symmetric_exactly": symmetric, "nonnegative_exactly": nonnegative, "connected_transition_support": len(reached) == size, "uniform_stationarity_exactly": columns}


def rational_encoding(matrix):
    denominator = math.lcm(*(value.denominator for row in matrix for value in row))
    return {"common_denominator": denominator, "integer_numerators": [[int(value * denominator) for value in row] for row in matrix]}


def mixing_trajectory(matrix, threshold=0.25, max_steps=5000):
    numeric = np.array([[float(value) for value in row] for row in matrix])
    size = len(matrix)
    eigenvalues = np.linalg.eigvalsh(numeric)
    power = np.eye(size)
    trajectory = []
    for step in range(max_steps + 1):
        tv = np.abs(power - 1.0 / size).sum(axis=1) * 0.5
        worst = int(np.argmax(tv))
        distance = float(tv[worst])
        trajectory.append({"step": step, "worst_tv": distance, "worst_start_index": worst})
        if distance <= threshold:
            return {"tv_arithmetic": "binary64 matrix powers on an exactly constructed rational transition matrix", "threshold": threshold, "mixing_steps": step, "trajectory": trajectory, "minimum_eigenvalue": float(eigenvalues[0]), "spectral_gap": None if size == 1 else float(1.0 - eigenvalues[-2]), "limit_reached": False}
        power = power @ numeric
    return {"tv_arithmetic": "binary64", "threshold": threshold, "mixing_steps": None, "trajectory": trajectory, "minimum_eigenvalue": float(eigenvalues[0]), "spectral_gap": None if size == 1 else float(1.0 - eigenvalues[-2]), "limit_reached": True}


class ScriptedSwitchRandom:
    def __init__(self, hold, vertices=(), first=0, second=1):
        self.hold, self.vertices = hold, vertices
        self.indices = iter((first, second - int(second > first)))

    def getrandbits(self, bits):
        assert bits == 1
        return int(not self.hold)

    def sample(self, population, count):
        assert count == 4
        return list(self.vertices)

    def randrange(self, limit):
        result = next(self.indices)
        assert 0 <= result < limit
        return result


class ScriptedCurveballRandom:
    def __init__(self, pair, pool, subset):
        self.pair, self.pool, self.subset = pair, pool, subset
        self.calls = 0

    def sample(self, population, count):
        self.calls += 1
        if self.calls == 1:
            assert count == 2
            return list(self.pair)
        assert list(population) == self.pool and count == len(self.subset)
        return list(self.subset)


def scripted_core_row(degrees, state, backend):
    """Enumerate actual production steps by supplying each random outcome.

    This test hook checks proposal probabilities and identity clocks, not
    just whether empirical samples eventually have the expected frequency.
    """
    n, row = len(degrees), Counter()

    def perform(random_source, weight):
        sampler = GraphSampler(degrees, backend=backend, edges=state)
        sampler._random = random_source
        changed = sampler.step()
        assert sampler.attempts == 1
        assert sampler.changes == int(changed)
        assert changed == (sampler.edges != state)
        row[sampler.edges] += weight

    if backend == "switch":
        if n < 4:
            perform(ScriptedSwitchRandom(True), ONE)
        else:
            perform(ScriptedSwitchRandom(True), Fraction(1, 2))
            weight = Fraction(1, 12 * math.comb(n, 4))
            for vertices in combinations(range(n), 4):
                for first, second in permutations(range(3), 2):
                    perform(ScriptedSwitchRandom(False, vertices, first, second), weight)
    else:
        if n < 2:
            perform(ScriptedCurveballRandom((), [], ()), ONE)
        else:
            for pair in combinations(range(n), 2):
                pool, count = singleton_choices(n, frozenset(state), pair)
                weight = Fraction(1, math.comb(n, 2) * math.comb(len(pool), count))
                for subset in combinations(pool, count):
                    perform(ScriptedCurveballRandom(pair, pool, subset), weight)
    return row


def triangle_count(state, n):
    graph = frozenset(state)
    return sum(all(edge in graph for edge in combinations(triple, 2)) for triple in combinations(range(n), 3))


def fraction_record(value):
    return {"fraction": str(value), "numerator": value.numerator, "denominator": value.denominator, "decimal": float(value)}


def jump_chain_audit(states, switch):
    neighbors = [sum(probability > 0 for target, probability in enumerate(row) if source != target) for source, row in enumerate(switch)]
    triangle_counts = [triangle_count(state, 6) for state in states]
    total_degree = sum(neighbors)
    uniform = [Fraction(1, len(states))] * len(states)
    jump = [Fraction(count, total_degree) for count in neighbors]
    triangle_event = [index for index, count in enumerate(triangle_counts) if count == 2]
    uniform_mass = sum((uniform[index] for index in triangle_event), ZERO)
    jump_mass = sum((jump[index] for index in triangle_event), ZERO)
    uniform_mean = sum((weight * count for weight, count in zip(uniform, triangle_counts)), ZERO)
    jump_mean = sum((weight * count for weight, count in zip(jump, triangle_counts)), ZERO)
    groups = Counter(zip(triangle_counts, neighbors))
    balance = all(jump[i] / neighbors[i] == jump[j] / neighbors[j] for i in range(len(states)) for j in range(len(states)) if i != j and switch[i][j] > 0)
    return {"arithmetic": "exact fractions", "state_groups": [{"triangle_count": triangles, "switch_neighbors": degree, "states": count} for (triangles, degree), count in sorted(groups.items())], "jump_detailed_balance_exactly": balance, "uniform_two_triangles_probability": fraction_record(uniform_mass), "jump_two_triangles_probability": fraction_record(jump_mass), "uniform_expected_triangles": fraction_record(uniform_mean), "jump_expected_triangles": fraction_record(jump_mean), "per_state_switch_neighbor_counts": neighbors, "per_state_triangle_counts": triangle_counts, "expected_identities_hold": uniform_mass == Fraction(1, 7) and jump_mass == Fraction(1, 5) and uniform_mean == Fraction(2, 7) and jump_mean == Fraction(2, 5) and groups == Counter({(0, 12): 60, (2, 18): 10})}


def empirical_audit(states, backend, count, seed):
    degrees = (2,) * 6
    lookup = {state: index for index, state in enumerate(states)}
    burn = mixing_steps_bound(6, .01, backend, states=len(states))
    sampler = GraphSampler(degrees, backend=backend, seed=seed)
    initial = sampler.edges
    frequency = [0] * len(states)
    for state in sampler.sample(count, burn_in=burn, spacing=10):
        if state not in lookup:
            raise ValueError("production sample left the independently enumerated state space")
        frequency[lookup[state]] += 1
    empirical_tv = sum(abs(value / count - 1.0 / len(states)) for value in frequency) * .5
    observed_triangle_mass = sum(value for state, value in zip(states, frequency) if triangle_count(state, 6) == 2) / count
    return {"backend": backend, "seed": seed, "sample_count": count, "burn_in_attempts": burn, "burn_in_target_epsilon": .01, "spacing_attempts": 10, "initial_edges": initial, "state_frequencies": frequency, "empirical_tv_from_uniform": empirical_tv, "empirical_two_triangles_probability": observed_triangle_mass, "uniform_two_triangles_probability": fraction_record(Fraction(1, 7)), "statistics": sampler.statistics(), "frequency_checks_passed": sum(frequency) == count and sampler.attempts == burn + count * 10, "interpretation": "Finite correlated trajectory; empirical TV describes this histogram, not a certificate of mixing or independent samples."}


def run(output, empirical_samples=5000, seed=20261017, max_steps=5000):
    started = time.perf_counter()
    source_dir = ROOT / "research" / "graph131"
    manifest = json.loads((source_dir / "sources.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        if hashlib.sha256((source_dir / entry["file"]).read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"source hash mismatch: {entry['file']}")
    cases = [("four_vertex_matchings", (1,) * 4, 3), ("six_vertex_two_regular", (2,) * 6, 70), ("six_vertex_matchings", (1,) * 6, 15), ("five_vertex_cycles", (2,) * 5, 12), ("empty_graph", (0,) * 5, 1), ("complete_graph", (4,) * 5, 1), ("labeled_star", (3, 1, 1, 1), 1), ("two_vertices", (1, 1), 1), ("zero_vertices", (), 1)]
    records, violations, empirical = [], [], []
    jump_result = None
    checked_core_rows = 0
    for name, degrees, expected_count in cases:
        states = enumerate_realizations(degrees)
        if len(states) != expected_count:
            raise ValueError(f"independent state-count mismatch for {name}")
        record = {"name": name, "degrees": list(degrees), "state_count": len(states), "expected_state_count": expected_count, "states": states, "kernels": {}}
        for backend, build in (("switch", switch_kernel), ("curveball", curveball_kernel)):
            matrix = build(len(degrees), states)
            checks = exact_checks(matrix)
            mixing = mixing_trajectory(matrix, max_steps=max_steps)
            lower_gap = None if len(states) == 1 else (Fraction(1, math.comb(len(degrees), 2)) if backend == "curveball" else Fraction(1, 24 * len(degrees) ** 2 * math.comb(len(degrees), 4)))
            indices = range(len(states)) if len(states) <= 3 else (0, len(states) - 1)
            core_exact = True
            for index in indices:
                actual = scripted_core_row(degrees, states[index], backend)
                reference = {state: matrix[index][target] for target, state in enumerate(states) if matrix[index][target]}
                core_exact &= actual == reference
                checked_core_rows += 1
            theoretical_bound = mixing_steps_bound(len(degrees), .25, backend, states=len(states))
            spectral_ok = lower_gap is None or mixing["spectral_gap"] + 1e-12 >= float(lower_gap)
            psd_ok = mixing["minimum_eigenvalue"] >= -1e-12
            expected_mix = (4 if backend == "switch" else 2) if name == "four_vertex_matchings" else (0 if len(states) == 1 else None)
            passed = all(checks.values()) and core_exact and spectral_ok and psd_ok and not mixing["limit_reached"] and (expected_mix is None or mixing["mixing_steps"] == expected_mix)
            record["kernels"][backend] = {"exact_checks": checks, "production_scripted_rows_match_exactly": core_exact, "production_rows_checked": list(indices), "rational_transition": rational_encoding(matrix), "spectral_gap_lower_bound": None if lower_gap is None else fraction_record(lower_gap), "spectral_bound_passed": spectral_ok, "positive_semidefinite_numeric_check_passed": psd_ok, "source_derived_attempt_bound_to_tv_quarter": theoretical_bound, "expected_closed_form_mixing_steps": expected_mix, **mixing, "checks_passed": passed}
            if not passed:
                violations.append({"case": name, "backend": backend})
            if name == "six_vertex_two_regular" and backend == "switch":
                jump_result = jump_chain_audit(states, matrix)
                if not jump_result["expected_identities_hold"] or not jump_result["jump_detailed_balance_exactly"]:
                    violations.append({"case": name, "check": "jump_chain_exact_identities"})
            if name == "six_vertex_two_regular" and empirical_samples:
                item = empirical_audit(states, backend, empirical_samples, seed + int(backend == "curveball"))
                empirical.append(item)
                if not item["frequency_checks_passed"]:
                    violations.append({"case": name, "backend": backend, "check": "empirical_counts"})
        records.append(record)
    result = {"schema_version": 1, "title": "Independent exact-state audit of degree-preserving graph kernels", "status": "checks_passed" if not violations else "check_failure", "created_utc": datetime.now(timezone.utc).isoformat(), "source_commit": PIN, "source_manifest": "research/graph131/sources.json", "source_manifest_sha256": hashlib.sha256((source_dir / "sources.json").read_bytes()).hexdigest(), "reproducibility": {"python": platform.python_version(), "numpy": np.__version__, "platform": platform.platform(), "empirical_seed": seed, "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "production_graphs_sha256": hashlib.sha256((ROOT / "math_to_code" / "graphs.py").read_bytes()).hexdigest(), "command": f"python scripts/audit_graphs.py --empirical-samples {empirical_samples} --seed {seed} --output results/graph_audit.json"}, "summary": {"degree_vectors": len(records), "kernel_matrices": 2 * len(records), "production_transition_rows_checked_exactly": checked_core_rows, "total_labeled_states_across_cases": sum(record["state_count"] for record in records), "violation_count": len(violations), "wall_seconds": time.perf_counter() - started}, "arithmetic": {"enumeration": "independent residual-degree-pruned labeled enumeration", "transition_and_stationarity": "exact Python Fraction arithmetic", "tv_and_eigenvalues": "binary64 NumPy; thresholds are numerically evaluated", "jump_chain_bias": "exact Python Fraction arithmetic"}, "cases": records, "jump_chain_bias": jump_result, "empirical_runs": empirical, "violations": violations}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "graph_audit.json")
    parser.add_argument("--empirical-samples", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20261017)
    parser.add_argument("--max-steps", type=int, default=5000)
    args = parser.parse_args()
    if args.empirical_samples < 0 or not 1 <= args.max_steps <= 5000:
        parser.error("empirical samples must be nonnegative and max steps in [1,5000]")
    result = run(args.output, args.empirical_samples, args.seed, args.max_steps)
    print(json.dumps({"status": result["status"], "summary": result["summary"], "empirical_tv": {item["backend"]: item["empirical_tv_from_uniform"] for item in result["empirical_runs"]}, "output": str(args.output)}, indent=2))
    return int(bool(result["violations"]))


if __name__ == "__main__":
    raise SystemExit(main())
