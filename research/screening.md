# Reproducible mathematics-to-code screening

Audit date: 2026-10-17 (Asia/Shanghai). Upstream commit: `1581d4cbdd69a0faf34b2089614fe2a814316a6a`.
[Pinned CONTENTS.md](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/CONTENTS.md); [pinned overview.tex](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/overview.tex).
The overview itself is dated October 6, 2026. The audit date is not the publication date of each paper.

Parsed **719 manuscripts in 372 result families**, with every title, PDF URL and abstract retained in `catalogue.json`.
Family identifiers run from 001 to 377; omitted identifiers are 045, 061, 070, 123, 163. Identifiers are preserved, not renumbered.
The user's figure of 722 is not the manuscript count in this pinned snapshot. Revisions can change counts.

## What the counts do and do not establish

The disclosed metadata heuristic flags **72 families**. A manually selected follow-up set contains **16 families**. Neither number counts proven practical applications.
The number of results with practical programming value is **unknown**. The number whose applications nobody has implemented is **unknown**. This screening neither establishes theorem correctness nor performs a worldwide novelty search.
The upstream README says the collection is at different verification stages and some unformalized results could have issues. A catalogue assertion is not an independent correctness audit.

## Manual follow-up candidates

These are candidate experiments, not implementation-completeness or usefulness claims. Only family 276 is selected as the initial small one-use Holevo scalar-formula pilot; its regularized-capacity interpretation is conditional on the upstream theorem. The other entries need full-paper review before implementation commitments.

| Family | Possible executable artifact | Why review / limitation |
|---|---|---|
| [104](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Turn-Based-Stochastic-Mean-Payoff-Games-in-Deterministic-Quasipolynomial-Time-October-5-2026/stochastic-mean-payoff-games.pdf) | Game solver | Exact mean-payoff/stochastic/parity game outputs; inspect constants and implementable subroutines. |
| [110](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Squared-logarithmic-randomized-k-server-on-arbitrary-metrics-September-24-2026/Squared-logarithmic-randomized-k-server-on-arbitrary-metrics-September-24-2026.pdf) | Online k-server experiment | Finite rational metrics have a stated polynomial implementation; audit preprocessing and movement constants. |
| [113](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/A-Fully-Polynomial-Randomized-Approximation-Scheme-for-Perfect-Matchings-in-General-Graphs-September-23-2026/main.pdf) | Perfect-matching counter | FPRAS and exact zero detection; compare against exact enumeration on small graphs. |
| [114](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/An-FPRAS-for-Common-Integer-Polymatroid-Bases-with-Binary-Capacities-October-5-2026/polymatroid-fpras.pdf) | Polymatroid-base counter | FPRAS in a rank-oracle model; charge oracle work explicitly in experiments. |
| [115](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Exact-Uniform-Sampling-of-Contingency-Tables-with-Arbitrary-Margins-September-24-2026/main.pdf) | Contingency-table sampler/counter | Useful finite inputs and structural zeros; audit transition details and polynomial constants. |
| [116](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Uniform-Matrix-Hitting-Points-in-Every-Positive-Characteristic-October-4-2026/uniform-matrix-hitting-points-positive-characteristic.pdf) | Noncommutative identity tester | Construct explicit hitting tuples; audit field representations and output sizes. |
| [120](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Almost-Linear-Time-Maximum-Cardinality-Matching-in-Sparse-General-Graphs-September-24-2026/main.pdf) | General-graph matching solver | Concrete output and near-linear asymptotic claim; audit crossover sizes and randomized failure checks. |
| [121](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/An-Almost-Linear-Approximation-Scheme-for-Edit-Distance-September-24-2026/paper.pdf) | Edit-distance approximator | Compare accuracy/time with exact dynamic programming; asymptotic fixed-epsilon guarantee does not establish practical speed. |
| [125](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Single-Exponential-Recovery-and-Bounded-Price-Strictness-for-Metric-k-Median-September-24-2026/paper.pdf) | Metric k-median approximator | Finite rational facility instances; inspect dependence on epsilon and algorithmic constants. |
| [128](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/A-Polynomial-Time-2-Approximation-for-Shortest-Common-Superstring-September-24-2026/paper.pdf) | Shortest-common-superstring approximation | Concrete string output with a claimed factor-two guarantee. Existing implementations include [nurric-ai/lazy-scs](https://github.com/nurric-ai/lazy-scs) and [buberlo/veriscs](https://github.com/buberlo/veriscs); this is not an empty implementation gap. Audit and compare existing work first. |
| [131](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Polynomial-Mixing-of-the-Switch-Chain-for-Every-Graphical-Degree-Sequence-September-25-2026/main.pdf) | Fixed-degree graph sampler | Edge-switch chain is directly experimentable; O(n^8) worst-case mixing is not a practical runtime promise. |
| [138](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Subset-Sum-in-Time-2-power-0-49n-October-4-2026/subset-sum.pdf) | Subset-sum solver | Compare against meet-in-the-middle on fixed inputs; exponential memory, constants and word assumptions need auditing. |
| [142](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Deterministic-Polynomial-Factorization-over-Prime-Fields-October-4-2026/Deterministic-Polynomial-Factorization-over-Prime-Fields.pdf) | Prime-field polynomial factorizer | Concrete coefficients/factors; benchmark against existing factorization libraries and inspect polynomial exponent. |
| [174](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/The-strong-thin-tree-conjecture-September-23-2026/paper.pdf) | Thin spanning-tree constructor | Concrete tree and cut inequalities; inspect the universal constant and construction overhead. |
| [178](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Deterministic-nonbipartite-Ramanujan-graphs-in-every-fixed-degree-September-23-2026/paper.pdf) | Ramanujan-graph constructor | Concrete adjacency list; fixed-degree exponent and sufficiently-large-n threshold require auditing. |
| [276](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Classical-capacity-and-entropy-inequalities-for-generalized-amplitude-damping-September-24-2026/paper.pdf) | Generalized amplitude-damping one-use Holevo calculator and conditional capacity audit | Explicit one-variable maximization has a small numerical implementation surface; validate endpoints and Holevo ensembles. Related one-use formulas already exist. Any interpretation as regularized classical capacity is conditional on the upstream theorem; this is an engineering/audit pilot, not a novelty claim. |

## Deferred or excluded from the first practical pilot

These exclusions concern the first engineering pilot, not the mathematical importance of the research.

| Family | Reason |
|---|---|
| [102](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/The-Unique-Games-Theorem-September-23-2026/paper.pdf) | Hardness/approximation thresholds constrain algorithms; they are not an algorithmic speedup. |
| [103](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Exact-Derandomization-of-Logarithmic-Space-L-equals-RL-equals-BPL-September-23-2026/paper.pdf) | An effective log-space compiler is stated, but the metadata does not make its polynomial exponent or practical compilation cost usable. |
| [107](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Matrix-Multiplication-Nine-Fourths-October-2-2026/paper.pdf) | An arithmetic matrix-multiplication exponent is not evidence of a usable BLAS replacement; tensor sizes, constants and numerical stability need review. |
| [109](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Integer-multiplication-below-n-log-n-September-23-2026/paper.pdf) | The exponent saving is kappa = 2^-182; no useful finite-input speedup follows from the asymptotic statement. |
| [111](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/One-Sample-Suffices-for-Matroid-Prophet-Inequalities-against-an-Almighty-Adversary-September-23-2026/final.pdf) | The metadata explicitly says no polynomial-time implementation is asserted. |
| [122](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Uniform-quasipolynomial-time-trace-reconstruction-October-5-2026/uniform-trace-reconstruction.pdf) | General fixed-deletion trace reconstruction has quasipolynomial bounds and a superpolynomial sample lower bound; not a low-cost first pilot. |
| [124](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/A-polynomial-time-algorithm-for-three-machine-unit-job-scheduling-September-24-2026/paper.pdf) | The linked paper's stated bound is O((L+2)^150020) deterministic multitape steps; polynomial does not mean practical. |
| [130](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/An-explicit-power-saving-for-the-exact-discrete-Fourier-transform-September-25-2026/main.pdf) | The exponent saving is delta = 10^-13 in exact complex arithmetic with unrestricted coefficients; no practical FFT improvement is established. |
| [137](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Simulating-One-Tape-Time-in-Two-Fifths-Power-Space-September-25-2026/article.pdf) | Space improves but simulation time is explicitly unrestricted. |
| [139](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Subpolynomial-query-complexity-for-well-conditioned-log-concave-sampling-September-26-2026/article.pdf) | Only exact value-and-gradient oracle-query complexity is bounded; computation between queries is unrestricted. |
| [141](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Existential-universal-real-sentences-in-the-counting-hierarchy-October-4-2026/etr-counting-hierarchy.pdf) | A counting-hierarchy membership theorem is not a practical real-polynomial solver. |
| [283](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Polynomial-Time-Unitary-Synthesis-from-a-Boolean-Oracle-October-5-2026/paper.pdf) | The target-dependent Boolean oracle may have an unrestricted truth table; efficient construction is not asserted. |

## Transparent heuristic

Case-insensitive regular expressions are applied to the concatenated family title, summary, manuscript titles and abstracts. All matching rule names are recorded per family. No score or probability is inferred. The full regex strings are recorded in `catalogue.json` and in `scripts/catalogue.py`.

| Rule | Regex |
|---|---|
| algorithm | `\balgorithms?\b` |
| complexity_or_runtime | `\b(?:computational\|complexity\|running.time\|bit.time\|polynomial.time\|word.time)\b` |
| sampling_or_counting | `\b(?:sampl(?:e\|es\|ing)\|counting\|decoder\|reconstruction)\b` |
| approximation | `\b(?:approximat(?:e\|es\|ion)\|derandomization\|identity.testing)\b` |
| numerical_formula | `\b(?:one.variable\|explicit.formula\|variational.formula\|exact.coefficient\|capacity)\b` |
| construction | `\b(?:deterministic.construction\|constructive\|constructively)\b` |

Known limitations: keyword false positives include hardness theorems, existence results and mathematical approximation unrelated to an efficient program. False negatives include useful implicit constructions or numerical bounds without these words. Manual candidates reflect a bounded audit, not exhaustive review.

## Reproduce and query

No network access or third-party packages are required after downloading the pinned input files. From the repository root:

```text
python scripts/catalogue.py
python scripts/catalogue.py --family 276
python scripts/catalogue.py --query sampling
```

The first command rebuilds both generated outputs and checks the header counts, all family IDs, unique manuscript paths, nonempty abstracts and subject coverage. `--family` and `--query` only print existing catalogue records and do not change files. Input SHA-256 hashes are stored in `catalogue.json` so snapshot drift is detectable. All generated PDF links pin the exact upstream commit.

Candidate queries for a separate prior-art review (record search date and inspected results): `"generalized amplitude damping" capacity python`, `"generalized amplitude damping" Holevo`, and the exact manuscript title plus `implementation` or `GitHub`. An absent search hit cannot establish that nobody has implemented something.

## All heuristic hits

| Family | Title | Matching rules | Manual status |
|---|---|---|---|
| 004 | Hilbert’s tenth problem over ℚ | algorithm | not_manually_reviewed |
| 006 | Goldfeld’s conjecture: densities and mean analytic rank | sampling_or_counting | not_manually_reviewed |
| 009 | Function-field reconstruction from Milnor K-theory and Galois data | sampling_or_counting | not_manually_reviewed |
| 028 | Uniformly bounded components of Gaussian-prime graphs | sampling_or_counting | not_manually_reviewed |
| 077 | Fourier restriction for positively curved surfaces | numerical_formula | not_manually_reviewed |
| 087 | The Mahler conjectures, functional inequalities and polar-product symplectic width | numerical_formula | not_manually_reviewed |
| 100 | Cylinder coverings below the half-area bound | approximation | not_manually_reviewed |
| 102 | The Unique Games Conjecture and optimal approximation thresholds | complexity_or_runtime, approximation | deferred_first_pilot |
| 103 | Exact derandomization of logarithmic space: $`\mathsf L=\mathsf{RL}=\mathsf{BPL}`$ | complexity_or_runtime, approximation | deferred_first_pilot |
| 104 | Quasipolynomial algorithms for mean-payoff, stochastic and parity games | algorithm, complexity_or_runtime | follow_up_candidate |
| 106 | Hardness of coloring three-colorable graphs | complexity_or_runtime | not_manually_reviewed |
| 108 | A cubic permanent–determinant lower bound | complexity_or_runtime | not_manually_reviewed |
| 109 | Integer multiplication below $`n\log n`$ | algorithm | deferred_first_pilot |
| 110 | Optimal-order randomized k-server on arbitrary metrics | algorithm, complexity_or_runtime | follow_up_candidate |
| 111 | One-sample matroid prophet inequalities against an almighty adversary | algorithm, complexity_or_runtime, sampling_or_counting | deferred_first_pilot |
| 112 | Beyond the square-root exponent for depth-three circuits | complexity_or_runtime | not_manually_reviewed |
| 113 | Approximate counting and entropy of perfect matchings | algorithm, complexity_or_runtime, sampling_or_counting, approximation | follow_up_candidate |
| 114 | Approximate counting of common integer polymatroid bases | algorithm, sampling_or_counting, approximation | follow_up_candidate |
| 115 | Sampling and counting contingency tables with arbitrary margins | algorithm, complexity_or_runtime, sampling_or_counting, approximation | follow_up_candidate |
| 116 | Uniform black-box noncommutative identity testing across characteristics | complexity_or_runtime, approximation | follow_up_candidate |
| 120 | Almost-linear-time exact matching and prescribed-degree factors in general graphs | algorithm, complexity_or_runtime | follow_up_candidate |
| 121 | Almost-linear approximation of edit distance | algorithm, approximation | follow_up_candidate |
| 122 | Quantitative trace-reconstruction bounds with a uniform decoder | algorithm, complexity_or_runtime, sampling_or_counting | deferred_first_pilot |
| 124 | Polynomial-time scheduling on three identical machines | algorithm, complexity_or_runtime | deferred_first_pilot |
| 125 | The metric k-median approximation threshold and recovery | algorithm, complexity_or_runtime, approximation | follow_up_candidate |
| 126 | Exponential semidefinite complexity of perfect matching | complexity_or_runtime | not_manually_reviewed |
| 128 | A factor-two approximation for shortest common superstring | algorithm, complexity_or_runtime, approximation | follow_up_candidate |
| 130 | Exact Fourier transforms below $`n\log n`$ | algorithm, sampling_or_counting | deferred_first_pilot |
| 131 | Rapid mixing of graph switches for every degree sequence | algorithm, complexity_or_runtime | follow_up_candidate |
| 133 | The computational complexity of Weisfeiler–Leman refinement | complexity_or_runtime | not_manually_reviewed |
| 135 | Homogeneous depth-five lower bounds for iterated matrix multiplication | complexity_or_runtime | not_manually_reviewed |
| 136 | A quasilinear PCP theorem for PPAD | complexity_or_runtime | not_manually_reviewed |
| 137 | One-tape time simulation in two-fifths-power space | complexity_or_runtime | deferred_first_pilot |
| 138 | Subset Sum in $`O(2^{0.49n})`$ time | algorithm, complexity_or_runtime | follow_up_candidate |
| 139 | Subpolynomial query complexity for log-concave sampling | algorithm, complexity_or_runtime, sampling_or_counting | deferred_first_pilot |
| 140 | Memory–sample lower bounds for noiseless Gaussian regression | sampling_or_counting | not_manually_reviewed |
| 141 | Existential–universal real sentences in the counting hierarchy | sampling_or_counting | deferred_first_pilot |
| 142 | Deterministic polynomial factorization over prime fields | algorithm, complexity_or_runtime | follow_up_candidate |
| 143 | Hilbert's sixteenth problem: uniform bounds for limit cycles | sampling_or_counting | not_manually_reviewed |
| 151 | A C1 counterexample to the entropy conjecture | complexity_or_runtime | not_manually_reviewed |
| 153 | Arithmetic classification and non-Pisot singularity for Bernoulli convolutions | algorithm, approximation | not_manually_reviewed |
| 174 | Deterministic construction of strong thin spanning trees | algorithm, complexity_or_runtime, construction | follow_up_candidate |
| 175 | Talagrand’s expectation thresholds, discrete convexity, and graph decompositions | sampling_or_counting | not_manually_reviewed |
| 178 | Deterministic nonbipartite Ramanujan graphs in every fixed degree | algorithm, complexity_or_runtime | follow_up_candidate |
| 206 | Finite lattice representation and undecidability | algorithm | not_manually_reviewed |
| 218 | Conformal universality for weakly interacting and random-bond Ising models | approximation | not_manually_reviewed |
| 222 | Perceptron free energies and microscopic jamming exponents | numerical_formula | not_manually_reviewed |
| 223 | Random-cluster interfaces: critical, disordered, thermal, and natural-time scaling | sampling_or_counting, approximation | not_manually_reviewed |
| 227 | Critical SK autocorrelation processes and dynamics across the temperature transition | sampling_or_counting | not_manually_reviewed |
| 229 | Exact three- and four-state reconstruction thresholds and four-state tree capacity | sampling_or_counting, numerical_formula | not_manually_reviewed |
| 233 | The joint critical Ashkin–Teller current limit | approximation | not_manually_reviewed |
| 234 | All-temperature pressure of orthogonally invariant Ising spin glasses | numerical_formula | not_manually_reviewed |
| 235 | Limiting random SAT thresholds, sharp variance and computability | approximation | not_manually_reviewed |
| 243 | Separating choiceless counting from polynomial time and witnessed choice | complexity_or_runtime, sampling_or_counting | not_manually_reviewed |
| 251 | Amenability, unitarizability, and strong Ulam stability | approximation | not_manually_reviewed |
| 265 | Area laws and tensor networks for two-dimensional gapped systems | approximation | not_manually_reviewed |
| 271 | Bloch's law, its lattice correction, and the spherical magnetization law | numerical_formula | not_manually_reviewed |
| 273 | The entropy photon-number inequality | numerical_formula | not_manually_reviewed |
| 275 | QMA-hardness of continuum Coulomb energy | complexity_or_runtime | not_manually_reviewed |
| 276 | Classical capacity of generalized amplitude damping | numerical_formula | follow_up_candidate |
| 279 | Exact quantum factoring over a fixed finite gate set | complexity_or_runtime | not_manually_reviewed |
| 281 | QAOA attains the SK optimum in the thermodynamic-first limit | algorithm, approximation | not_manually_reviewed |
| 282 | From scale symmetry to local conformal symmetry in four-dimensional QFT | sampling_or_counting | not_manually_reviewed |
| 283 | Polynomial-time unitary synthesis from a Boolean oracle | complexity_or_runtime, approximation | deferred_first_pilot |
| 284 | The optimal quartic separation between randomized and quantum queries | complexity_or_runtime | not_manually_reviewed |
| 298 | Two notions of free entropy differ even when both are finite | approximation | not_manually_reviewed |
| 300 | Approximation and quadratic strong-operator paving | approximation | not_manually_reviewed |
| 326 | The cotype–cotype conjecture under the approximation property | approximation | not_manually_reviewed |
| 330 | A uniformly discrete counterexample to bounded approximation in Lipschitz-free spaces | approximation | not_manually_reviewed |
| 343 | Symplectic ball packing in higher dimensions | numerical_formula | not_manually_reviewed |
| 349 | The Solomon–Yau least-volume conjecture | sampling_or_counting | not_manually_reviewed |
| 368 | The three-dimensional Ball–Evans approximation problem | approximation | not_manually_reviewed |
