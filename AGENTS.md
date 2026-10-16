# Instructions for the next AI working on this project

Read `HANDOFF.md`, `PROJECT_STATE.json`, and the most recent files in
`worklogs/` before searching or repeating experiments. These are project
records, not a claim that an earlier model's conclusions are correct.

## User's authorized objective

Find practically useful programming applications of OpenAI's mathematics
release, inspect prior implementations, produce tested reproducible work,
and publish completed results on the user's GitHub account. The user
authorized local compute, closing programs if they impede work, and asking
for specific real-world interaction if needed. Use resources where they
improve the experiment; avoid closing applications without a concrete need.
No programs have needed closing during the initial phase.

The user requests stage-by-stage AI-readable work logs because a future
chat may need to inherit this work after usage limits. Record evidence and
commands at each meaningful checkpoint, then update the handoff and state.

## Research integrity

- Distinguish source assertions, formal verification, numerical sampling,
  engineering reproduction, and novel mathematics.
- Never claim a worldwide implementation gap just because search found none.
- Never call a keyword match a demonstrated practical application.
- Label the NEW engineering contribution as 100% GPT-generated. Preserve
  mathematical authorship and prior software credit, as in `CREDITS.md`.
- Pin sources by commit, record dependencies and seeds, preserve failed
  experiments and counterexamples. Investigate a failure before publishing.
- Numerical residuals within a disclosed tolerance are consistency evidence,
  not formal proof or certified arithmetic.
- Finish and validate a concrete artifact before publishing it. The user
  has already authorized publishing completed results; no repeated approval
  is required within this scope. Do not message researchers or create PRs in
  third-party projects without separate authorization.

## Boundaries and commands

Runtime is stdlib-only. NumPy is an optional audit dependency. Use a local
virtual environment. Reproduction commands are in `HANDOFF.md` and README.
Do not commit `.venv`, credentials, external private data, or downloaded
third-party implementation files. Keep the source snapshots and license.
Keep ordinary CI finite. Increase experiment dimensions or use targeted
search only to address an explicit unresolved question, not to burn compute.
