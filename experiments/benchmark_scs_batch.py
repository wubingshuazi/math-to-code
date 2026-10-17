"""Repeated-case batch throughput for pinned native lazy-scs variants.

New engineering: 100% GPT-generated. Each process solves the SAME case many
times through the existing --batch --verify CLI. Startup is amortized, not
removed. This measures repeated-case throughput, not single-call latency.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
from time import perf_counter_ns

from scs_native_cases import input_digest, native_line_bytes, validate_result


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_batch(data: bytes, words: list[bytes], iterations: int) -> list[tuple[bytes, dict]]:
    """Decode exactly two ASCII output lines per instance without byte loss."""
    data.decode('ascii')
    lines = data.split(b'\n')
    if lines[-1] == b'':
        lines.pop()
    if len(lines) != 2 * iterations:
        raise ValueError(f'expected {2 * iterations} output lines, got {len(lines)}')
    result = []
    for index in range(iterations):
        fields = lines[2 * index].removesuffix(b'\r').split(b' ', 4)
        if len(fields) != 5 or any(not field.isdigit() for field in fields[:4]):
            raise ValueError(f'invalid batch header at instance {index}')
        cert = dict(zip(('W_ext', 'W', 'length', 'rounds'), map(int, fields[:4])))
        cert.update(strings=len(words), input_chars=sum(map(len, words)))
        stats = {}
        for pair in fields[4].decode('ascii').split(',') if fields[4] else []:
            key, separator, value = pair.partition('=')
            if not separator or not key.isidentifier() or not value.isascii() or not value.isdigit():
                raise ValueError(f'invalid statistic {pair!r}')
            if key in stats or key in cert:
                raise ValueError(f'duplicate or reserved statistic {key!r}')
            stats[key] = int(value)
        cert['stats'] = stats
        result.append((lines[2 * index + 1].removesuffix(b'\r'), cert))
    return result


def main() -> None:
    if not __debug__:
        raise SystemExit('Run without -O or PYTHONOPTIMIZE; independent validation must remain enabled.')
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('inputs', 'base', 'candidate', 'output', 'work'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--iterations', type=int, default=20)
    parser.add_argument('--timeout', type=float, default=60)
    parser.add_argument('--case', '--casefilters', action='append', default=[])
    parser.add_argument('--seed', type=int, default=1282026)
    parser.add_argument('--profile', '--warm-profile', action='store_true',
                        help='separate untimed timing-profile batch for each variant before timed runs')
    args = parser.parse_args()
    if args.repeats < 1 or args.iterations < 1 or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('repeats, iterations and finite timeout must be positive')
    journal = args.output.with_suffix('.jsonl')
    if journal == args.output or any(path.exists() for path in (args.output, journal, args.work)):
        parser.error('output (.json), journal and work paths must be unused; previous runs are preserved')
    manifest_path = args.inputs / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    filters = [part for value in args.case for part in value.split(',') if part]
    cases = [row for row in manifest['cases'] if not filters or any(p in row['name'] for p in filters)]
    if not cases:
        parser.error('no cases selected')
    binaries = {'base': args.base.absolute(), 'candidate': args.candidate.absolute()}
    report = {
        'scope': 'repeated-same-case native batch throughput; not single-call latency or independent samples',
        'engineering_attribution': '100% GPT-generated; solver and corpus credit retained',
        'target_commit': manifest['target_commit'], 'environment': {'python': sys.version, 'platform': platform.platform()},
        'script_sha256': sha(Path(__file__)), 'validator_sha256': sha(Path(__file__).with_name('scs_native_cases.py')),
        'input_manifest_sha256': sha(manifest_path),
        'binaries': {name: {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}
                     for name, path in binaries.items()},
        'repeats': args.repeats, 'iterations_per_process': args.iterations,
        'timeout_seconds_per_process': args.timeout, 'seed': args.seed, 'filters': filters,
        'process_wall_scope': 'startup, native batch parsing, cloning, solve, --verify, coverage checks and captured output',
        'checked_wall_scope': 'process wall plus raw-capture preservation, Python parsing and every independent result check; excludes journal fsync',
        'profile_batches_excluded_from_medians': True, 'cases': [], 'failures': [],
    }
    args.work.mkdir(parents=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    journal.touch(exist_ok=False)
    rng = random.Random(args.seed)

    def log(record: dict) -> None:
        with journal.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(record, sort_keys=True) + '\n')
            stream.flush()
            os.fsync(stream.fileno())

    def execute(variant: str, case_index: int, row: dict, words: list[bytes], batch: Path,
                mode: str, repeat: int, reference: list) -> dict:
        stem = args.work / f'case-{case_index:03}-{variant}-{mode}-{repeat}'
        stdout_path, stderr_path = stem.with_suffix('.stdout'), stem.with_suffix('.stderr')
        env = os.environ.copy()
        env.pop('LAZY_SCS_PROFILE', None)
        if mode == 'profile':
            env['LAZY_SCS_PROFILE'] = '1'
        record = {'case': row['name'], 'variant': variant, 'mode': mode, 'repeat': repeat,
                  'iterations': args.iterations, 'stdout_path': str(stdout_path), 'stderr_path': str(stderr_path)}
        start = perf_counter_ns()
        try:
            try:
                proc = subprocess.run([str(binaries[variant]), str(batch.absolute()), '--batch', '--verify'],
                                      env=env, capture_output=True, timeout=args.timeout)
            except subprocess.TimeoutExpired as error:
                record['process_wall_ns'] = perf_counter_ns() - start
                stdout_path.write_bytes(error.stdout or b'')
                stderr_path.write_bytes(error.stderr or b'')
                record['timed_out'] = True
                raise
            record.update(process_wall_ns=perf_counter_ns() - start, returncode=proc.returncode)
            stdout_path.write_bytes(proc.stdout)
            stderr_path.write_bytes(proc.stderr)
            if proc.returncode:
                raise ValueError(f'process returned {proc.returncode}; raw stderr preserved')
            instances = []
            for index, (output, cert) in enumerate(parse_batch(proc.stdout, words, args.iterations)):
                validation = validate_result(words, output, cert)
                if not reference:
                    reference.append((output, cert))
                if (output, cert) != reference[0]:
                    raise ValueError(f'output bytes or non-timing certificate differ at instance {index}')
                instances.append({'certificate': cert, 'validation': validation})
            profiles = [json.loads(line) for line in proc.stderr.decode('utf-8').splitlines() if line.strip()]
            if mode == 'profile':
                if len(profiles) != args.iterations or any(
                    p.get('kind') != 'lazy_scs_stage_profile' or p.get('schema_version') != 1
                    or p.get('instance_index') != i or not p.get('verify_lower_bound')
                    for i, p in enumerate(profiles)
                ):
                    raise ValueError('missing or invalid per-instance timing profiles')
            elif profiles:
                raise ValueError('timed process unexpectedly emitted profiling/stderr data')
            record.update(status='passed', checked_wall_ns=perf_counter_ns() - start,
                          instances=instances, profiles=profiles, stdout_sha256=sha(stdout_path),
                          stderr_sha256=sha(stderr_path), all_outputs_and_certificates_identical=True)
        except Exception as error:
            record.update(status='failed', checked_wall_ns=perf_counter_ns() - start,
                          failure={'type': type(error).__name__, 'error': str(error)})
        for name, path in (('stdout', stdout_path), ('stderr', stderr_path)):
            if path.exists():
                record[name + '_sha256'] = sha(path)
        log(record)
        return record

    log({'event': 'start', **{key: value for key, value in report.items() if key != 'cases'}})
    for case_index, row in enumerate(cases):
        entry = {'input': row, 'runs': []}
        try:
            source = args.inputs / row['path']
            raw = source.read_bytes()
            raw.decode('ascii')  # Lossy UTF-8 output is unsuitable for byte-equivalence claims.
            words = raw.split(b'\n')
            if words[-1] == b'':
                words.pop()
            words = [word.removesuffix(b'\r') for word in words]
            if not words or sha(source) != row['file_sha256'] or input_digest(words) != row['input_sha256']:
                raise ValueError('input hash mismatch or empty case')
            if len(words) != row['strings'] or sum(map(len, words)) != row['input_chars']:
                raise ValueError('input manifest dimensions do not match source')
            block = native_line_bytes(words)  # Rejects FASTA, separator, whitespace and empty records.
            batch = args.work / f'case-{case_index:03}.batch.txt'
            with batch.open('xb') as stream:
                stream.write(b'---\n'.join([block] * args.iterations))
            entry.update(batch_sha256=sha(batch), batch_file_bytes=batch.stat().st_size)
            # Across timed repeats, AB and BA counts differ by at most one.
            orders = [['base', 'candidate'], ['candidate', 'base']] * (args.repeats // 2)
            if args.repeats % 2:
                orders.append(rng.sample(['base', 'candidate'], 2))
            rng.shuffle(orders)
            entry['timed_order'] = orders
            reference = []
            schedule = [('profile', 0, ['base', 'candidate'])] if args.profile else []
            schedule += [('timed', i, order) for i, order in enumerate(orders)]
            for mode, repeat, order in schedule:
                for variant in order:
                    run = execute(variant, case_index, row, words, batch, mode, repeat, reference)
                    entry['runs'].append(run)
                    if run['status'] != 'passed':
                        raise ValueError(f'{variant}/{mode}/{repeat}: {run["failure"]}')
            for metric in ('process_wall_ns', 'checked_wall_ns'):
                medians = {v: statistics.median(r[metric] for r in entry['runs']
                           if r['variant'] == v and r['mode'] == 'timed') for v in binaries}
                entry['median_' + metric] = medians
                entry['amortized_median_' + metric + '_per_instance'] = {v: t / args.iterations for v, t in medians.items()}
                entry[metric + '_reduction_fraction'] = 1 - medians['candidate'] / medians['base']
            entry['all_outputs_and_certificate_values_identical'] = True
        except Exception as error:
            failure = {'case': row['name'], 'type': type(error).__name__, 'error': str(error)}
            entry['failure'] = failure
            report['failures'].append(failure)
            log({'event': 'case_failure', **failure})
        report['cases'].append(entry)
        args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'case': row['name'], 'failed': 'failure' in entry,
                          'process_wall_reduction': entry.get('process_wall_ns_reduction_fraction')}), flush=True)
    report['journal_sha256'] = sha(journal)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    if report['failures']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
