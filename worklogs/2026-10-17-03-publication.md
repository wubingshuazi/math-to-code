# Stage 03 — Reproducible publication checkpoint

Status: initial project published; code CI passed. Client date: 2026-10-17.

## Remote artifacts

- Public repository: https://github.com/wubingshuazi/math-to-code
- Validated code commit: `4572d1eda3a0e014b475264e5f23838ed68bdad7`
- All 4 CI jobs passed:
  https://github.com/wubingshuazi/math-to-code/actions/runs/38949983630
- Matrix: Windows/Linux on Python 3.10 and 3.14. Full NumPy audits on 3.14;
  stdlib tests and installed CLI on all versions.
- Published release: https://github.com/wubingshuazi/math-to-code/releases/tag/v0.1.0
- Release attachments: Python wheel, quantum/thermal JSON reports, GAD CSV
  scan and SHA256SUMS. The attached wheel's SHA-256 is
  `7c3e50365fc4fb6d7e666673c141c80151707d7420a621f0a4a0ff9816918f34`.

## Final verification and actual fixes

- 15 local tests passed, wheel built and installed, installed CLI returned
  the expected .55707889036718-bit sample result.
- Exported staged files into a clean verification directory. Rebuilt the
  catalogue there: all 7 integrity checks passed. Thermal audit ran from
  that clean copy with its exact pinned source hash intact.
- Fixed a discovered packaging issue before publication: the original
  ignore pattern excluded the thermal source required by the audit. Added
  an explicit exception and verified clean export.
- Added Git attributes preserving hashed upstream snapshot bytes across
  Windows/Linux checkout. These original snapshots retain CRLF and some
  upstream whitespace, which a broad whitespace checker flags. Newly
  written source/doc paths passed the scoped whitespace check. Do not alter
  hashed provenance files cosmetically without regenerating their hashes.
- Independent review identified audit-version ambiguity: NumPy 2.5.4 needs
  Python >=3.12 although runtime is >=3.10. README/HANDOFF now distinguish
  those requirements. Added Python 3.10 CI coverage.

## Final research evidence

- Thermal audit: 10,240 cases, 7,299 noncommuting Gram cases, zero violations
  exceeding 2e-10 nats. Min residual -8.77e-15 nats; equality max absolute
  residual 1.10e-14 nats. This is numerical consistency only.
- Quantum audit: finite two-/three-qubit inputs and independent matrix
  path. The actual source theorem remains outside the proof scope.
- No original mathematical theorem, worldwide implementation gap, certified
  numerical interval, or comparative software speedup has been established.
- Existing generic GAD code and earlier scalar formulas are credited.

## Resume

Read HANDOFF.md -> PROJECT_STATE.json -> docs/NEXT_RESEARCH.md. Use existing
source pins, venv and logs; don't redo intake work. For the next completed
phase, add a new checkpoint and preserve all failed hypotheses or inputs.
Publishing completed work within this project is already authorized by the
user. No researcher outreach, API spending, or background schedule was set up.
