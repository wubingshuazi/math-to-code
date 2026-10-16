# Stage 05 — Quantitative thermal bound and sharpness study

Client date: 2026-10-17, Asia/Shanghai. User asked for less defensive
communication and encouraged continuing research. New engineering,
mathematics derivation and experiments remain GPT-generated.

## Main result

Derived from the pinned thermal proof's endpoint mixture and quantum
Pinsker: R >= beta*eta/(2 U0 U1) ||XX*-YY*||_1² in nats. Full derivation,
support assumptions, boundaries and sources in
`docs/thermal-stability-derivation.md`. Three agents independently checked
the coefficient algebra/conventions; Carlen–Lieb arXiv1402.3840v2 Eq2.6
confirms the natural-log Pinsker factor1/2.

This gives a reusable stdlib function `math_to_code.thermal.gap_lower_bound`
and CLI `thermal-bound`. It is a corollary using the source endpoint
estimates. Preserve that dependency in subsequent reasoning.

Additional deductions: Y=UX with U commuting XX* is an equality family;
interior equality requires XX*=YY* but that alone is insufficient. At u=0,
equality is equivalent to X*X=Y*Y when both row sums are positive. For
full-row-rank X, u>0, beta*eta>0 and nonzero first Gram derivative D,
R(eps)=Theta(eps²). Rank-deficient tall cases require separate analysis.

## Completed experiments

- 4,146 matrix cases +2 scalar cases check the stronger bound, structured
  equality families and a same-Gram-but-positive-gap example.
- 396 perturbation paths /3,168 evaluations. Same deterministic inputs as
  selected JSON; generic tangent excludes radial and global phase directions.
  108 resolved slopes in [1e-4,1e-2] range1.86975–2.08518. New bound covers
  0.78%–89.47% of resolved residuals.
- Parallel search:128starts,24processes,1BLASthread each,191,995objective
  callbacks,6.99sec measured walltime. Best feasible R=3.632746197e-5nats,
  start57. 127starts hit1500eval budget;1reported optimizer success. Do not
  describe the whole search as converged minima. Full candidate inputs saved.
- Independent weighted-Gram-factor/SVD route agrees on9selected candidates.
- 9candidates+36perturbation points evaluated at80and160decimal digits:
  90HP computations,45precision comparisons passed. Smallest resolved R
  about2.2583e-17nats; signs and positive strengthened margins agree.
- Full 128worker journals:27,681,145uncompressed bytes, archived to
  4,207,603bytes; manifest hashes in results/research_artifacts.json.

## Implementation/verification lessons

- Constrained normalization parameters have scale/phase redundancies; only
  accept candidates after independent feasibility checks, not success flags.
- Deadline checks now cover initialization as well as objective/constraints;
  wall limits remain cooperative with process startup/join overhead.
- Search refuses existing output/journal directories. Two tests ensure old
  results are preserved. Use a fresh run directory for future searches.
- HP coefficient preflight uses exact rational decimal parsing to preserve
  exact K=0 cases. Direct float subtraction would invent a negative tiny
  determinant. Input normalization is recorded explicitly at each precision.
- Source JSON inputs hashed by HP reports have -text Git attributes so
  Windows/Linux checkout preserves their exact bytes.
- 31tests pass locally, including7HP reference,2record-preservation and
  2extreme-small-row tests.
  NumPy/mpmath/SciPy tests skip in dependency-free runtime environments.
- Final independent review caught a fixed absolute determinant tolerance
  that admitted infeasible tiny rows. The core API now checks the decimal
  coefficient determinant with exact Fractions and evaluates scaled ratios
  to avoid subnormal product underflow. Both reproducing cases are tests.
- Archive headers now fix platform and Unix permission fields. The manifest
  also records the zlib runtime; identical compressed bytes require the same
  compression implementation, while per-journal SHA256 is universal.

## Reproduction

Install requirements-research.txt with Python3.12+ (tested3.14), then:

```console
python scripts/check_thermal_stability.py
python scripts/thermal_perturbations.py
python scripts/confirm_thermal.py
python scripts/plot_thermal_sharpness.py
python -m unittest discover -s tests -v
```

To search again, use a new directory:

```console
python scripts/search_thermal.py --starts 128 --workers 24 --output results/run-002/search.json
```

The remaining publication checkpoint records v0.2.0, CI and release assets.
