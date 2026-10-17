"""Check native lazy-scs outputs with independent tiny exact-SCS oracles.

New engineering: 100% GPT-generated. Solver authorship and MIT credit remain
with nurric-ai/lazy-scs. This finite correctness check makes no timing claim.
Empty instances and binary/unrepresentable lines are recorded as skipped;
empty words in mixed instances are removed explicitly, preserving optimum.
The Rust unit tests cover the broader byte-array/empty-pattern trim contract.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

from scs_native_cases import (
    SOLVER_COMMIT,
    TinyCase,
    certificate_json,
    exact_optimal_length,
    input_digest,
    native_line_bytes,
    self_test as generator_self_test,
    tiny_cases,
    validate_result,
)


@dataclass(frozen=True)
class NativeCase:
    original: TinyCase
    words: tuple[bytes, ...]
    serialized: bytes
    removed_empty_words: int


def select_native_cases(cases: list[TinyCase]) -> tuple[list[NativeCase], list[dict]]:
    selected = []
    skipped = []
    for case in cases:
        words = tuple(word for word in case.strings if word)
        if not words:
            skipped.append({
                'case': case.name,
                'reason': 'empty instance: pinned upstream CLI emits malformed empty-stats JSON',
                'original_strings': len(case.strings),
            })
            continue
        try:
            serialized = native_line_bytes(words)
        except ValueError as error:
            skipped.append({'case': case.name, 'reason': str(error),
                            'original_strings': len(case.strings)})
            continue
        # Preserve the generated mathematical instance while making its CLI
        # representation explicit. Do not turn binary/FASTA/whitespace cases
        # into a different input by decoding, stripping or replacing bytes.
        if exact_optimal_length(words) != case.expected_optimal:
            raise ValueError(f'{case.name}: CLI filtering changed the exact optimum')
        if serialized.split(b'\n')[:-1] != list(words):
            raise ValueError(f'{case.name}: native line serialization changed bytes')
        selected.append(NativeCase(case, words, serialized, len(case.strings) - len(words)))
    return selected, skipped


def self_test() -> dict:
    generated = generator_self_test()
    selected, skipped = select_native_cases(tiny_cases(random_cases=0))
    if {case['case'] for case in skipped} != {'empty', 'only_empty', 'binary_only'}:
        raise AssertionError('native selection did not explicitly exclude incompatible fixed cases')
    duplicate_case = next(case for case in selected if case.original.name == 'duplicates_containment')
    if duplicate_case.removed_empty_words != 1 or any(not word for word in duplicate_case.words):
        raise AssertionError('mixed empty word was not explicitly removed')
    bad_words = [b'A\nB', b'A\rB', b'>FASTA', b'---', b' A', b'A ', b'\xff']
    bad_cases = [TinyCase(f'unsafe_line_{i}', (word,), len(word))
                 for i, word in enumerate(bad_words)]
    accepted, rejected = select_native_cases(bad_cases)
    if accepted or len(rejected) != len(bad_words):
        raise AssertionError('unsafe native line was silently accepted')
    return {'generator': generated, 'compatible_fixed_cases': len(selected),
            'excluded_fixed_cases': len(skipped), 'rejected_unsafe_lines': len(rejected),
            'mixed_empty_word_removal_checked': True}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_case(case: NativeCase, binaries: dict[str, Path], work: Path, timeout: float) -> dict:
    source = work / f'{case.original.name}.txt'
    source.write_bytes(case.serialized)
    env = os.environ.copy()
    env.pop('LAZY_SCS_PROFILE', None)
    env.pop('SCS_RECORD_ORDER', None)
    outputs = {}
    certificates = {}
    validations = {}
    for variant, binary in binaries.items():
        output = work / f'{case.original.name}-{variant}.out'
        command = [str(binary), str(source), '--check', '--verify', '-o', str(output)]
        completed = subprocess.run(command, capture_output=True, env=env, timeout=timeout)
        if completed.returncode:
            message = completed.stderr.decode('utf-8', errors='replace')[:12000]
            raise RuntimeError(f'{case.original.name}/{variant} exited {completed.returncode}: {message}')
        data = output.read_bytes()
        certificate = certificate_json(completed.stdout)
        validation = validate_result(case.words, data, certificate,
                                     require_verified=True, check_optimum=True)
        if validation.get('exact_optimal_length') != case.original.expected_optimal:
            raise ValueError(f'{case.original.name}/{variant}: exact-oracle mismatch')
        outputs[variant] = data
        # Execution seconds are the only unstable native summary field. Counts,
        # independent-checker outcomes, rounds and reported ratios must match.
        certificates[variant] = {key: value for key, value in certificate.items() if key != 'seconds'}
        validations[variant] = validation
    if outputs['base'] != outputs['candidate']:
        raise ValueError(f'{case.original.name}: output bytes differ')
    if certificates['base'] != certificates['candidate']:
        raise ValueError(f'{case.original.name}: certificate values differ')
    return {
        'case': case.original.name,
        'original_inputs_hex': [word.hex() for word in case.original.strings],
        'native_inputs_hex': [word.hex() for word in case.words],
        'original_input_sha256': input_digest(case.original.strings),
        'native_input_sha256': input_digest(case.words),
        'removed_empty_words': case.removed_empty_words,
        'exact_optimal_length': case.original.expected_optimal,
        'common_output_hex': outputs['base'].hex(),
        'common_certificate_without_seconds': certificates['base'],
        'validation': validations,
        'outputs_and_certificate_values_identical': True,
    }


def main() -> None:
    if sys.flags.optimize:
        raise SystemExit('Run without Python -O: generator/oracle checks require assertions enabled.')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path)
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--random-cases', type=int, default=24)
    parser.add_argument('--seed', type=int, default=1282026)
    parser.add_argument('--timeout', type=float, default=30.0, help='seconds per native process')
    parser.add_argument('--self-test', action='store_true', help='also permits generator/selection checks without binaries')
    args = parser.parse_args()
    if args.random_cases < 0 or args.seed < 0:
        parser.error('random-cases and seed must be nonnegative')
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('timeout must be finite and positive')
    if (args.base is None) != (args.candidate is None):
        parser.error('provide both --base and --candidate')
    if args.base is None and not args.self_test:
        parser.error('provide both binaries or --self-test')
    if args.output is not None and args.output.exists():
        parser.error('output already exists; preserve previous check reports')

    report = {
        'schema_version': 1,
        'scope': 'finite native correctness and exact tiny-case checks; no performance thresholds',
        'target_repository': 'https://github.com/nurric-ai/lazy-scs',
        'target_commit': SOLVER_COMMIT,
        'new_engineering': '100% GPT-generated; original implementation retains upstream credit',
        'environment': {'python': sys.version, 'platform': platform.platform()},
        'checker_script_sha256': digest(Path(__file__)),
        'generator_script_sha256': digest(Path(__file__).with_name('scs_native_cases.py')),
        'self_tests': self_test(),
        'native_flags': ['--check', '--verify'],
        'seed': args.seed, 'random_cases': args.random_cases,
        'cases': [], 'skipped': [], 'failures': [],
        'lower_bound_proof_scope': 'upstream independent checker; additionally W<=exact OPT on each selected tiny case',
    }

    def save() -> None:
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')

    if args.base is not None:
        binaries = {'base': args.base.absolute(), 'candidate': args.candidate.absolute()}
        for name, binary in binaries.items():
            if not binary.is_file():
                parser.error(f'{name} binary not found: {binary}')
        report['binaries'] = {name: {'name': binary.name, 'sha256': digest(binary),
                                    'bytes': binary.stat().st_size}
                              for name, binary in binaries.items()}
        selected, skipped = select_native_cases(tiny_cases(args.seed, args.random_cases))
        report['skipped'] = skipped
        with tempfile.TemporaryDirectory(prefix='scs-native-check-') as temporary:
            for case in selected:
                try:
                    report['cases'].append(check_case(case, binaries, Path(temporary), args.timeout))
                except Exception as error:
                    report['failures'].append({'case': case.original.name,
                                               'type': type(error).__name__, 'message': str(error)})
                    save()
                    raise
        report['all_selected_cases_passed'] = True
    save()
    print(json.dumps({'self_tests': report['self_tests'],
                      'native_cases_passed': len(report['cases']),
                      'removed_empty_words': sum(case['removed_empty_words'] for case in report['cases']),
                      'skipped': report['skipped'], 'failures': report['failures'],
                      'output': str(args.output) if args.output else None}, indent=2))


if __name__ == '__main__':
    main()
