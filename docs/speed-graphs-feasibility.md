# Speed project feasibility: matching 120 and games 104

Client date: 2026-10-17, Asia/Shanghai. New analysis: 100% GPT-generated.
This is a source and engineering feasibility audit, not a measured speedup.

**Decision:** do not spend the proposed one to two months implementing the
complete family 120 near-linear matching algorithm. Its checked parameter
range excludes physical input sizes. Family 104 has executable, finite
recursion and deserves a bounded experiment if a narrow formal-verification
application is acceptable; its practical advantage is unmeasured.

## 120: a concrete reason the fast branch cannot run

Pinned source root:
[OpenAI family 120](https://github.com/openai/math/tree/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Almost-Linear-Time-Maximum-Cardinality-Matching-in-Sparse-General-Graphs-September-24-2026).
The actual TeX construction was fetched through the GitHub API and read,
including sections 03 through 09. The obstacle below is a necessary
prerequisite, not an estimate obtained by substituting into big-O notation.

The [priced-step engine, section 5](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Almost-Linear-Time-Maximum-Cardinality-Matching-in-Sparse-General-Graphs-September-24-2026/build/sections/05-engine.tex)
requires integer `a >= 1000`, and a backend size `M = 2^u <= S^2`, where
`S` is the master instance size. The
[routing helper, equation route:parameters](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Almost-Linear-Time-Maximum-Cardinality-Matching-in-Sparse-General-Graphs-September-24-2026/build/sections/06-routing-helper.tex)
sets

```text
b = M^(1/a²)
Λ = 2^(1000 a²) (1 + u)
P* = Λ^(400 a²)
checked prerequisite: P* <= b
```

Taking binary logarithms gives a directly checkable necessary condition:

```text
u / a² >= 400 a² [1000 a² + log2(1 + u)]
u >= 400000 a^6 + 400 a^4 log2(1 + u)
log2(S) >= u/2 > 200000 a^6 >= 2 × 10^23.
```

Thus `S` must exceed `2^(2 × 10^23)` even at the smallest engine parameter.
This is an input-size prerequisite. Extra CPU time or GPU memory cannot
make a real graph pass it. Section 7 repeats this guard and adds others.
The source algorithm suspends inadequate parameter branches; section 9
also runs a deterministic classical fallback, which supplies the answer
at small sizes. Calling the fallback a new near-linear implementation
would misattribute its performance.

This does not refute an asymptotic theorem. It shows why this particular
construction is an unsuitable practical acceleration commitment. Reducing
these constants without losing correctness would be a new research
problem, not routine tuning.

Additional implementation burden includes an exact dyadic optimization
engine, signed link-cut-tree path accounting, a dynamic minimum-ratio
cycle backend, recursive verified covers, resource-preserving routing,
and exact integral-flow calls. Implementing one of these components may
be useful, but no isolated component was shown here to accelerate an
existing workload because of the new matching theorem.

### Baselines and failure handling

The primary practical comparison should be compiled unweighted matching,
not Python weighted matching with all edge weights equal to one:

- [Boost maximum-cardinality matching](https://www.boost.org/doc/libs/develop/libs/graph/doc/html/graph/algorithms/network_flow/maximum_matching.html)
  provides Edmonds matching and a checked variant. We inspected its
  [actual implementation at commit 3cd4aa3](https://github.com/boostorg/graph/blob/3cd4aa314683c92266ca636109cce8802f40ce14/include/boost/graph/max_cardinality_matching.hpp).
  It initializes with extra-greedy matching and augments until exhausted.
  Its verifier makes an augmentation attempt, then checks a Tutte–Berge
  certificate using the resulting vertex labels. A valid edge set alone
  is insufficient to certify maximum size.
- [Ansaripour, Danaei and Mehlhorn, 2024](https://arxiv.org/abs/2409.14849)
  already implemented Gabow's `O(m sqrt(n))` algorithm in C++ with LEDA
  and published experiments. Their random-graph results illustrate that
  classical implementations can look nearly linear on easy inputs even
  when their worst-case bounds differ.
- [NetworkX max_weight_matching](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.matching.max_weight_matching.html)
  is useful as an independent small-instance oracle. It solves the more
  general weighted problem and documents cubic time. Beating it with C++
  does not establish benefit from family 120.

Maximum cardinality means maximizing the number of disjoint pairs in an
unweighted general graph. Weighted scheduling, length-three exchange
cycles, approximate matching, and merely maximal mesh coarsening have
different objectives; their users cannot be counted as direct beneficiaries
without a concrete reduction and workload. No existing user's bottleneck
has yet been measured here. No matching speedup benchmark was run because
the source guard already gives a decisive rejection of the full route.

If matching is revisited, cap its first experiment at two days: build
Boost and a practical Gabow/Micali–Vazirani baseline; use sparse random,
odd-cycle/blossom, long augmenting-path and published hard families; time
input conversion, solving and verification separately; require identical
cardinalities and certificate success. A theorem-inspired prototype must
identify the exact new subroutine it uses. Stop if it is only a language
rewrite or the fast branch never gets past its prerequisites.

## 104: a plausible, narrower experiment

Pinned source:
[Deterministic quasipolynomial-time mean-payoff games](https://github.com/openai/math/tree/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Deterministic-quasipolynomial-time-mean-payoff-games-September-25-2026).
All nine section files were fetched and inspected. The concrete target is
the exact zero-threshold winning set for a finite directed, sinkless,
two-player graph with signed binary integer rewards. This is relevant to
quantitative verification and resource-control synthesis, not ordinary
video-game rendering or AI training.

The [six-step procedure](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Deterministic-quasipolynomial-time-mean-payoff-games-September-25-2026/build/source/sections/04-algorithm.tex)
uses exact integer boxes, rational masses, simultaneous coordinate updates,
and recursive labels. It has no equivalent giant-input guard. Its base
case uses a clamped min/max operator at width below 4096. Wider boxes use
two pivot passes, a half-width child, and a reweighted continuation.
Consequently the mathematical routine is implementable without an
unrestricted oracle. The shared finite-box comparison lemma comes from
the randomized companion and must be audited there before claiming a
full independent mathematical validation.

The practical risk is recursive overhead. The source permits as many as
`2048 n + 3` mass-budget-decreasing children per node; the mass budget is
`1 + floor(log_(32/25)(n²))`. Worst-case asymptotic improvement does not
establish that a small or medium instance runs faster. Existing solvers
may finish in only a few useful iterations.

### Relevant mature comparison and public inputs

- [Fast value iteration, Cadilhac–Casares–Ohlmann, TACAS 2025](https://link.springer.com/chapter/10.1007/978-3-031-90653-4_16)
  evaluates PPI/DPPI/QDPM and strategy checking on actual energy games.
  This is a better direct baseline for the threshold problem than a
  parity-only solver. Match objective, sign convention and zero ties.
- [Its reproducible benchmark collection](https://github.com/michaelcadilhac/game-benchmarks/tree/1e7b325e06fe806649a8072a0ebe37702e6ef80f)
  includes synthetic and verification-derived parity games plus a seeded
  generator for energy games. The full generated set is over 50 GB;
  generate a bounded subset rather than all of it during feasibility work.
- [Oink](https://github.com/trolando/oink/tree/8fbf0a7c3e5b0baa254cb4516258c5c42fa99db1)
  is a mature C++ parity solver with multiple algorithms and solution
  verification. Use it on parity-derived cases only. Its recursive
  quasipolynomial implementations are useful engineering references,
  but the stock parity API does not directly solve arbitrary mean-payoff
  input.

### A specific 48-hour feasibility gate

1. Implement a literal integer/rational reference of the deterministic
   procedure, instrumenting calls, edge scans, base iterations, maximum
   stack and bit lengths. Do not silently alter the 4096 base threshold
   or substitute floating-point masses.
2. Check tiny graphs against independent exhaustive positional strategies,
   exact reachable-cycle means, and zero-weight ties. Include self-loops,
   parallel edges, mixed signs, disconnected components and constant
   shifts of rewards. The source's transform is `(n+1)w+1`; changing the
   sign of its final one changes tie semantics.
3. Use the same implementation language and graph representation for
   the old and new bottleneck when establishing an algorithmic gain.
   Compare direct energy/mean-payoff baselines and run verification on
   every output. A timeout or call-budget exhaustion is a recorded
   failure, not a win or a guessed partition.
4. Sweep roughly 8–128 vertices and 8, 32, 64, 128 and 256 reward bits,
   within explicit per-case time/memory limits. Separate random easy cases,
   crafted long-improvement cases and genuine verification-derived cases.
   Scaling rewards by a common positive integer is a useful invariance
   test, but cannot be the entire speed claim because preprocessing may
   remove that scale.
5. Continue to a one-month engineering effort only after independently
   checked outputs and a reproducible advantage on a meaningful workload
   family. Publish distributions and regressions, not only a best ratio.
   Otherwise retain the reference/checker and change candidates.

No family 104 prototype or head-to-head timing was produced during this
audit; its status is **implementable candidate, performance unknown**.

## Source replay notes

Source TeX was inspected locally under ignored `.verification/speedgraphs/`.
Useful exact-byte SHA-256 checks:

```text
120 build/sections/05-engine.tex
939f221a14b39eee8ab0aca6417de5502983842c4f2d23579e00b4ea5f0885d3
120 build/sections/06-routing-helper.tex
25f5c0ecdcdd291635a76fa9acab05f7af3053165c3998cfed1535d6b22a7cd2
120 build/sections/07-backend-quality.tex
01699a433457bc787331cc2e76f8e99aa7697206be49ab7a639d43653d379401
120 build/sections/09-uniformization.tex
7c4f2d2ec41daf7f7d2113370d8f06c8f23de9ac87aa809135f357999342eed0
104 build/source/sections/04-algorithm.tex
74715cfe52b2223f6bfe7bd7c2c08bb30cbabe7a65753776770d96048b887673
104 build/source/sections/06-complexity.tex
b841542374a82a78719d2edb7626889205ed9ca3eb0747868b2ebb083426620c
```
