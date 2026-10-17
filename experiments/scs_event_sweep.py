"""Differential toy probe for a lazy-scs step-function aggregation hotspot.

This is a Python model, not a patched Rust solver or an application benchmark.
Source target: nurric-ai/lazy-scs commit 4ee86724b770c54bad400fe077b297288b087c4b,
scs/scs-rs/src/counts.rs::Counts::compute. Original software retains its credit.
New experimental implementation and report: 100% GPT-generated.
"""

from __future__ import annotations

import argparse
from bisect import bisect_right
import hashlib
from itertools import groupby
import json
from pathlib import Path
import platform
import random
import statistics
import sys
from time import perf_counter_ns

# Each table contains (strictly increasing breakpoints, nonnegative values).
Table = tuple[tuple[int, ...], tuple[int, ...]]


def evaluate(table: Table, length: int) -> int:
    starts, values = table
    index = bisect_right(starts, length) - 1
    if index < 0:
        raise ValueError('The step function must be defined at this length.')
    return values[index]


def reference(tables: list[Table], lo: int, hi: int) -> list[tuple[int, int]]:
    """Model the existing breakpoint union and all-successor reevaluation."""
    points = {lo}
    for starts, _ in tables:
        points.update(start - 1 for start in starts if start >= 1 and lo <= start - 1 <= hi)
    return [(length, sum(evaluate(table, length + 1) for table in tables))
            for length in sorted(points)]


def event_sweep(tables: list[Table], lo: int, hi: int) -> list[tuple[int, int]]:
    """Preserve every union breakpoint, updating only changed successors."""
    total = sum(evaluate(table, lo + 1) for table in tables)
    events: list[tuple[int, int]] = []
    for starts, values in tables:
        # Changes exactly at lo are already included in the initial evaluation.
        first = bisect_right(starts, lo + 1)
        stop = bisect_right(starts, hi + 1)
        for index in range(first, stop):
            events.append((starts[index] - 1, values[index] - values[index - 1]))
    events.sort(key=lambda event: event[0])
    result = [(lo, total)]
    for position, batch in groupby(events, key=lambda event: event[0]):
        total += sum(delta for _, delta in batch)
        result.append((position, total))
    return result


def direct_check(tables: list[Table], lo: int, hi: int, result: list[tuple[int, int]]) -> None:
    """Check all integer lengths independently of the reference breakpoint set."""
    reconstructed: Table = (tuple(point for point, _ in result), tuple(value for _, value in result))
    for length in range(lo, hi + 1):
        expected = sum(next(values[i] for i in range(len(starts) - 1, -1, -1)
                            if starts[i] <= length + 1)
                       for starts, values in tables)
        assert evaluate(reconstructed, length) == expected


def correctness(seed: int, count: int) -> dict:
    rng = random.Random(seed)
    boundaries = [
        ([], 1, 1),
        ([((1,), (5,))], 1, 10),
        ([((1, 2, 4), (5, 3, 0)), ((1, 2, 4), (0, 2, 5))], 1, 4),
        ([((0, 2, 3), (9, 7, 7))], 1, 2),
        ([((1, 7, 8), (10, 8, 5))], 6, 6),
    ]
    cases = list(boundaries)
    for _ in range(count):
        lo = rng.randint(1, 8)
        hi = rng.randint(lo, lo + 100)
        tables = []
        for _ in range(rng.randint(0, 32)):
            starts = (1, *sorted(rng.sample(range(2, hi + 5), rng.randint(0, min(20, hi + 3)))))
            values = [rng.randint(0, 1000) for _ in starts]
            if rng.random() < 0.5:
                values.sort(reverse=True)  # The production count functions are nonincreasing.
            tables.append((tuple(starts), tuple(values)))
        cases.append((tables, lo, hi))
    for tables, lo, hi in cases:
        old = reference(tables, lo, hi)
        new = event_sweep(tables, lo, hi)
        assert old == new, (tables, lo, hi, old, new)
        direct_check(tables, lo, hi, new)
    return {'seed': seed, 'random_cases': count, 'boundary_cases': len(boundaries),
            'all_breakpoint_lists_and_integer_length_values_match': True}


def benchmark(seed: int, repeats: int) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for degree, segments in [(1, 128), (4, 8), (4, 64), (16, 32), (64, 32), (128, 64)]:
        lo, hi = 1, 4096
        tables = []
        for _ in range(degree):
            starts = (1, *sorted(rng.sample(range(2, hi + 2), segments - 1)))
            values = sorted((rng.randrange(100000) for _ in starts), reverse=True)
            tables.append((tuple(starts), tuple(values)))
        expected = reference(tables, lo, hi)
        assert event_sweep(tables, lo, hi) == expected
        times: dict[str, list[int]] = {'reference': [], 'event_sweep': []}
        for repeat in range(repeats):
            order = [('reference', reference), ('event_sweep', event_sweep)]
            if repeat % 2:
                order.reverse()
            for name, function in order:
                started = perf_counter_ns()
                actual = function(tables, lo, hi)
                elapsed = perf_counter_ns() - started
                assert actual == expected
                times[name].append(elapsed)
        old_time = statistics.median(times['reference'])
        new_time = statistics.median(times['event_sweep'])
        rows.append({'successors': degree, 'segments_per_successor': segments,
                     'union_breakpoints': len(expected),
                     'reference_step_function_queries': degree * len(expected),
                     'candidate_initial_step_function_queries': degree,
                     'reference_median_ns': old_time, 'event_sweep_median_ns': new_time,
                     'python_model_speed_ratio': old_time / new_time,
                     'raw_times_ns': times})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=1282026)
    parser.add_argument('--random-cases', type=int, default=500)
    parser.add_argument('--repeats', type=int, default=7)
    parser.add_argument('--output', type=Path, default=Path('results/scs_event_sweep_probe.json'))
    args = parser.parse_args()
    if args.random_cases < 0 or args.repeats < 1:
        parser.error('random-cases must be nonnegative and repeats positive')
    report = {
        'scope': 'Python structural toy model; no Rust solver or whole-application speedup established',
        'target_repository': 'https://github.com/nurric-ai/lazy-scs',
        'target_commit': '4ee86724b770c54bad400fe077b297288b087c4b',
        'target_function': 'scs/scs-rs/src/counts.rs::Counts::compute',
        'experimental_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'environment': {'python': sys.version, 'platform': platform.platform()},
        'correctness': correctness(args.seed, args.random_cases),
        'benchmark': benchmark(args.seed, args.repeats),
        'required_next_gate': 'Native Rust patch parity and staged full-solver profiles on representative data',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(args.output), 'correctness': report['correctness'],
                      'toy_speed_ratios': [round(row['python_model_speed_ratio'], 3)
                                           for row in report['benchmark']]}, indent=2))


if __name__ == '__main__':
    main()
