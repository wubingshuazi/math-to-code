# Stage 02 — Formula implementation and independent audits

Status: engineering and initial tests complete; publication checkpoint is
recorded separately after all final checks. Client date: 2026-10-17.

## Implementation

- `math_to_code/gad.py`: stdlib-only, bit entropy, stable small-eigenvalue
  calculation, phase-pair Holevo objective, concave scalar golden search,
  explicit identity/reset/unital cases and thermal reflection.
- `math_to_code/__main__.py`: JSON for a single parameter pair, CSV sweep.
- No API calls, paid services, GPU code, background service, or app closures.
- `nu` is stationary EXCITED-state population. Some other packages reverse
  this convention. `tolerance` bounds numerical search width in p, not a
  certified information error.
- For gamma=.35, nu=.2: one-use Holevo value .55707889036718 bits,
  p approximately .46061004. Classical-capacity interpretation depends on
  the source theorem, which these tests do not prove.

## Validation design

- `tests/test_gad.py`: 15 stdlib tests, including direct Kraus calculations,
  exact endpoint/unital expectations, thermal duality, and grid comparison.
- `scripts/validate_quantum.py`: NumPy Kraus/eigenspectrum route, independent
  of determinant formula. Initial default run: 36 parameter pairs, 432
  two-/three-qubit entropy samples, 72 random block ensembles and 72 product
  phase-pair attainment checks. Max scalar/matrix error about 1.55e-15 bits.
- `scripts/validate_thermal.py`: directly constructs the rectangular thermal
  matrix in the pinned source. Includes saturation, almost-singular,
  zero-coefficient, near-equality and rectangular-shape cases.
- `scripts/benchmark.py`: 4281 pairs/run, 3 runs; median .343 seconds on this
  machine, 300 separate dense-grid comparisons. A local timing measurement,
  not evidence of speedup over another package.
- Preserve report JSON as authoritative if later runs change these numbers.

## Environment

Windows, Intel Core i9-14900HX (32 logical CPUs), RTX 4060 Laptop GPU.
Runtime Python 3.14.3. Audit venv uses NumPy 2.5.4. Runtime package itself
has no third-party dependency. Use `.venv/Scripts/python.exe` locally.

## Next checks before publishing

Read all completed audit reports; run final unit tests, packaging check,
metadata rebuild, and any independent code-review fixes. Do not label finite
samples as a proof. Then publish to user-owned `wubingshuazi/math-to-code`
and record commit/release/CI status in the next checkpoint.
