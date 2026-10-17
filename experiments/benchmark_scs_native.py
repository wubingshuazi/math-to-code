"""Isolated A/B screening for same-commit native lazy-scs builds.

New benchmark engineering: 100% GPT-generated. Solver/corpus credit retained.
All timed runs enable the upstream independent lower-bound checker. Python
wall time includes process startup, parsing, solving, checking and output.
Stage profiles are separate runs; their instrumentation is identical in A/B.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
from time import perf_counter_ns

from scs_native_cases import certificate_json, input_digest, validate_result


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=5)
    parser.add_argument('--timeout', type=float, default=60)
    parser.add_argument('--case', action='append', default=[])
    parser.add_argument('--seed', type=int, default=1282026)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('repeats must be positive')
    if args.output.exists() or args.work.exists():
        parser.error('output and work paths must be unused; preserve previous runs')
    args.work.mkdir(parents=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    journal = args.output.with_suffix('.jsonl')
    if journal.exists():
        parser.error('journal already exists')
    journal.touch(exist_ok=False)
    manifest_path = args.inputs / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    cases = [row for row in manifest['cases'] if not args.case or
             any(pattern in row['name'] for pattern in args.case)]
    if not cases:
        parser.error('no cases selected')
    binaries = {'base': args.base.absolute(), 'candidate': args.candidate.absolute()}
    report = {
        'scope': 'native development-set screen, not a general speedup or held-out adoption result',
        'target_commit': manifest['target_commit'],
        'environment': {'python': sys.version, 'platform': platform.platform()},
        'input_manifest_sha256': sha(manifest_path),
        'benchmark_script_sha256': sha(Path(__file__)),
        'input_validator_sha256': sha(Path(__file__).with_name('scs_native_cases.py')),
        'binaries': {name: {'name': path.name, 'sha256': sha(path), 'bytes': path.stat().st_size}
                     for name, path in binaries.items()},
        'repeats': args.repeats, 'seed': args.seed,
        'timing_scope': 'sequential unprofiled process wall time; --verify enabled for both variants',
        'cases': [], 'failures': [],
    }
    rng = random.Random(args.seed)

    def execute(variant: str, row: dict, mode: str, index: int) -> dict:
        source = args.inputs / row['path']
        assert sha(source) == row['file_sha256']
        words = source.read_bytes().splitlines()
        assert len(words) == row['strings'] and input_digest(words) == row['input_sha256']
        output = args.work / f"{row['name']}-{variant}-{mode}-{index}.out"
        env = os.environ.copy()
        env.pop('LAZY_SCS_PROFILE', None)
        if mode != 'unprofiled':
            env['LAZY_SCS_PROFILE'] = mode
        start = perf_counter_ns()
        try:
            completed = subprocess.run([str(binaries[variant]), str(source.absolute()),
                                        '--verify', '-o', str(output.absolute())],
                                       env=env, capture_output=True, timeout=args.timeout)
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(f'{variant} timed out on {row["name"]}') from error
        wall_ns = perf_counter_ns() - start
        if completed.returncode:
            raise RuntimeError(f'{variant} failed on {row["name"]}: {completed.stderr.decode(errors="replace")}')
        certificate = certificate_json(completed.stdout)
        data = output.read_bytes()
        validation = validate_result(words, data, certificate)
        profiles = [json.loads(line) for line in completed.stderr.decode('utf-8').splitlines() if line.strip()]
        if mode == 'unprofiled':
            assert not profiles
        else:
            assert len(profiles) == 1 and profiles[0]['kind'] == 'lazy_scs_stage_profile'
            assert profiles[0]['verify_lower_bound']
        result = {'variant': variant, 'mode': mode, 'index': index, 'wall_ns': wall_ns,
                  'summary': certificate, 'output_sha256': hashlib.sha256(data).hexdigest(),
                  'validation': validation, 'profiles': profiles}
        with journal.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'case': row['name'], **result}) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        return result

    for row in cases:
        entry = {'input': row, 'runs': []}
        try:
            # Profile runs warm both binaries and expose structural distribution.
            for variant in ['base', 'candidate']:
                entry['runs'].append(execute(variant, row, '1', 0))
                entry['runs'].append(execute(variant, row, 'stats', 0))
            for repeat in range(args.repeats):
                order = ['base', 'candidate']
                if rng.randrange(2):
                    order.reverse()
                for variant in order:
                    entry['runs'].append(execute(variant, row, 'unprofiled', repeat))
            baseline = entry['runs'][0]
            stable_keys = {key: value for key, value in baseline['summary'].items()
                           if key not in {'seconds'}}
            for run in entry['runs']:
                assert run['output_sha256'] == baseline['output_sha256'], 'Output bytes differ'
                assert {key: value for key, value in run['summary'].items()
                        if key not in {'seconds'}} == stable_keys, 'Certificate/count values differ'
            medians = {variant: statistics.median(run['wall_ns'] for run in entry['runs']
                                                if run['variant'] == variant and run['mode'] == 'unprofiled')
                       for variant in binaries}
            entry['median_wall_ns'] = medians
            entry['time_reduction_fraction'] = 1 - medians['candidate'] / medians['base']
            entry['all_outputs_and_certificate_values_identical'] = True
            entry['baseline_count_share_of_cli_profile'] = (
                baseline['profiles'][0]['timings_ns']['count'] /
                max(1, baseline['profiles'][0]['timings_ns']['cli_total']))
            print(json.dumps({'case': row['name'], 'base_ms': medians['base'] / 1e6,
                              'candidate_ms': medians['candidate'] / 1e6,
                              'time_reduction_pct': entry['time_reduction_fraction'] * 100,
                              'count_share_pct': entry['baseline_count_share_of_cli_profile'] * 100}), flush=True)
        except Exception as error:
            failure = {'case': row['name'], 'type': type(error).__name__, 'error': str(error)}
            entry['failure'] = failure
            report['failures'].append(failure)
            print(json.dumps(failure), flush=True)
        report['cases'].append(entry)
        args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    report['journal_sha256'] = sha(journal)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    if report['failures']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
