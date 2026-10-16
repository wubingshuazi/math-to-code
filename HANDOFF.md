# Resume here

Last checkpoint: 2026-10-17 (Asia/Shanghai). Read `PROJECT_STATE.json` for
current status and `worklogs/` for evidence, failed approaches and decisions.

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

## Next research direction

Inspect source `research/screening.md` and the prior-art audit before
choosing another family. For any proposed engineering gap, first read its
actual construction and inspect existing code. Exclude impractical hidden
constants or unrestricted-oracle claims from the first performance pilot.
For #276, a useful next step may be a targeted adversarial search near
thermal-lemma equality cases or an independent formal-proof audit; neither
is completed by the initial random experiments. Do not rerun all easy tests
just to consume compute. Preserve counterexamples if a check fails.

## Claims to avoid

No global novelty count, no first-GAD-implementation claim, no newly proved
mathematics, no certified floating-point capacity interval, no benchmark
speedup. Never attribute original mathematics or NumPy to this project's
100% GPT engineering label.
