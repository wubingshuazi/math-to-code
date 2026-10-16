# Prior-art check and contribution scope

Checked on **2026-10-17**. This is a scoped engineering review, not an exhaustive literature review, a historical-priority determination, or a count of all unimplemented results.

## What this project contributes

An independently written implementation of the generalized amplitude-damping (GAD) scalar Holevo optimization, together with reproducible numerical audits of the population-dependent output-entropy bound and the rectangular thermal entropy lemma in OpenAI mathematics family 276. The implementation, test inputs, tolerances, parameters, and measured residuals are inspectable.

The project does **not** claim to introduce the scalar formula, be the first GAD simulator, prove an additivity theorem, verify an upstream formalization, or demonstrate that nobody else has implemented this result. It supplies a small auditable reproduction and a targeted experimental validation harness.

## Pinned source and mathematical scope

The inspected release is [openai/math at commit 1581d4cbdd69a0faf34b2089614fe2a814316a6a](https://github.com/openai/math/tree/1581d4cbdd69a0faf34b2089614fe2a814316a6a). The current repository describes its verification status and cautions that unformalized results can have issues. Treat repository manuscripts as attributed claims with their stated verification status.

The [family 276 manuscript introduction](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Classical-capacity-and-entropy-inequalities-for-generalized-amplitude-damping-September-24-2026/build/paper.tex) explicitly credits earlier ordinary-amplitude-damping formulas and Hou and Fang (2007) for characterization and numerical evaluation of the generalized channel's one-use optimum. Its claimed extension is the removal of block regularization and additivity with arbitrary finite-dimensional partner channels. Evaluating the one-use scalar expression alone is therefore a reproduction of an older computable formula.

The targeted new-lemma audit reads the pinned [thermal theorem source](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Classical-capacity-and-entropy-inequalities-for-generalized-amplitude-damping-September-24-2026/build/sections/thermal.tex), including its rectangular matrices, normalization, coefficient determinant constraint, entropy units, and equality case. The independently constructed matrix and eigenspectrum checks test finite samples only. A source copy and SHA-256 check prevent accidental drift between the source recorded and the source audited.

The [channel output section](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Classical-capacity-and-entropy-inequalities-for-generalized-amplitude-damping-September-24-2026/build/sections/output.tex) states the stronger population-dependent bound across tensor powers. The [special cases](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Classical-capacity-and-entropy-inequalities-for-generalized-amplitude-damping-September-24-2026/build/sections/special.tex) give endpoint and thermal-duality checks. Numerical agreement does not establish the corresponding all-input, all-dimension claims.

## Existing implementations inspected

| Primary repository | Directly observed overlap | Difference from this project's scoped audit |
| --- | --- | --- |
| [sumeetkhatri/QuTIpy](https://github.com/sumeetkhatri/QuTIpy) | Its [channel source](https://github.com/sumeetkhatri/QuTIpy/blob/master/qutipy/channels.py) supplies GAD Kraus operators and tensor products; its [entropy source](https://github.com/sumeetkhatri/QuTIpy/blob/master/qutipy/entropies.py) supplies generic Holevo and minimum-output-entropy numerical optimization using a random initial point. | Already covers general channel calculations. The inspected functions do not present this pinned rectangular thermal-lemma sampling protocol. That observation is limited to the files reviewed. |
| [vnourozi/quantum-channel-capacity-simulator](https://github.com/vnourozi/quantum-channel-capacity-simulator) | Its README and [channels.py](https://github.com/vnourozi/quantum-channel-capacity-simulator/blob/main/channels.py) include GAD Kraus operators and coherent-information / quantum-capacity-bound calculations. | Coherent information and unassisted classical Holevo information are different quantities. The reviewed code is not an implementation of the rectangular entropy-lemma audit. |
| [magnuax/bloch-map](https://github.com/magnuax/bloch-map) | README describes visualization of qubit channels as affine transformations of the Bloch sphere. | A channel-geometry visualizer does not supply the specific theorem audit implemented here. |

**Parameter convention:** In QuTIpy, `generalized_amplitude_damping_channel(gamma, N)` uses `N = nu`, the stationary excited population in the manuscript. In vnourozi's reviewed `gadc_Kraus(gamma, Nth)`, the ordinary-damping Kraus pair has weight `Nth`, so that parameter corresponds to `1 - nu`. Comparing both programs at the same numerical thermal argument without this conversion can give misleading results. Thermal duality makes the optimized capacity symmetric, but the channel action and signal population still differ.

No code from these repositories was incorporated into the independent audit script. QuTIpy's source is AGPL-3.0; this review describes its functions rather than importing their implementation.

## Why shortest common superstring was not selected as an untouched gap

Primary GitHub repository searches returned multiple family 128 implementations. In particular, [nurric-ai/lazy-scs](https://github.com/nurric-ai/lazy-scs) already describes compressed counts, lazy periodic rules, Rust and Python implementations, Windows wheels, and an independent checker. It reports large-input experiments and lists limitations including incomplete rare-branch coverage and an unverified Rust implementation. Its existence is enough to reject an assertion that this family has no implementation; its own correctness and benchmark claims were not independently reproduced here.

Other directly inspected repository pages are [buberlo/veriscs](https://github.com/buberlo/veriscs), [bkarak/shortest-superstring-js](https://github.com/bkarak/shortest-superstring-js), and [rongou/superstring-rs](https://github.com/rongou/superstring-rs). They describe different verified-reference, executable, and partial implementations. Their descriptions should not be conflated with independently established verification of every source file.

## Search record and limits

The review used the official manuscript catalogue, actual TeX source, primary repository READMEs and source files, public GitHub repository-search API results, and web-index searches restricted to GitHub pages. Example queries included:

- `"superstring" "openai"` — GitHub repository search returned `nurric-ai/lazy-scs` and `buberlo/veriscs`.
- `"2-approximation" "superstring"` — GitHub repository search returned `rongou/superstring-rs`, `bkarak/shortest-superstring-js`, and `buberlo/veriscs`.
- `"forced occurrence" "superstring"` — the repository search returned no match. This is not evidence that the concept is unimplemented: lazy-scs directly documents it.
- GAD-related project searches and source inspection covered the three channel repositories listed above; local search snapshots in this research folder record additional intake queries.

Repository search covers indexed names, descriptions, and README text according to GitHub's search behavior. It is not a complete search of all public code, unpublished work, package registries, private repositories, or all forks. Web results may lag repository updates. Consequently, the justified outcome is **a useful, explicitly scoped contribution**, not a first-implementation or originality claim.

## Attribution

The new audit code and this review were prepared by GPT at the user's direction. Mathematical results and earlier software retain their original attribution. Describing the newly written implementation as GPT-generated must not transfer authorship of the underlying mathematics or imply OpenAI sponsorship or endorsement.
