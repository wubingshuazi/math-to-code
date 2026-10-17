"""Reproducible byte-string workloads and independent lazy-scs result checks.

New engineering: 100% GPT-generated. This module is stdlib only and does
not import the solver, its automaton, count tables or certificate checker.
It never benchmarks the solver. No network access happens on import.

The native CLI at nurric-ai/lazy-scs@4ee86724 reads UTF-8 lines and switches
to FASTA mode if any line starts with '>'. Therefore DNA4, ASCII32, ASCII64
and periodic cases use only the explicit line-safe alphabets below. They
exclude CR/LF, '>', all whitespace and the native batch separator '---'.
True binary128 cases are available through generate_case(), but cannot be
written as native CLI lines; use a byte-array library API in a later study.

The optional real string dictionary is Adobe Glyph List 2.0: glyph names
used in font/Unicode mapping. Its upstream BSD-3-Clause copyright and
license are preserved with the downloaded source. This is a candidate
string-pool workload; it does not itself demonstrate a production speedup.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import struct
from typing import Any, Iterable, Mapping
import urllib.request


SOLVER_COMMIT = "4ee86724b770c54bad400fe077b297288b087c4b"
DNA4 = b"ACGT"
ASCII32 = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
ASCII64 = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
BINARY128 = bytes(range(128, 256))
NATIVE_KINDS = ("dna4", "ascii32", "ascii64", "periodic")
CORPUS_COMMIT = "4036a9ca80a62f64f9de4f7321a9a045ad0ecfd6"
CORPUS_BASE = (
    "https://raw.githubusercontent.com/adobe-type-tools/agl-aglfn/"
    + CORPUS_COMMIT
    + "/"
)
CORPUS_FILES = {
    "glyphlist.txt": {
        "sha256": "a3b2f61ced9f3644cc0d4ecde5c59df34ca286c689d9484a43a710a81c466789",
        "bytes": 78060,
    },
    "LICENSE.md": {
        "sha256": "58147d341e7a34aa2196862395a34d2fd95716c41d5ed26efb59ab0e12f92089",
        "bytes": 1404,
    },
}


def _integer(value: Any, name: str, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _byte_strings(strings: Iterable[bytes]) -> list[bytes]:
    if isinstance(strings, (str, bytes, bytearray, memoryview)):
        raise TypeError("strings must be an iterable of byte strings")
    result = []
    for item in strings:
        if not isinstance(item, (bytes, bytearray, memoryview)):
            raise TypeError("every input string must be bytes-like")
        result.append(bytes(item))
    return result


def input_digest(strings: Iterable[bytes]) -> str:
    """Unambiguous ordered-list hash; includes count and each byte length."""
    data = _byte_strings(strings)
    digest = hashlib.sha256(struct.pack("<Q", len(data)))
    for word in data:
        digest.update(struct.pack("<Q", len(word)))
        digest.update(word)
    return digest.hexdigest()


def reduce_inputs(strings: Iterable[bytes]) -> list[bytes]:
    """Independent duplicate/containment removal, using Python byte search.

    This deliberately simple O(k²) reference is for tiny correctness cases;
    do not include its time in native solver measurements or run it merely
    to describe a million-character workload.
    """
    unique = sorted(set(_byte_strings(strings)), key=lambda word: (-len(word), word))
    kept: list[bytes] = []
    for word in unique:
        if word and not any(word in larger for larger in kept):
            kept.append(word)
    return kept


def exact_optimal_length(strings: Iterable[bytes], max_strings: int = 9) -> int:
    """Exact shortest-superstring length by subset DP after containment removal.

    Once no word contains another, an optimum has a left-to-right word
    order and consecutive suffix/prefix overlaps, so Held-Karp over those
    overlaps is exact. The oracle shares no solver/SAM/count implementation.
    The limit applies to the irredundant words, allowing duplicates and
    contained-word regressions among the original inputs.
    """
    _integer(max_strings, "max_strings", 1)
    words = reduce_inputs(strings)
    n = len(words)
    if n > max_strings:
        raise ValueError(f"exact oracle limited to {max_strings} irredundant strings; got {n}")
    if not n:
        return 0
    overlap = [[0] * n for _ in range(n)]
    for i, left in enumerate(words):
        for j, right in enumerate(words):
            if i != j:
                for size in range(min(len(left), len(right)), 0, -1):
                    if left[-size:] == right[:size]:
                        overlap[i][j] = size
                        break
    unreachable = sum(map(len, words)) + 1
    costs = [[unreachable] * n for _ in range(1 << n)]
    for last, word in enumerate(words):
        costs[1 << last][last] = len(word)
    for mask in range(1, 1 << n):
        for last in range(n):
            current = costs[mask][last]
            if current == unreachable:
                continue
            for nxt, word in enumerate(words):
                if not mask & (1 << nxt):
                    new_mask = mask | (1 << nxt)
                    candidate = current + len(word) - overlap[last][nxt]
                    if candidate < costs[new_mask][nxt]:
                        costs[new_mask][nxt] = candidate
    return min(costs[-1])


def validate_containment(strings: Iterable[bytes], superstring: bytes) -> dict[str, Any]:
    """Check every original word directly, including duplicates and empties."""
    words = _byte_strings(strings)
    if not isinstance(superstring, (bytes, bytearray, memoryview)):
        raise TypeError("superstring must be bytes-like")
    output = bytes(superstring)
    missing = [i for i, word in enumerate(words) if word not in output]
    if missing:
        raise ValueError(f"output misses input indexes {missing[:12]}")
    return {
        "contained": True,
        "checked_original_strings": len(words),
        "output_length": len(output),
        "output_sha256": hashlib.sha256(output).hexdigest(),
    }


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def certificate_json(value: str | bytes | Mapping[str, Any]) -> dict[str, Any]:
    """Parse one JSON summary, rejecting duplicate keys and NaN/Infinity."""
    if isinstance(value, (str, bytes)):
        parsed = json.loads(value, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    elif isinstance(value, Mapping):
        parsed = dict(value)
    else:
        raise TypeError("certificate must be a JSON object or serialized JSON object")
    if not isinstance(parsed, dict) or not all(isinstance(key, str) for key in parsed):
        raise ValueError("certificate must be a JSON object with string keys")
    return parsed


def validate_result(
    strings: Iterable[bytes],
    superstring: bytes,
    certificate: str | bytes | Mapping[str, Any],
    *,
    require_verified: bool = True,
    check_optimum: bool = True,
) -> dict[str, Any]:
    """Validate containment, summary consistency and reported checker outcomes.

    A JSON counter is not an independently rederived lower-bound proof.
    For >9 original words this module checks the checker outcome, output
    containment and length inequalities; it does not assert exact optimality.
    Call the native solver with --verify so the required counters exist.
    Tiny cases additionally check W <= exact OPT and length <= 2 exact OPT.
    """
    words = _byte_strings(strings)
    report = validate_containment(words, superstring)
    summary = certificate_json(certificate)
    stats = summary.get("stats", {})
    if not isinstance(stats, Mapping):
        raise ValueError("stats must be an object")
    native = "W" in summary
    bound_name = "W" if native else "lower_bound"
    if bound_name not in summary:
        raise ValueError("certificate missing W/lower_bound")
    lower_bound = _integer(summary[bound_name], bound_name)
    length = report["output_length"]
    if "length" in summary and _integer(summary["length"], "length") != length:
        raise ValueError("certificate length does not match actual output bytes")
    if native and "length" not in summary:
        raise ValueError("native certificate missing length")
    if lower_bound > length or length > 2 * lower_bound:
        raise ValueError("length must satisfy W <= length <= 2W")
    if "W_ext" in summary and _integer(summary["W_ext"], "W_ext") > lower_bound:
        raise ValueError("initial W_ext exceeds final W")
    if "strings" in summary and _integer(summary["strings"], "strings") != len(words):
        raise ValueError("certificate string count does not match original input")
    total = sum(map(len, words))
    if "input_chars" in summary and _integer(summary["input_chars"], "input_chars") != total:
        raise ValueError("certificate input_chars does not match original input")
    if "rounds" in summary:
        _integer(summary["rounds"], "rounds", 1 if any(words) else 0)
    elif native:
        raise ValueError("native certificate missing rounds")
    if "seconds" in summary:
        seconds = summary["seconds"]
        if (isinstance(seconds, bool) or not isinstance(seconds, (int, float))
                or not math.isfinite(seconds) or seconds < 0):
            raise ValueError("seconds must be a finite nonnegative number")
    checks: dict[str, int] = {}
    for key in ("verify_points", "verify_unjustified", "verify_ext_violations"):
        if key in summary and key in stats and summary[key] != stats[key]:
            raise ValueError(f"conflicting {key} counters")
        value = summary.get(key, stats.get(key))
        if value is not None:
            checks[key] = _integer(value, key)
        elif require_verified and any(words):
            raise ValueError(f"certificate missing {key}; run solver with --verify")
    if checks.get("verify_unjustified", 0) or checks.get("verify_ext_violations", 0):
        raise ValueError("upstream independent checker reports a certificate violation")
    if require_verified and any(words) and checks.get("verify_points", 0) == 0:
        raise ValueError("nonempty input requires at least one independently checked point")
    report.update({
        "lower_bound": lower_bound,
        "factor_two_length_check": True,
        "checker_counters": checks,
        "checker_outcome_checked": bool(checks),
        "lower_bound_independently_rederived_here": False,
        "input_sha256": input_digest(words),
    })
    if check_optimum and len(words) <= 9:
        optimum = exact_optimal_length(words)
        if lower_bound > optimum:
            raise ValueError(f"reported lower bound {lower_bound} exceeds exact optimum {optimum}")
        if length > 2 * optimum:
            raise ValueError("output length exceeds twice exact optimum")
        report["exact_optimal_length"] = optimum
        report["exact_approximation_ratio"] = length / optimum if optimum else 1.0
    return report


def generate_case(kind: str, total_chars: int, seed: int, fragment_length: int = 80) -> list[bytes]:
    """Deterministic synthetic fragments with exactly total_chars input bytes.

    Random classes sample overlapping error-free fragments from a seeded
    source of approximately one quarter the aggregate input length. Periodic
    cases alternate pure periodic reads with reads having random flanks;
    they exercise duplicate reduction and periodic structure separately.
    The final fragment may be shorter to preserve the requested total.
    """
    _integer(total_chars, "total_chars")
    _integer(seed, "seed")
    _integer(fragment_length, "fragment_length", 1)
    alphabets = {"dna4": DNA4, "ascii32": ASCII32, "ascii64": ASCII64, "binary128": BINARY128}
    if kind not in (*alphabets, "periodic"):
        raise ValueError(f"unknown workload kind {kind!r}")
    if not total_chars:
        return []
    rng = random.Random(seed)
    sizes = [fragment_length] * (total_chars // fragment_length)
    if total_chars % fragment_length:
        sizes.append(total_chars % fragment_length)
    if kind != "periodic":
        alphabet = alphabets[kind]
        source_length = max(max(sizes), total_chars // 4 + fragment_length)
        source = bytes(alphabet[rng.randrange(len(alphabet))] for _ in range(source_length))
        result = []
        for size in sizes:
            start = rng.randrange(source_length - size + 1)
            result.append(source[start:start + size])
        return result
    result = []
    for index, size in enumerate(sizes):
        period = (1, 2, 3, 5, 7, 11)[index % 6]
        motif = bytes(DNA4[rng.randrange(4)] for _ in range(period))
        offset = rng.randrange(period)
        core = (motif * ((size + period * 2) // period))[offset:offset + size]
        if index % 2 and size >= 18:
            flank = min(8, size // 4)
            left = bytes(ASCII32[rng.randrange(32)] for _ in range(flank))
            right = bytes(ASCII32[rng.randrange(32)] for _ in range(flank))
            core = left + core[flank:-flank] + right
        result.append(core)
    return result


@dataclass(frozen=True)
class TinyCase:
    name: str
    strings: tuple[bytes, ...]
    expected_optimal: int


def tiny_cases(seed: int = 1282026, random_cases: int = 24) -> list[TinyCase]:
    """Finite correctness cases; zero-input cases need the library API.

    The pinned Rust CLI emits a trailing comma in its JSON when the solver
    returns empty stats. Record that upstream CLI limitation rather than
    treating malformed empty-instance JSON as a valid certificate.
    """
    _integer(seed, "seed")
    _integer(random_cases, "random_cases")
    fixed = [
        ("empty", ()),
        ("only_empty", (b"",)),
        ("single", (b"GATTACA",)),
        ("duplicates_containment", (b"", b"ABC", b"BC", b"ABC", b"A")),
        ("overlap_chain", (b"ABC", b"BCD", b"CDE")),
        ("overlap_cycle", (b"ABC", b"BCA", b"CAB")),
        ("periodic", (b"ABABA", b"BABAB", b"ABAB")),
        ("no_overlap", (b"AAA", b"BBB", b"CCC")),
        ("classic", (b"CATGC", b"CTAAGT", b"GCTA", b"TTCA", b"ATGCATC")),
        ("binary_only", (b"\x00\x80\xff", b"\x80\xff\x00", b"\xff\x00\x80")),
    ]
    rng = random.Random(seed)
    for index in range(random_cases):
        count = 1 + index % 9
        alphabet = (DNA4, ASCII32, ASCII64)[index % 3]
        words = tuple(
            bytes(alphabet[rng.randrange(len(alphabet))] for _ in range(rng.randrange(1, 10)))
            for _ in range(count)
        )
        fixed.append((f"seeded_{seed}_{index:03d}", words))
    return [TinyCase(name, tuple(words), exact_optimal_length(words)) for name, words in fixed]


def native_line_bytes(strings: Iterable[bytes]) -> bytes:
    """Serialize only inputs represented unchanged by the pinned native CLI."""
    words = _byte_strings(strings)
    for index, word in enumerate(words):
        if not word or b"\r" in word or b"\n" in word or word.startswith(b">") or word == b"---":
            raise ValueError(f"input {index} is not representable unambiguously as native CLI lines")
        try:
            text = word.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"input {index} is binary-only, not UTF-8 native CLI input") from exc
        if text.strip() != text:
            raise ValueError(f"input {index} has leading/trailing whitespace")
    return b"\n".join(words) + (b"\n" if words else b"")


def load_adobe_glyph_names(
    cache_dir: Path | str,
    *,
    limit: int | None = None,
    split: str = "all",
    seed: int = 1282026,
) -> tuple[list[bytes], dict[str, Any]]:
    """Explicitly fetch/cache the pinned, hash-verified BSD-3-Clause corpus.

    'development'/'holdout' split membership depends only on SHA-256(name),
    not on solver behavior. Subset selection uses a separately seeded hash
    order, returned in lexical order. Full source with license header and
    LICENSE.md are retained in cache_dir and must accompany redistributed
    derived input files. Data is public; no user files are accessed.
    """
    if split not in ("all", "development", "holdout"):
        raise ValueError("split must be all, development or holdout")
    if limit is not None:
        _integer(limit, "limit", 1)
    _integer(seed, "seed")
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    raw: dict[str, bytes] = {}
    for filename, expected in CORPUS_FILES.items():
        path = cache / filename
        data = path.read_bytes() if path.exists() else urllib.request.urlopen(CORPUS_BASE + filename, timeout=30).read()
        if len(data) != expected["bytes"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
            raise ValueError(f"pinned Adobe corpus hash/size mismatch: {filename}")
        if not path.exists():
            path.write_bytes(data)
        raw[filename] = data
    words = []
    for line in raw["glyphlist.txt"].splitlines():
        if line and not line.startswith(b"#"):
            parts = line.split(b";")
            if len(parts) != 2 or not parts[0].isalnum():
                raise ValueError("unexpected Adobe glyph-list record")
            words.append(parts[0])
    if len(set(words)) != len(words):
        raise ValueError("duplicate Adobe glyph names")
    original_count = len(words)
    if split != "all":
        side = 0 if split == "development" else 1
        words = [word for word in words if hashlib.sha256(word).digest()[0] % 2 == side]
    if limit is not None and len(words) > limit:
        words = sorted(words, key=lambda word: hashlib.sha256(str(seed).encode("ascii") + b":" + word).digest())[:limit]
    words.sort()
    provenance = {
        "name": "Adobe Glyph List 2.0 glyph-name dictionary",
        "table_version": "2.0",
        "table_date": "2002-09-20",
        "repository": "https://github.com/adobe-type-tools/agl-aglfn",
        "commit": CORPUS_COMMIT,
        "license": "BSD-3-Clause",
        "copyright": "Copyright 2002-2019 Adobe (http://www.adobe.com/).",
        "source_files": {filename: {**info, "url": CORPUS_BASE + filename} for filename, info in CORPUS_FILES.items()},
        "source_dictionary_names": original_count,
        "selected_names": len(words),
        "selected_input_chars": sum(map(len, words)),
        "selection": {"split": split, "limit": limit, "seed": seed},
        "split_method": "SHA256(name)[0] % 2; 0 development, 1 holdout",
        "selected_input_sha256": input_digest(words),
        "license_preserved_in": str(cache.resolve()),
    }
    return words, provenance


def _write_new(path: Path, content: bytes) -> None:
    with path.open("xb") as target:
        target.write(content)


def write_workloads(
    out_dir: Path | str,
    *,
    sizes: Iterable[int] = (10000, 100000),
    seeds: Iterable[int] = (1282026,),
    fragment_length: int = 80,
    include_adobe: bool = False,
    adobe_limits: Iterable[int] = (128, 512),
) -> dict[str, Any]:
    """Write new fixture files and manifest, refusing to overwrite results.

    Corpus subsets at two sizes are screening inputs, not separate corpus
    sources or independent observations. Holdout glyphs are not emitted
    during this development pilot. Native timing is the root driver's job.
    """
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    size_list, seed_list = list(sizes), list(seeds)
    if not size_list or not seed_list:
        raise ValueError("at least one size and seed are required")
    for size in size_list:
        _integer(size, "size", 1)
    for seed in seed_list:
        _integer(seed, "seed")
    _integer(fragment_length, "fragment_length", 1)
    cases = []

    def emit(name: str, words: list[bytes], details: dict[str, Any]) -> None:
        path = output / (name + ".txt")
        raw = native_line_bytes(words)
        _write_new(path, raw)
        cases.append({
            "name": name,
            "path": path.name,
            "strings": len(words),
            "input_chars": sum(map(len, words)),
            "unique_strings": len(set(words)),
            "alphabet_cardinality": len(set(b"".join(words))),
            "input_sha256": input_digest(words),
            "file_sha256": hashlib.sha256(raw).hexdigest(),
            "file_bytes": len(raw),
            **details,
        })

    for kind in NATIVE_KINDS:
        for size in size_list:
            for seed in seed_list:
                words = generate_case(kind, size, seed, fragment_length)
                emit(f"{kind}-bytes{size}-seed{seed}", words,
                     {"kind": kind, "seed": seed, "fragment_length": fragment_length, "source": "synthetic"})
    if include_adobe:
        cache = output / "adobe-source-and-license"
        for limit in adobe_limits:
            words, provenance = load_adobe_glyph_names(cache, limit=limit, split="development", seed=seed_list[0])
            emit(f"adobe-glyphs-development-{limit}", words,
                 {"kind": "adobe_glyph_names", "source": "real_dictionary", "provenance": provenance})
    manifest = {
        "schema_version": 1,
        "engineering_attribution": "100% GPT-generated; original corpus and solver attribution preserved",
        "target_repository": "https://github.com/nurric-ai/lazy-scs",
        "target_commit": SOLVER_COMMIT,
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "native_input_note": "UTF-8 lines; ASCII synthetic cases exclude CR/LF, > and whitespace; binary128 not emitted",
        "case_count": len(cases),
        "cases": cases,
    }
    _write_new(output / "manifest.json", (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return manifest


def self_test() -> dict[str, int]:
    """Bounded integrity checks only; no solver runs or performance timings."""
    checked = 0
    for case in tiny_cases(random_cases=12):
        assert 0 <= case.expected_optimal <= sum(map(len, case.strings))
        checked += 1
    # Independent exhaustive output-string search over a tiny binary universe,
    # not a second implementation of the overlap recurrence.
    universe = [b"A", b"B", b"AA", b"AB", b"BA", b"BB"]
    for chosen in itertools.combinations(universe, 3):
        exact = exact_optimal_length(chosen)
        brute = None
        for length in range(sum(map(len, chosen)) + 1):
            if any(all(word in bytes(candidate) for word in chosen)
                   for candidate in itertools.product(b"AB", repeat=length)):
                brute = length
                break
        assert exact == brute, (chosen, exact, brute)
        checked += 1
    for kind in (*NATIVE_KINDS, "binary128"):
        first = generate_case(kind, 1037, 1282026)
        assert sum(map(len, first)) == 1037
        assert first == generate_case(kind, 1037, 1282026)
        if kind != "binary128":
            native_line_bytes(first)
        checked += 1
    summary = {"W": 5, "W_ext": 5, "length": 5, "rounds": 1,
               "verify_points": 3, "verify_unjustified": 0, "verify_ext_violations": 0}
    assert validate_result([b"ABC", b"BCD", b"CDE"], b"ABCDE", summary)["exact_optimal_length"] == 5
    bad_count = 0
    for broken in (
        {**summary, "W": 6}, {**summary, "length": 4}, {**summary, "verify_unjustified": 1},
        {**summary, "verify_ext_violations": 1}, {**summary, "verify_points": 0},
        {**summary, "W": True}, {**summary, "seconds": float("nan")},
    ):
        try:
            validate_result([b"ABC", b"BCD", b"CDE"], b"ABCDE", broken)
        except ValueError:
            bad_count += 1
        else:
            raise AssertionError("invalid certificate accepted")
    for serialized in ('{"W": 5, "W": 6}', '{"W": NaN}', '[]'):
        try:
            certificate_json(serialized)
        except ValueError:
            bad_count += 1
        else:
            raise AssertionError("malformed certificate accepted")
    try:
        validate_containment([b"MISSING"], b"ABCDE")
    except ValueError:
        bad_count += 1
    else:
        raise AssertionError("missing string accepted")
    return {"positive_cases": checked + 1, "rejected_bad_results": bad_count}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--sizes", default="10000,100000")
    parser.add_argument("--seeds", default="1282026")
    parser.add_argument("--fragment-length", type=int, default=80)
    parser.add_argument("--adobe", action="store_true", help="download/cache pinned BSD-3-Clause Adobe glyph names")
    parser.add_argument("--adobe-limits", default="128,512")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
    if args.output_dir is not None:
        manifest = write_workloads(
            args.output_dir,
            sizes=[int(value) for value in args.sizes.split(",")],
            seeds=[int(value) for value in args.seeds.split(",")],
            fragment_length=args.fragment_length,
            include_adobe=args.adobe,
            adobe_limits=[int(value) for value in args.adobe_limits.split(",")],
        )
        print(json.dumps({"case_count": manifest["case_count"], "manifest": str(args.output_dir / "manifest.json")}, sort_keys=True))
    elif not args.self_test:
        parser.error("provide --self-test and/or --output-dir")


if __name__ == "__main__":
    main()
