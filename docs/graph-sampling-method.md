# Degree-preserving graph sampling: kernels, clocks, and mixing

The software targets simple, undirected **labeled** graphs with a fixed degree at each vertex. This is a network null model: it holds the degrees fixed while allowing other structure, such as triangles and connected components, to change. It samples graph realizations, not isomorphism classes.

The reference is OpenAI mathematics family 131, [*Polynomial mixing of the switch chain for every graphical degree sequence* at commit 1581d4cbdd69a0faf34b2089614fe2a814316a6a](https://github.com/openai/math/tree/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Polynomial-Mixing-of-the-Switch-Chain-for-Every-Graphical-Degree-Sequence-September-25-2026). Unmodified source excerpts, citation instructions, and their SHA-256 hashes are preserved in [research/graph131/sources.json](../research/graph131/sources.json).

## State space and practical input/output

For vertices \(V=\{0,\ldots,n-1\}\) and a graphical vector \(d\), let \(\Omega_d\) be all simple undirected graphs with labeled degrees \(d\), and let \(N=|\Omega_d|\). The source uses labels starting at one; shifting labels changes neither kernel.

An edge list needs an explicit vertex count so isolated vertices are retained. Reject loops, repeated edges, and out-of-range endpoints. Keep vertex labels attached to their degrees rather than sorting the degree vector independently. Output the sampled edge list, the seed and kernel, total attempted steps, changed steps, and structural statistics of interest. A degree vector can alternatively be realized by a deterministic Havel--Hakimi construction before the chain runs.

The uniform law \(\pi(G)=1/N\) includes disconnected graphs. Enforcing connectedness, forbidden host edges, or other structural restrictions changes the state space and the analysis. A finite-run output is identified by its step count; the bounds below quantify its distance from uniform when their premises are used. Successive retained graphs along one trajectory can be correlated.

## The paper's lazy four-vertex switch kernel

The exact proposal is specified in the pinned [introduction, before Theorem `thm:main`](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Polynomial-Mixing-of-the-Switch-Chain-for-Every-Graphical-Degree-Sequence-September-25-2026/build/sections/introduction.tex):

1. Stay at the current graph with probability \(1/2\).
2. Otherwise choose an unordered four-element vertex set uniformly.
3. On sorted vertices \(a<b<c<d\), the three perfect matchings are \(\{ab,cd\}\), \(\{ac,bd\}\), and \(\{ad,bc\}\). Choose uniformly one of their six ordered distinct pairs \((F,F')\).
4. If both edges of \(F\) exist and both edges of \(F'\) are absent, replace \(F\) by \(F'\). Otherwise stay.

The two edges in the third matching are unrestricted. Store undirected edges canonically to avoid an additional orientation convention. Explicit holding and rejected proposals both consume a step.

The pinned [mixing proof, `mix:normalization` and `mix:gamma`](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Polynomial-Mixing-of-the-Switch-Chain-for-Every-Graphical-Degree-Sequence-September-25-2026/build/sections/mixing.tex) gives, with \(q=12\binom n4\),

\[
P_{\rm switch}(G,H)=1/q
\]

for every distinct switch neighbor. Its diagonal is \(1-r(G)/q\), where \(r(G)\) counts distinct switch neighbors. The matrix is symmetric and stochastic, so the uniform law is stationary. The source gives gap at least \([24n^2\binom n4]^{-1}\) and worst-start total-variation mixing time to \(1/4\) at most \(2n^8\), for \(n\ge4\). Bounds count attempts, not accepted changes. They can be conservative enough to be unsuitable as an automatic large-graph default.

## The source's pair-resampling / Curveball kernel

The pinned [setup section](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Polynomial-Mixing-of-the-Switch-Chain-for-Every-Graphical-Degree-Sequence-September-25-2026/build/sections/setup.tex) describes a different update already known as an undirected Curveball trade:

1. Choose an unordered pair \(\{i,j\}\) uniformly.
2. Keep edge \(ij\), all edges outside the pair, and all common neighbors unchanged.
3. Form the outside singleton pool: vertices adjacent to exactly one of \(i,j\), excluding \(i,j\) themselves. Let its size be \(s\), and let \(k\) be the number currently assigned to \(i\).
4. Choose a uniform \(k\)-subset of this pool. Assign exactly those vertices to \(i\), and assign the rest to \(j\).

The current subset is one of the possible results and must remain eligible. A pair with no reassignment choice simply gives an identity update, which still consumes a step. There is **no extra half-holding coin** for this heat-bath kernel.

Every update preserves degrees and simplicity. Conditional on the data held fixed, all \(k\)-subsets are feasible and equiprobable. Thus its operator \(E_a\), for a chosen vertex pair \(a\), is a conditional expectation under the uniform graph law. The source credits the undirected Curveball framework to [Carstens, Berger, and Strona (2018), extended version arXiv:1609.05137v3](https://arxiv.org/abs/1609.05137v3). The algorithm is prior work; the following bound is a direct consequence of the operator inequality in the pinned OpenAI proof.

## Derived Curveball spectral and TV bounds

Put \(b=\binom n2\), \(h_a=I-E_a\), and \(H=\sum_a h_a\). One uniform pair update has kernel

\[
P_{\rm curveball}=\frac1b\sum_a E_a=I-\frac Hb.
\]

Each \(E_a\) is an orthogonal projection: it is self-adjoint, positive semidefinite, and a contraction. Consequently \(P_{\rm curveball}\) is symmetric, stochastic, and positive semidefinite. In particular, its eigenvalues are nonnegative without additional laziness.

The pinned [mixing section, `mix:global` and `mix:poincare`](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Polynomial-Mixing-of-the-Switch-Chain-for-Every-Graphical-Degree-Sequence-September-25-2026/build/sections/mixing.tex) establishes \(H^2\succeq H\) and identifies its kernel as the constant functions. On centered functions, every eigenvalue of \(H\) is therefore at least one. When \(N>1\),

\[
\operatorname{gap}(P_{\rm curveball})\ge1/b,
\qquad
0\le\lambda\le1-1/b
\]

for every nonconstant eigenmode. This is a derived bound conditional on the cited operator result, with a clock of one uniformly chosen pair resampling per step.

The density of a point mass relative to \(\pi\), minus one, has squared \(L^2(\pi)\) norm \(N-1\). Spectral contraction and Cauchy--Schwarz give, for every starting state,

\[
\|P_{\rm curveball}^t(G,\cdot)-\pi\|_{\rm TV}
\le\tfrac12\sqrt{N-1}(1-1/b)^t
\le\tfrac12\sqrt N\,e^{-t/b}.
\]

All logarithms below are natural. Since \(N\le2^b\), a computable sufficient step count for \(0<\varepsilon<1/2\), \(n\ge4\), is

\[
\boxed{\displaystyle
t\ge\left\lceil b\left(\frac b2\ln2+\ln\frac1{2\varepsilon}\right)\right\rceil.}
\]

If enumeration supplies \(N>1\), replace \(b\ln2\) by \(\ln N\) for a tighter sufficient count. If \(N=1\), the mixing time is zero. Graphical labeled degree vectors with fewer than four vertices also have a unique realization and can be handled directly. Adding a half-holding coin to Curveball divides its gap by two and requires doubling this sufficient bound. Costs per update differ between the two kernels, so step bounds are not wall-clock comparisons.

## Why accepted changes are a different clock

For the paper's switch chain, deleting holding times leaves a jump chain with

\[
J(G,H)=1/r(G)
\]

on switch neighbors. Its stationary law is

\[
\pi_J(G)=\frac{r(G)}{\sum_H r(H)},
\]

because \(\pi_J(G)J(G,H)\) is the same constant in either direction. This equals the uniform graph law only when switch-neighbor counts are constant. The relevant count \(r(G)\) is a degree in the **state-transition graph**, not the original vertex degrees, which remain fixed.

An exactly enumerable example has \(d=(2,2,2,2,2,2)\). Every realization is either a six-cycle or two disjoint triangles:

- Six-cycles: \((6-1)!/2=60\) labeled realizations. Each has 12 distinct switch neighbors: six disjoint edge pairs admit one replacement, and three opposite edge pairs admit two.
- Two triangles: \(\binom63/2=10\) realizations. Each of the nine pairs consisting of one edge from each triangle admits both replacement matchings, giving 18 distinct neighbors.

Thus the uniform graph law assigns two triangles probability

\[
10/70=1/7,
\]

whereas the successful-move jump law assigns probability

\[
\frac{10\cdot18}{60\cdot12+10\cdot18}=1/5.
\]

Their expected triangle counts are respectively \(2/7\) and \(2/5\). This explains a practical bias from changing the observation clock even though every sampled graph has the correct degrees. Curveball identity trades likewise belong to its specified clock and should not be discarded when interpreting its transition bound.

## Closed-form checks and complete small-state audits

For \(d=(1,1,1,1)\), there are three perfect matchings. The switch matrix has diagonal \(5/6\) and off-diagonal \(1/12\), so its worst-start TV is \((2/3)(3/4)^t\), with \(1/4\) mixing time 4. Curveball has diagonal \(2/3\), off-diagonal \(1/6\), TV \((2/3)(1/2)^t\), and mixing time 2. These identities detect both a missing switch holding factor and an unwanted Curveball holding factor.

For larger enumerable examples, build all labeled realizations, retain rejected/identity probability on the diagonal, and compute the entire transition law. Check row sums, symmetry, invariant degrees, uniform stationarity, and every starting state's TV trajectory. Rational transition construction can be exact; reports should identify whether subsequent matrix powers and TV values use rational arithmetic or floating-point arithmetic. A simulated frequency histogram alone cannot replace this complete-state check.

## Existing software and contribution scope

[NetworkX `double_edge_swap` documentation](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.swap.double_edge_swap.html) defines `nswap` as successful swaps. Its [published source](https://networkx.org/documentation/stable/_modules/networkx/algorithms/swap.html) chooses oriented edges through degree-weighted vertex selection and has a successful-swap stopping condition. It is an existing degree-preserving randomization tool, with a different proposal and clock from the pinned four-vertex kernel. The documentation does not claim that its `nswap` value is the timestep in this paper; no such claim or library defect is inferred here.

The inspected [Sage degree-sequence module](https://github.com/sagemath/sage/blob/develop/src/sage/graphs/generators/degree_sequence.py) provides Havel--Hakimi realization, a configuration pseudograph model, and an expected-degree model through NetworkX. A configuration pseudograph may contain loops and parallel edges; an expected-degree model does not hold every realized degree fixed.

This project's useful contribution is a small, inspectable implementation of both specified clocks, clear inputs and outputs, reproducible examples, complete small-state validation, and a concrete explanation of successful-move bias. The Curveball and switch algorithms themselves retain their existing attribution. The ordinary finite-run samplers are distinct from the paper's separate exact-uniform residual-correction construction.
