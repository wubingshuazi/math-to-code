# Stage 10 — Native profiling rejects the first hotspot

2026-10-17, Asia/Shanghai. User confirmed practical speedup takes priority
and allows mature methods outside the OpenAI collection, then explicitly
asked to continue producing results. This is an ongoing native checkpoint.

## Setup and reproducible snapshots

Pinned lazy-scs source remains 4ee86724b770c54bad400fe077b297288b087c4b.
Ignored source copies: .verification/lazy-scs-native/base and event-sweep.
The source manifest records every fetched original file SHA-256. No upstream
AGENTS.md was present. Original MIT attribution is retained.

Dedicated Rust 1.99.1 GNU toolchain installed under .buildcheck/toolchains;
no global PATH changes. Rustup's initial downloads stalled; direct stdlib
downloads verified the official manifest SHA-256, then a pinned minimal
toolchain installation succeeded. Native MinGW linking cannot open paths
containing the Chinese workspace component. An ASCII junction
C:/Users/lenovo/math-speed-native points to this checkout; explicit sysroot
uses that alias. Dependency rlib canonicalization needed a real ASCII target
directory, so current Cargo outputs are C:/Users/lenovo/math-speed-build-targets/{variant}.
The isolated helper is .buildcheck/native_cargo.py. These are local build
details; ordinary ASCII checkouts can build directly with Cargo.

## Native correctness and profiles

Candidate Counts::compute uses exact event-sweep aggregation; original
compute/new are retained under cfg(test) for differential comparison.
Release tests: 5 passed, 0 failed, covering seven boundary fixtures,
1,000 random step-function cases, 961 binary-word-pair SAMs, five periodic
fixed-point fixtures and 100 random real SAMs, including forced interior
bumps. Full r/f tables, indices, children_sum, W, bumps, passes and edge
multiplicities match. No native performance conclusion came from those tests.

Identical lib.rs/main.rs instrumentation is applied in both variants.
LAZY_SCS_PROFILE=1 records timing stages; =stats also records structural
histograms. Default mode preserves normal output. Single and batch smoke
checks confirmed parsed JSON, unchanged output and timer containment.

## Persisted complete-program screen

Run results/scs_native_screen.json and its append-only JSONL journal were
produced by the first revision of experiments/benchmark_scs_native.py.
The report stores the exact benchmark-script SHA-256. Source and report
must be retained together in Git history before modifying the driver.

Inputs: DNA4, ASCII32, ASCII64 and periodic strings at 10k/100k bytes,
seed1282026; Adobe glyph dictionary development subsets128/512. The actual
Adobe files and BSD-3-Clause license are pinned/hashes verified by
experiments/scs_native_cases.py. All timing runs enable --verify.

Eight cases completed: all 112 runs have identical output bytes and all
non-time certificate/statistic values. Two periodic baseline cases hit
the 60-second limit before candidate timing, and are explicitly failed
cases rather than excluded winning data. No solver process remains active.

The count stage is about3.8–9.3% of measured internal CLI work. Synthetic
process-wall changes range roughly-3.1% to+3.0%; the small Adobe512 wall
median appears8.4% lower, but its sampled native interval does not improve,
and Windows startup dominates those tiny cases. This does not pass the
15% whole-task continuation gate. Stop treating count aggregation as the
main optimization target; preserve the valid implementation as a prototype.

Generator/validator self-checks:48 positive and11 rejected-invalid cases.
The exact tiny oracle was independently compared with exhaustive strings.
The ordinary-run driver is sequential, randomized A/B, and validates every
output. A reviewer requested two hardening changes for the next revision:
refuse Python -O (or replace assertions), and persist timeout context/raw
partial output in the journal. These do not retroactively change this run.

## Next measured target

Profiles show significant repeated suffix-automaton construction, including
Sam::trim, which builds TWO automata. A new aho-trim variant is in progress:
use existing Aho–Corasick multi-pattern matching to compute the same latest
start cut and subsequent earliest-end cut. Independent review verified SAM
pos means first occurrence end on1,023 binary texts/25,732 queries.

Important fixture: t=abab, req=[ab,ba] must return bab. The second matching
pass starts fresh at the retained suffix; accepting any full-text match
whose end merely exceeds the cut is incorrect. Overlapping matching is
required. Existing reduced req is a substring antichain, so matching output
events are linear in text length for actual solver calls.

This is mature-algorithm engineering, not a new OpenAI mathematical result.
The original paper length guarantee and independent checker stay intact.
Strings agent owns aho-trim sam.rs/Cargo files; a second agent is preparing
a batch-throughput driver to amortize Windows process startup. Developer
input run-002 adds1m-byte cases and all2,189 development glyph names; no
held-out data has been used. Complete native A/B and held-out validation
before accepting a useful acceleration claim.
