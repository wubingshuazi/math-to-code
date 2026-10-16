# Stage 01 — Source verification and scope

Status: complete. Local client date: 2026-10-17, Asia/Shanghai.

## Objective and authorization

The user wants spare compute used to turn OpenAI math results into useful
software, and authorizes publishing completed results to GitHub with a
100% GPT contribution label. Later the user explicitly authorized all local
compute and asked for checkpoint logs enabling the next AI/chat to resume.

## Evidence

- Official release: https://openai.com/index/sharing-ai-progress-in-mathematics/
- Upstream: https://github.com/openai/math
- Commit `1581d4cbdd69a0faf34b2089614fe2a814316a6a`, committed
  `2026-10-12T21:55:24Z`.
- Initial release had 722 manuscripts; current source lists 719, grouped
  into 372 families. `history.md` records 3 withdrawals. Family IDs extend
  to 377, with gaps; never treat max ID as a count.
- The metadata parser found 719 manuscripts and 372 families, 7 integrity
  checks passed. Broad keyword screening flagged 72 families, manual bounded
  follow-up set has 16. These are not verified practical/novelty counts.
- No trustworthy global count of useful AND unimplemented results has been
  established. Keep these count fields null in the machine-readable output.

## Decisions

- Defer #124 scheduling: explicit polynomial exponent 150020, no practical
  runtime claim. Defer #109/#130 tiny asymptotic exponent savings and #139
  oracle-query savings with unrestricted internal computation.
- #128 shortest superstring already has substantial implementations,
  including nurric-ai/lazy-scs and buberlo/veriscs. Do not duplicate it while
  claiming an untouched research gap.
- First pilot: #276 generalized amplitude damping. Its scalar one-use
  formula predates 2026, so novelty is NOT claimed for a capacity calculator.
  Useful scoped work: formula implementation plus independent numerical
  audits of the source's population-specific and rectangular thermal bounds.
- Existing QuTIpy provides channels and generic optimization; reviewed
  other repos do not establish a specific audit of the new thermal lemma.
  Scope of this search is limited; see research/prior-art.md.

## Artifacts

`research/upstream-contents.md`, `upstream-overview.tex`, `upstream-readme.md`,
`catalogue.json`, `screening.md`, and `scripts/catalogue.py`.
Source descriptions and abstracts are Apache-2.0 materials attributed in NOTICE.

## Reproduction

```console
python scripts/catalogue.py
python scripts/catalogue.py --family 276
```

## Failed approaches worth remembering

The full upstream recursive Git tree response is truncated by the large Lean
tree before preprints. It yielded an empty filtered preprint tree. Query
individual preprint directories with GitHub contents API instead. Raw PDF
web extraction returned unsupported application/octet-stream; use the
paper's build/*.tex sources for precise formulas.
