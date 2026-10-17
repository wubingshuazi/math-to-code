# String-algorithm acceleration feasibility

Checked 2026-10-17 (Asia/Shanghai). New assessment: 100% GPT-generated.
Read AGENTS.md, HANDOFF.md, PROJECT_STATE.json and stage 08 before this audit.
This is source inspection and an experiment proposal; no local speedup has
been measured in this note.

## Decision

| Candidate | Practical decision for a one-to-two-month project |
| --- | --- |
| Family 121, almost-linear edit-distance approximation | Reject direct implementation as a practical acceleration project. The published program uses exact quadratic DP at every physically feasible input size. |
| Family 128, factor-two shortest common superstring | A plausible short profiling experiment, by improving an existing implementation. It already has several implementations; the opportunity is a measured improvement with unchanged output/certificate behavior. |

**Best string candidate: profile and optimize lazy-scs's compressed-count
evaluation, with a 48-hour stop/go decision.** This would make an existing
implementation of family 128 faster. It would not establish a new
almost-linear edit-distance implementation or a general-purpose genome
assembler.

## Family 121: the cutoff is decisive

Pinned upstream: `openai/math@1581d4cbdd69a0faf34b2089614fe2a814316a6a`.
The [input and fallback rules, lines 88–108](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/An-Almost-Linear-Approximation-Scheme-for-Edit-Distance-September-24-2026/build/sections/02-geometry.tex#L88-L108)
define H as a power-of-two rounding of log2(N+2), and ell as a
power-of-two rounding of log2 H. Lines 99–100 explicitly select exact
dynamic programming whenever `ell < 2^1000` or `ell * epsilon < 10`.
Even an input of one trillion symbols has H = 64 and ell = 8. This is
an asymptotic result with a deliberately enormous threshold, not a
branch that additional local CPU/GPU time can make accessible.

Removing that guard would be a new experimental algorithm: the existing
analysis would not certify its accuracy. The same source's parameter
section has `P = H^(p_*+20)`, `theta = ell^-40` and `Q1 = ell^80`;
the [work analysis](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/An-Almost-Linear-Approximation-Scheme-for-Edit-Distance-September-24-2026/build/sections/10-work.tex)
also directly enumerates action lists exponential in a branching
parameter. The theorem does not provide a usable practical crossover.

The [main guarantee](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/An-Almost-Linear-Approximation-Scheme-for-Edit-Distance-September-24-2026/build/sections/01-introduction.tex)
is an upper estimate between D and `(1+epsilon)D` with probability at
least 2/3, for unit-cost insertions, deletions and substitutions. It
returns a distance, not an edit script. The almost-linear assertion is
for each fixed rational epsilon; it does not claim polynomial dependence
on inverse accuracy.

Any future relaxed-parameter prototype must compete with mature native
code, not a Python quadratic teaching implementation:

- [Edlib](https://github.com/Martinsos/edlib/tree/0ddc23ea06abd95ab6227442acb4c27bd7607b68)
  implements exact Levenshtein alignment with Myers bit vectors,
  Ukkonen banding and linear-space path reconstruction. It supports
  distance-only work and performs especially well on similar sequences.
- [WFA2-lib](https://github.com/smarco/WFA2-lib/tree/6176f9476dcda0a2291dfff3248cedba2ba8d68e)
  supports exact edit distance as well as other scoring models, score-only
  operation and low-memory modes. Its README gives O(ns+s^2) time and
  O(s) space in the ultralow mode. Heuristics must be disabled for an exact
  baseline; reuse aligner objects across repeated requests. Gap-affine
  scores must not be compared as if they were unit-cost edit distance.

These baselines leave the most plausible approximation niche at long,
dissimilar strings when a distance estimate is acceptable. Family 121's
published finite rules do not reach that niche at practical sizes.
Two GitHub repository searches returned no matching family-121 project;
that does not establish an implementation gap.

## Family 128: improve existing software

The [paper's construction](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/A-Polynomial-Time-2-Approximation-for-Shortest-Common-Superstring-September-24-2026/build/sections/07-algorithm.tex)
explicitly considers O(L^2) distinct substrings, periodic occurrence
rules, a balanced graph and an Euler traversal. It constructs a string
containing every input contiguously, with length at most twice optimum.
The guarantee concerns output length, not superiority in execution speed
or typical compressed size over greedy algorithms.

Existing [lazy-scs](https://github.com/nurric-ai/lazy-scs/tree/4ee86724b770c54bad400fe077b297288b087c4b)
already uses Rust, a generalized suffix automaton, compressed step-function
counts and lazily enabled periodic rules. It has Python/Windows wheels
and an independent lower-bound checker. The authors report a 46.4-million
input-character run, but that performance has not been reproduced here.
Their documented rare-branch and verification limits remain relevant.
[VeriSCS](https://github.com/buberlo/veriscs) provides another executable
reference and explicitly describes itself as slow, useful as an oracle
rather than production software.

### Concrete optimization opportunity

In pinned [counts.rs, lines 87–127](https://github.com/nurric-ai/lazy-scs/blob/4ee86724b770c54bad400fe077b297288b087c4b/scs/scs-rs/src/counts.rs#L87-L127),
`Counts::compute` collects every successor count-function breakpoint,
sorts and deduplicates them, then loops over **every successor at every
breakpoint**. Each successor query performs another binary search.

An exact replacement can start with the sum at `lo+1`, collect each
successor's value-change event at `segment_start-1`, and sweep those
events in order while maintaining the running sum. Combine simultaneous
events, retain the same breakpoint list, and leave subsequent forced
counts and periodic rules unchanged. A sorted-event version is simpler
than a heap and reuses the existing sort. The intended gain is removing
the repeated all-successor binary searches. This is a source-inferred
opportunity, **not an observed hotspot**. Large alphabets and many count
segments are more promising than DNA's four-letter case.

Second possible target: [sam.rs](https://github.com/nurric-ai/lazy-scs/blob/4ee86724b770c54bad400fe077b297288b087c4b/scs/scs-rs/src/sam.rs#L50-L104)
stores one separately allocated transition vector per automaton state.
A compact frozen representation after construction may reduce allocation
and memory traffic. The builder mutates/clones rows, so first preserve its
behavior, freeze only for later read-only passes, and measure the extra
freeze time and peak memory. This target also requires profiling.

Potential application is a certified string pool for static dictionaries
or overlapping fragments, where each ID can point to a `(offset,length)`
span in a common byte array. It needs a real workload and comparison with
greedy pooling, simple concatenation plus compression, and random-access
cost. Null-terminated APIs and noisy genome assembly are different
requirements. A paper guarantee alone does not establish an application
win.

## Falsifiable 48-hour experiment

1. Pin lazy-scs at the commit above and preserve its MIT attribution.
   The native build is `cargo build --release` in `scs/scs-rs`, then
   `target/release/scs-rs reads.txt --verify` (Windows executable suffix
   as appropriate). Rust/Cargo were absent from PATH in this inspection;
   use a separate local build toolchain. An isolated wheel install can
   establish baseline behavior before native builds.
2. Add stage timers around input reduction, automaton build, count
   calculation, construction, verification and trimming in
   [lib.rs](https://github.com/nurric-ai/lazy-scs/blob/4ee86724b770c54bad400fe077b297288b087c4b/scs/scs-rs/src/lib.rs#L22-L52).
   Record states, edges, breakpoint totals, count passes and lazy rounds.
   Test seeded 0.1/1/10-million-character inputs: four-letter error-free
   fragments; repetitive periodic fragments; byte alphabets of 32/128
   symbols; and a pinned real string-dictionary workload. Use at least
   five seeds, repeated runs, fixed thread/optimization settings, peak
   process memory, and a time limit per case. Separate verifier time.
3. Implement the event sweep in isolation. For every state compare
   complete `r`, `f`, bumps and W to the original; then compare final
   output bytes, lower bound and branch statistics. Run upstream trigger
   fixtures, exhaustive tiny binary instances and seeded random tests;
   check containment independently and exact optimum on tiny cases.
   Do not replace the separate checker with the optimized count code.
4. Continue for a month only if a real target is identified and the
   pilot improves median end-to-end time by at least 15%, or reduces
   peak memory by at least 25%, without output/quality changes and
   without a material regression on the other classes. Include building
   indexes in all timings. A microbenchmark gain alone fails this gate.
   If counts occupy under 15% of runtime, abandon the event-sweep target
   or select a measured different stage before more optimization.

The thresholds are project selection criteria, not predictions. The
first useful deliverable can be a reproducible benchmark and a negative
result; a successful optimization would be separately tested and
published with upstream credit before proposing integration.
