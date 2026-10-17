# Practical acceleration screen: caching, scheduling, arithmetic, and matrix functions

Research snapshot: 2026-10-17. **Recommendation: give family 325 one bounded 48-hour feasibility test; do not commit a month to it yet. No second candidate in this screen clears the implementation gate.** Family 110's uniform k-server construction is unsuitable for a practical cache replacement. The other screened arithmetic and scheduling results establish theoretical guarantees without a credible crossover on this laptop.

This is a source-based feasibility assessment. The proposed matrix-function experiment below has not been implemented or benchmarked. Families 104, 120, 121, and 128 are covered by other screens; 107 and 138 are being assessed separately.

## Source snapshot

All OpenAI references below use repository commit `1581d4cbdd69a0faf34b2089614fe2a814316a6a`, the same revision as our local catalogue. Manuscript statements are taken from their actual TeX constructions, rather than inferred from their titles. Existing library code was checked at these revisions:

| Library | Revision and primary source inspected |
|---|---|
| SciPy | [`0feac33c7624d7834bce4d0baf610237dafb4274`, `_expm_multiply.py`](https://github.com/scipy/scipy/blob/0feac33c7624d7834bce4d0baf610237dafb4274/scipy/sparse/linalg/_expm_multiply.py) |
| LeXInt | [`90319e940aec256eec9e340f7469c52054ae33fe`, `Python/real_Leja_exp.py`](https://github.com/Pranab-JD/LeXInt/blob/90319e940aec256eec9e340f7469c52054ae33fe/Python/real_Leja_exp.py) |
| libCacheSim | [`93529a1faef2c57bbdb9323213b78cad2adec1cd`, README and linked policy implementations](https://github.com/1a1a11a/libCacheSim/blob/93529a1faef2c57bbdb9323213b78cad2adec1cd/README.md) |

## Conditional candidate: family 325, fewer sparse matrix products at a fixed error target

**Application:** compute `exp(t A) b` for large sparse, nonnormal advection–diffusion operators, with repeated right-hand sides or time queries. This is the action of a matrix function on a vector; we do not form the dense exponential. Inputs would be a sparse operator, vector, time, requested error, and a supported certified enclosure. Outputs would be the approximation, error estimate, number of operator products, and timings.

The relevant source is [*The complete Crouzeix theorem*](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/The-complete-Crouzeix-theorem-September-23-2026/build/main.tex), especially `cor:polynomial` and `cor:hilbert`. Its stated holomorphic inequality gives the following usable consequence for a polynomial `p_m` and a known outer enclosure `Omega` of the numerical range:

\[
 E_m=\sup_{z\in\Omega}|e^{tz}-p_m(z)|,
 \qquad
 \|(e^{tA}-p_m(A))b\|_2\le 2E_m\|b\|_2.
\]

Thus a smaller certified degree can save sparse matrix–vector products. This is an application of the inequality, not an algorithm supplied by the manuscript. Its optimal-similarity and boundary-density construction does not provide a cheap sparse stopping controller. Computing a full matrix similarity, conformal map, or semidefinite program would defeat this target.

### What could actually be new in the experiment

The generic constant changes from `1 + sqrt(2)` to `2`. This reduces that bound by about 17.2%; it permits a scalar approximation error about 20.7% larger. Neither percentage is a runtime speedup. If `E_m` behaves like `C rho^(-m)`, the continuous degree reduction is only

\[
 \frac{\log((1+\sqrt2)/2)}{\log\rho},
\]

often less than one matrix product. Integer degree selection and setup cost can erase the gain.

There is also a crucial existing competitor: [Beckermann and Crouzeix, *Faber polynomials of matrices for non-convex sets* (2013), Lemma 4 and its convex-set consequence](https://arxiv.org/pdf/1310.1356), already give `||F_j(A)|| <= 2` when the convex set contains `W(A)`. Consequently a Faber-series tail bound `2 sum_{j>m}|a_j|` is older mathematics. Reimplementing that bound cannot be presented as an acceleration obtained from family 325. A direct uniform residual bound can sometimes improve on a coefficient absolute-value sum, but that benefit must also be separated from replacing the generic constant.

The manuscript itself credits independent 2026 proofs of the scalar constant-two result; its wider contribution is the complete inequality for matrix-valued functions. A scalar `exp(tA)b` application therefore is not an exclusively OpenAI-derived result. We should credit the full chain of sources.

### A computable first target

Start with real tridiagonal operators `A = c I + b S + d S*`, where `S` is the length-`n` shift. Its numerical range is the image of the disk of radius `cos(pi/(n+1))` under `w -> c + b w + d conjugate(w)`, giving an explicit ellipse. This elementary structured enclosure avoids expensive numerical-range estimation. Two-dimensional separable operators can use enclosures of their Kronecker sums, with all enlargement charged to the error bound.

Use an established polynomial recurrence. Compute a certified scalar residual bound on the ellipse: an analytic coefficient-tail bound is simplest; a grid bound needs an explicit derivative bound between grid points and outward error allowance. A dense plot of boundary samples by itself is not a certificate. Ritz values and sampled numerical-range points are not safe outer enclosures either.

The theorem controls approximation error in exact arithmetic. Recurrence roundoff and scalar-bound evaluation must have their own allowance. Start at normalized absolute targets `||error||_2 <= tau ||b||_2`, `tau` in `{1e-8, 1e-10, 1e-12}`. For a relative target, do not replace the unknown result norm by `||b||`: if `B` bounds the absolute error and `y` is the approximation, the sufficient check is `B <= rtol ||y||_2/(1+rtol)`.

### Existing baseline behavior that must be preserved

[SciPy's implementation](https://github.com/scipy/scipy/blob/0feac33c7624d7834bce4d0baf610237dafb4274/scipy/sparse/linalg/_expm_multiply.py) already uses trace shifting, norm-based degree/scaling selection, and early termination of Taylor terms. Its public function does not expose a tolerance parameter; the single-time and interval paths set their working tolerance to `2**-53`. The interval path also reuses products across time points. Supply `traceA` for a `LinearOperator` when available, preserve multiple-right-hand-side handling, and compare its interval API for an interval workload.

[LeXInt's real Leja routine](https://github.com/Pranab-JD/LeXInt/blob/90319e940aec256eec9e340f7469c52054ae33fe/Python/real_Leja_exp.py) already accepts a tolerance, applies the operator once per polynomial term, and stops using a term-size estimate. It is an accuracy-configurable baseline, although its term test is not the proposed uniform certificate. An apparent gain from requesting `1e-8` accuracy while SciPy computes near machine precision is an accuracy tradeoff; it does not establish a paper-derived speedup.

### Forty-eight-hour kill test

1. **Hours 0–8: scalar feasibility only.** Fix 12–24 representative ellipse/time/error combinations before timing. Compute valid `E_m` curves and compare three stopping controllers: the same polynomial/enclosure with constants `1 + sqrt(2)` and `2`, and the existing Faber factor-two coefficient-tail controller where applicable. Reject the manuscript-specific acceleration route if it saves no products, if gains occur only at cherry-picked degree boundaries, or if the scalar certificate costs more than the expected savings. Record all degree curves, including ties and failures.
2. **Hours 8–32, only if the first gate passes:** implement the sparse operator-action prototype using the existing Python/SciPy stack. Use sizes roughly `10^4` to `10^6`, subject to actual memory, and include both cold calls and declared operator/coefficient reuse. Count all operator products used by norm estimation, enclosures, and validation. Keep polynomial, dtype, enclosure, and requested accuracy identical in the constant-only ablation.
3. **Hours 32–48:** compare the optimized prototype with SciPy and a tolerance-configurable Leja baseline on held-out operator parameters. Use an independent dense/high-precision reference for small cases and independently tightened reference computations for large ones. Require every reported speedup case to meet the same measured accuracy target. Report all cases and setup amortization, rather than only the winning matrix.

A reasonable continuation gate is at least a 15% geometric-mean end-to-end gain on a clearly named held-out application class, plus a measurable product reduction attributable to the theorem constant rather than a new tolerance or recurrence. A smaller useful gain can still merit publication, but it should not trigger a month-long commitment without evidence of adoption value. If a good solver results but the constant-only ablation saves nothing, describe it as numerical-software engineering, not a family-325 acceleration.

On this i9-14900HX/32-thread, 31.7-GiB machine, begin with CPU CSR operations, fixed thread settings, and a bounded number of concurrent cases. Sparse products often exhaust memory bandwidth before all cores help. GPU porting and a C++ toolchain are subsequent choices; neither is needed to decide this first gate.

## Family 110: reject for practical caching acceleration

The actual uniform construction is in [*Uniform computation of the squared-logarithmic k-server bound*, sections 2–4](https://github.com/openai/math/tree/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Uniform-computation-of-the-squared-logarithmic-k-server-bound-September-24-2026/build/source/sections). Its finite policy has variables for every request word of length at most a derived horizon `H` and every ordered distinct server configuration; there are `n!/(n-k)!` such configurations and exponentially many words. It uses Fourier–Motzkin elimination without an efficient constructor bound. On request `t`, it restarts a capped constructor simulation with `floor(log2(t+1))` steps. If the constructor needs `T_P` steps, activation waits until roughly `2**T_P` requests. The finite initial movement cost is absorbed into an unrestricted instance-dependent additive constant.

The result is a uniform-computability and competitive-movement theorem, not a short-latency eviction algorithm. Small polynomial preprocessing does not build the enormous policy. Reducing the horizon or replacing the policy with a heuristic would remove the theorem's guarantee.

For real caching, [libCacheSim](https://github.com/1a1a11a/libCacheSim/blob/93529a1faef2c57bbdb9323213b78cad2adec1cd/README.md) already supplies LRU, ARC, S3-FIFO, SIEVE, trace replay, and object/byte miss-ratio measurement. The k-server objective must not be confused with those software throughput and byte-cost metrics. There is no justified 48-hour implementation bet here. Reconsider only if a compact policy with an explicit practical horizon/activation bound is independently derived; the current manuscript does not supply it.

## Other construction-level rejections

| Family | Actual construction detail | Practical decision |
|---|---|---|
| 124, three-machine scheduling | [The paper](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/A-polynomial-time-algorithm-for-three-machine-unit-job-scheduling-September-24-2026/paper.pdf) gives a deterministic multitape bound `O((L+2)^150020)` and bounded-description enumeration with fixed `K=10000`. The model has three identical machines, unit jobs, and precedence constraints. | A valuable polynomial-time existence result does not provide a credible scheduler speedup. Pruning descriptions heuristically would require a separate correctness/performance argument. |
| 142, prime-field polynomial factorization | [Driver and complexity sections](https://github.com/openai/math/tree/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Deterministic-Polynomial-Factorization-over-Prime-Fields-October-4-2026/build/sections) use `B=20+(n+1)(ceil(log2 p)+1)`, scalar enumeration in the branch `p <= B^200000`, and an explicit overall polynomial exponent as large as `10^12`. | Determinism is the target guarantee. No supported speed advantage over practical randomized factorization is visible. Do not spend the month reproducing the proof's driver. |
| 130, exact DFT | [The actual all-length construction](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/An-explicit-power-saving-for-the-exact-discrete-Fourier-transform-September-25-2026/build/main.tex) works in exact complex arithmetic with unrestricted coefficients and states saving exponent `10^-13`. | No binary64 stability or useful finite-size crossover follows. A finite gadget might be a separate research question, but the asymptotic theorem alone does not justify replacing FFT libraries. |
| 109, integer multiplication | [The manuscript](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Integer-multiplication-below-n-log-n-September-23-2026/paper.pdf) states exponent saving `2^-182` on a fixed finite-alphabet multitape Turing machine. | The stated saving is not evidence of a feasible crossover against native multiprecision libraries on this computer. No implementation allocation is recommended from that bound alone. |

The next concrete action supported by this screen is the family-325 scalar feasibility gate. It can cheaply produce either a reproducible rejection or a focused sparse-solver experiment, before consuming weeks of compute.
