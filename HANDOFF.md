# Resume here

Last checkpoint: 2026-10-17 (Asia/Shanghai). Read `PROJECT_STATE.json` for
current status and `worklogs/` for evidence, failed approaches and decisions.

Repository: https://github.com/wubingshuazi/math-to-code

First release: https://github.com/wubingshuazi/math-to-code/releases/tag/v0.1.0

Second phase: see `docs/SHARPNESS_RESULTS.md` and stage05 in `worklogs/`.
v0.2.0 adds a proof-derived quantitative thermal bound, structured equality
families, 191,995 parallel-search evaluations and 80/160-digit confirmation.

The initial engineering phase is complete and published. All four CI jobs
(Windows/Linux, Python 3.10/3.14) passed for code commit
`4572d1eda3a0e014b475264e5f23838ed68bdad7`:
https://github.com/wubingshuazi/math-to-code/actions/runs/38949983630
Those checks describe the first release. Current second-phase validation
and publication status are recorded in `PROJECT_STATE.json`.

## User goal and standing authorization

Use the user's spare compute to implement genuinely useful applications
from OpenAI's mathematical manuscripts. Inspect prior work, reproduce
results honestly, and publish completed work to their GitHub account with
new engineering work marked **100% GPT-generated**. The user authorized
all local compute and necessary real-world questions, and explicitly asked
for these handoff logs because model usage may run out.

## What exists

- Complete pinned catalogue: 719 manuscripts / 372 families, not 722 active
  papers. 72 broad metadata hits, 16 follow-up candidates; unknown number
  of practically useful, unimplemented applications.
- Working dependency-free GAD Holevo calculator and CSV scanner (#276).
- Independent Kraus/eigenvalue audit, thermal-lemma audit, benchmark, tests.
- Source/predecessor attribution and explicit numerical limitations.
- Repository-specific instructions in `AGENTS.md`.
- `math_to_code.thermal.gap_lower_bound` and CLI `thermal-bound`, with a full
  endpoint-mixture/Pinsker derivation in docs/thermal-stability-derivation.md.
- Completed perturbation study and independent factor/SVD +80/160-digit
  replay. Reports, figure and research artifact manifest are in results/.
- 31 local tests pass, including high-precision, record-preservation and
  extreme small-row arithmetic tests.

## Commands

On this Windows checkout the audit interpreter is `.venv\Scripts\python.exe`.
Use your local environment's equivalent on another machine.

```console
python -m unittest discover -s tests -v
python scripts/catalogue.py
python -m math_to_code gad --gamma 0.35 --nu 0.2
python scripts/validate_quantum.py
python scripts/validate_thermal.py
python scripts/benchmark.py
```

Runtime needs Python 3.10+. Pinned audits need Python 3.12+ (tested 3.14)
and `requirements-audit.txt`.

Research experiments additionally use `requirements-research.txt`.

```console
python scripts/check_thermal_stability.py
python scripts/thermal_perturbations.py
python scripts/confirm_thermal.py
python scripts/plot_thermal_sharpness.py
```

Search journals are retained locally and in the v0.2.0 release ZIP. Rerunning
search requires an unused directory: `--output results/run-002/search.json`.

## Next research direction

Inspect source `research/screening.md` and the prior-art audit before
choosing another family. For any proposed engineering gap, first read its
actual construction and inspect existing code. Exclude impractical hidden
constants or unrestricted-oracle claims from the first performance pilot.
The proposed numerical tracks in `docs/NEXT_RESEARCH.md` have now been
executed; preserve that file as the original plan. The study produced an
explicit quantitative corollary and equality constructions. Open choices:
seek a sharper interior bound or equality classification, formalize the
short corollary, or choose another practically constructive family from
the screened list. The constrained search used its evaluation budget on
127/128 starts, so targeted refinement is possible; all best feasible points
are saved. Read stage05 before doing more runs. Preserve useful failures.

## Claims to avoid

No global novelty count, first-GAD-implementation claim, certified arithmetic
or benchmark speedup. The quantitative corollary has a written derivation;
do not inflate it into an independent proof of the source theorem or a
historical-priority claim. Preserve original mathematical attribution.
