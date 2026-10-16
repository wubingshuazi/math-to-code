# A quantitative residual bound and exact equality families

This note derives an explicit corollary of the pinned thermal proof and standard quantum Pinsker inequality. It also records equality constructions useful for interpreting numerical searches. No historical-priority claim is made.

## Definitions and dependencies

Use the matrices and nonnegative coefficients from [OpenAI's thermal theorem, commit 1581d4cbdd69a0faf34b2089614fe2a814316a6a](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Classical-capacity-and-entropy-inequalities-for-generalized-amplitude-damping-September-24-2026/build/sections/thermal.tex). Put

\[
A=XX^*,\quad B=YY^*,\quad C=XY^*,\qquad
\operatorname{Tr}A=\operatorname{Tr}B=1,
\]

\[
U_0=\alpha+\beta,\quad U_1=\eta+\delta,\quad
K^2=\alpha\delta-\beta\eta\ge0,\quad
u=U_0U_1-K^2=\beta U_1+\eta U_0.
\]

All four coefficients sum to one, so \(U_0+U_1=1\). Write

\[
T=\begin{pmatrix}\alpha A+\beta B&KC\\KC^*&\eta A+\delta B\end{pmatrix},
\quad
R=S(T)-(\alpha+\eta)S(A)-(\beta+\delta)S(B)-g(u).
\]

Entropy and relative entropy use **natural logarithms**. The norm \(\|\cdot\|_1\) below is the full trace norm, not half the trace norm.

The nonnegative endpoint residuals used below are precisely the consequences of the [zero-block theorem `thm:block`](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Classical-capacity-and-entropy-inequalities-for-generalized-amplitude-damping-September-24-2026/build/sections/block.tex) used in the thermal proof. Thus the quantitative bound depends on those endpoint estimates; it is not an independent proof of that upstream theorem.

For the other input, [Carlen and Lieb, *Remainder Terms for Some Quantum Entropy Inequalities*, arXiv:1402.3840v2, page 3, Eq. (2.6)](https://arxiv.org/pdf/1402.3840v2#page=3) states quantum Pinsker in the required convention:

\[
D(\rho\|\sigma)=\operatorname{Tr}\rho(\ln\rho-\ln\sigma)
\ge\tfrac12\|\rho-\sigma\|_1^2.
\]

As a second reference, [Watrous, *The Theory of Quantum Information*, Theorem 5.38, Eq. (5.190)](https://cs.uwaterloo.ca/~watrous/TQI/TQI.pdf) gives the base-two form with coefficient \(1/(2\ln2)\). Multiplying relative entropy by \(\ln2\) gives the natural-logarithm coefficient above.

## Proposition: an explicit lower bound on the residual

If \(U_0U_1>0\), then

\[
\boxed{\displaystyle
R\ge \frac{\beta\eta}{2U_0U_1}\|A-B\|_1^2.}
\]

Consequently, when \(\beta\eta>0\), equality in the thermal inequality requires \(A=B\).

**Proof.** First suppose \(u>0\). Take the endpoint coefficient tuples from the source proof:

\[
(\alpha_1,\beta_1,\eta_1,\delta_1)
=(K^2/U_1,u/U_1,0,U_1),
\]

\[
(\alpha_2,\beta_2,\eta_2,\delta_2)
=(U_0,0,u/U_0,K^2/U_0).
\]

Let \(T_i\) be the corresponding block states and set

\[
w_1=\beta U_1/u,\qquad w_2=\eta U_0/u.
\]

They satisfy \(w_1+w_2=1\) and \(T=w_1T_1+w_2T_2\). Their scalar term \(g(u)\) is the same. If \(R_i\) denotes their thermal residual, linearity of the remaining terms gives the exact decomposition

\[
R=J+w_1R_1+w_2R_2,\qquad
J=S(T)-w_1S(T_1)-w_2S(T_2).
\]

The endpoint estimates give \(R_i\ge0\). For positive weights, expansion of relative entropy gives

\[
J=w_1D(T_1\|T)+w_2D(T_2\|T).
\]

The support of each endpoint state is contained in the support of their positive mixture, so the relative entropies here are well defined and finite. Pinsker, together with \(T_1-T=w_2(T_1-T_2)\) and \(T_2-T=-w_1(T_1-T_2)\), yields

\[
J\ge\tfrac12w_1w_2\|T_1-T_2\|_1^2.
\]

Direct block subtraction gives

\[
T_1-T_2=
\operatorname{diag}\!\left(\frac{u}{U_1}(B-A),\frac{u}{U_0}(B-A)\right).
\]

Trace norm adds over direct sums, hence

\[
\|T_1-T_2\|_1
=u(1/U_0+1/U_1)\|A-B\|_1
=\frac{u}{U_0U_1}\|A-B\|_1.
\]

Finally, \(w_1w_2=\beta\eta U_0U_1/u^2\), which gives the displayed bound. If an endpoint weight is zero, its right-hand side is zero and the endpoint estimate supplies \(R\ge0\) directly. If \(u=0\) while both row sums are positive, \(u=\beta U_1+\eta U_0\) forces \(\beta=\eta=0\); the bound again reduces to the source's zero-block estimate. This exhausts \(U_0U_1>0\). If a row sum vanishes, the fraction is not defined and must not be evaluated; the original concavity boundary case applies instead. \(\square\)

The bound is independent of matrix dimensions. It can be tested numerically by inspecting the strengthened residual \(R-\beta\eta\|A-B\|_1^2/(2U_0U_1)\), using the same logarithm and trace-norm conventions.

## Proposition: a sufficient equality family beyond identical matrices

For \(X\in\mathbb C^{d\times e}\), let \(U\) be a unitary on the row-index space \(\mathbb C^d\), assume \(UA=AU\), and take \(Y=UX\). Then equality holds for every admissible coefficient tuple.

Indeed, \(B=UAU^*=A\) and \(C=AU^*\). For

\[
M=\begin{pmatrix}U_0&K\\K&U_1\end{pmatrix},\qquad
W=\operatorname{diag}(I,U),
\]

one obtains exactly \(T=W(M\otimes A)W^*\). The state \(M\) has determinant \(u\), so \(S(T)=g(u)+S(A)\), equal to the proposed lower expression. This includes a relative global phase and nontrivial commuting unitary rotations.

The necessary condition \(A=B\) in the interior is **not sufficient by itself**. For example, take row vectors \(X=(1,0)\), \(Y=(0,1)\), so \(A=B=1\) but \(C=0\). Whenever \(K>0\), the residual is \(h(U_0)-g(u)>0\). Cross-Gram information matters even when the two output Grams coincide.

Two boundary reductions further explain optimizer behavior:

- If \(K=0\), the coefficient matrix has rank one, and \(R=S(rA+sB)-rS(A)-sS(B)\), where \(r=\alpha+\eta\), \(s=\beta+\delta\). For positive \(r,s\), equality is exactly \(A=B\); if a column weight vanishes, equality is automatic.
- If \(u=0\) and both row sums are positive, then \(\beta=\eta=0\). The nonzero spectrum of \(T\) is that of \(\alpha X^*X+\delta Y^*Y\). Strict entropy concavity shows equality is exactly \(X^*X=Y^*Y\). In particular, \(Y=UX\) works for any left unitary here, even if the output Grams do not commute.

These are proved equality constructions and boundary characterizations, not a complete interior classification.

## What follows for small perturbations

Fix coefficients with \(u>0\) and take a **full-row-rank** matrix \(X\). Let

\[
Y_\varepsilon=(X+\varepsilon H)/\|X+\varepsilon H\|_{\rm HS},
\qquad \operatorname{Re}\operatorname{Tr}(HX^*)=0.
\]

At zero, \(A\), \(B\), and \(T=M\otimes A\) are positive definite. Entropy is smooth in a neighborhood. The nonnegative residual vanishes at zero, so its first derivative vanishes and \(R(\varepsilon)=O(\varepsilon^2)\). Furthermore,

\[
B_\varepsilon-A=\varepsilon D+O(\varepsilon^2),\qquad
D=HX^*+XH^*.
\]

If \(\beta\eta>0\) and \(D\ne0\), the quantitative bound proves

\[
\liminf_{\varepsilon\to0}\frac{R(\varepsilon)}{\varepsilon^2}
\ge\frac{\beta\eta}{2U_0U_1}\|D\|_1^2>0.
\]

Thus these directions have \(R(\varepsilon)=\Theta(\varepsilon^2)\). If \(D=0\), this lower bound does not identify the leading order: cross-Gram changes can still create a quadratic term, while symmetry directions can remain exactly flat. If \(X\) is rank deficient, or \(u=0\), the smoothness argument does not apply. In particular, a `3x2` matrix is necessarily row-rank deficient; a logarithmic correction near a newly opening eigenvalue is possible.

For numerical identification, remove scalar and phase directions but also account for common right-unitary transformations, common left-unitary conjugation, and the commuting-unitary equality family above. Hilbert--Schmidt orthogonality to \(X\) alone does not remove all such directions. Small curvature in redundant coordinates is therefore not automatically an additional equality family.
