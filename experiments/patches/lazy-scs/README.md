# Reproducible lazy-scs optimization patches

These patches modify an existing implementation of OpenAI math family 128.
The final `aho-trim` variant replaces the output-trimming implementation
with Aho–Corasick matching while retaining the original trim as a fallback.
Its purpose is to reduce repeated construction of output-sized suffix
automata while producing the same output bytes.

**New patches, experiment scripts, tests and project documentation are
100% GPT-generated.** The mathematical theorem, original lazy-scs solver,
Aho–Corasick algorithm, Rust matcher implementation and corpus retain their
original authorship. That label does not claim their work as our contribution.
See [third-party notices](THIRD_PARTY_NOTICES.md) and the repository's
[contribution record](../../../CREDITS.md).

## Pinned starting point and variants

Upstream: [nurric-ai/lazy-scs](https://github.com/nurric-ai/lazy-scs/tree/4ee86724b770c54bad400fe077b297288b087c4b),
commit `4ee86724b770c54bad400fe077b297288b087c4b`, MIT,
copyright 2026 Krushna Dere. [source_index.json](source_index.json) records
every selected original source file, patch digest, ordered patch list and
expected resulting file hash. The preparation script checks those bytes
before and after applying patches; it fetches a selected build/test source
subset rather than cloning every upstream file.

| Variant | Patches, applied in order | Role |
| --- | --- | --- |
| `original` | none | Unmodified pinned baseline. |
| `profile-original` | `profiling.patch` | Baseline stage timing and structural inspection. |
| `event-sweep` | `profiling.patch`, `event-sweep.patch` | Earlier count-aggregation prototype and differential tests. The count stage was too small to justify continuing this target. |
| `aho-trim-v1` | `aho-trim-v1.patch` | Historical first trim prototype; matcher-build errors panic. Preserved for replay of its experiments. |
| `profile-aho-trim-v1` | `profiling.patch`, `aho-trim-v1.patch` | Historical prototype with the same profiling instrumentation as the baseline. |
| `aho-trim` | `aho-trim.patch` | Final trim candidate, including legacy fallback and six trim test groups. Original `lib.rs`, `main.rs`, count algorithm and independent checker remain byte-identical to upstream. |

`aho-trim-v1.patch` and `aho-trim.patch` are alternative patches from the
same original source, not successive patches to stack. Use the preparation
script and variant names to apply the correct sequence. Profiling changes
are excluded from the final `original` versus `aho-trim` comparison.

## What the final trim changes

The existing trim removes a leading prefix, then a trailing suffix, while
preserving every required string. The replacement builds one multi-pattern
matcher, records each pattern's latest occurrence start, and cuts at the
minimum of those starts. It then scans the retained suffix afresh, records
each pattern's earliest occurrence end and cuts at the maximum of those
ends. Overlapping matches are required. For `t = abab`, requirements `ab`
and `ba`, the retained output is `bab`; the second pass cannot simply reuse
matches that cross the first cut.

If the matcher's fallible construction returns an error, the final variant
calls the retained legacy suffix-automaton trim. The injected-builder tests
exercise this path without allocating huge inputs to exhaust matcher
representation limits. Missing required strings preserve the original
panic contract. Empty requirements, duplicates, contained patterns, UTF-8
and arbitrary bytes are covered in trim tests. This fallback concerns
reported matcher-build errors; it does not turn process-wide allocation
failure into a recoverable error.

The change uses the established Aho–Corasick method and Andrew Gallant's
`aho-corasick` crate, pinned to 1.1.5; its `memchr` dependency is locked to
2.8.3. It changes neither the paper's approximation construction nor the
upstream lower-bound checker. Tests and output parity support the
implementation claim; they are not an independent formal proof of the
complete upstream solver.

## Prepare, build and check

Run these commands from this repository's root. Git, Python 3.10+ and a
Rust toolchain with the required platform linker must be available. The
recorded native study used Rust 1.99.1 on `x86_64-pc-windows-gnu`; retain
toolchain, target and flags when comparing runs. Use fresh source/output
directories: preparation refuses to overwrite earlier snapshots.

```console
python experiments/prepare_scs_native.py --directory .verification/scs-replay-original --variant original
python experiments/prepare_scs_native.py --directory .verification/scs-replay-aho --variant aho-trim
cargo build --locked --release --manifest-path .verification/scs-replay-original/scs/scs-rs/Cargo.toml --target-dir .verification/scs-replay-build/original
cargo build --locked --release --manifest-path .verification/scs-replay-aho/scs/scs-rs/Cargo.toml --target-dir .verification/scs-replay-build/aho-trim
cargo test --locked --release --manifest-path .verification/scs-replay-aho/scs/scs-rs/Cargo.toml --target-dir .verification/scs-replay-build/aho-trim
python experiments/scs_native_cases.py --self-test
```

Both builds must use identical release settings. The prepared directories
contain `source_provenance.json` and a `third-party-notices` directory with
license copies. Ordinary Cargo builds do not require the local study's
private toolchain helper. On this Windows machine, an ASCII checkout/alias
and an ASCII build-target directory were needed for the GNU linker; the
details are recorded in [stage 10](../../../worklogs/2026-10-17-10-native-screen-checkpoint.md).

## Reproduce the fixed corpus and batch comparison

The public real-data case is the Adobe Glyph List 2.0 glyph-name dictionary,
not private user data. The preparation script checks its pinned source and
license hashes. A name's SHA-256 determines development versus holdout
membership: 2,189 development names and 2,092 holdout names, with zero
intersection. The holdout script emits a fixed 512-name subset and the
complete holdout; it does not run the solver. Its generated directory
preserves the original data, copyright header and BSD-3-Clause license.

The following is a Windows replay example. On Unix, omit `.exe` from the
two binary paths. Choose unused result/work paths on subsequent runs.

```console
python experiments/prepare_scs_holdout.py --output-dir .verification/scs-replay-heldout
python experiments/benchmark_scs_batch.py --inputs .verification/scs-replay-heldout --base .verification/scs-replay-build/original/release/scs-rs.exe --candidate .verification/scs-replay-build/aho-trim/release/scs-rs.exe --output results/scs-local-heldout.json --work .verification/scs-local-heldout-output --repeats 9 --iterations 40 --timeout 60
```

Each process solves **the same input case 40 times** using upstream
`--batch --verify`, rebuilding solver structures on every instance. This
amortizes process startup; it is not 40 independent datasets or a
single-call latency measurement. A/B execution order is balanced and
shuffled. All output bytes, lower bounds and non-time certificate values
are checked, and raw captures and failures are preserved.

Process wall time includes startup, native parsing, cloning, solving,
upstream verification, coverage checking and output. The separate checked
wall metric additionally includes capture preservation and Python result
validation. Profile runs, when explicitly enabled on instrumented
variants, are excluded from timing medians. Do not request profiling from
the final uninstrumented binaries.

See [final held-out raw results](../../../results/scs_aho_trim_batch_heldout_final.json)
and [append-only run journal](../../../results/scs_aho_trim_batch_heldout_final.jsonl).
Earlier development/v1 results and the unsuccessful count-stage experiment
remain separate records. The measured application scope is repeated glyph
dictionary solves on this machine; it does not establish the same benefit
for arbitrary text, genome assembly, all periodic inputs, single invocations
or other hardware. Broader adoption requires the corresponding workload
and platform checks.
