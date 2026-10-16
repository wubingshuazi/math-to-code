# Proposed next study: sharpness of the thermal entropy inequality

**Status: proposed, not implemented or executed.** The existing random audit is a separate completed experiment. No optimization results, high-precision confirmations, or mathematical advances are claimed by this plan.

## Research question

Investigate where the rectangular thermal inequality becomes sharp, how its residual grows near equality, and whether noncommuting examples expose unexpected nearly sharp behavior. This is more informative than repeating generic random sampling because it examines equality structure, local curvature, and boundary behavior. It remains an empirical study unless accompanied by a mathematical argument.

## Fixed mathematical target

Use [the thermal theorem at upstream commit 1581d4cbdd69a0faf34b2089614fe2a814316a6a](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Classical-capacity-and-entropy-inequalities-for-generalized-amplitude-damping-September-24-2026/build/sections/thermal.tex), labels `thm:thermal`, `eq:thermal-condition`, `eq:thermal-state`, and `eq:thermal-bound`. Keep its exact hypotheses and natural-logarithm entropy convention:

- Complex matrices `X` and `Y` have the same rectangular shape, with `Tr(XX*) = Tr(YY*) = 1`; `*` means conjugate transpose.
- Nonnegative `alpha`, `beta`, `eta`, and `delta` sum to one.
- `K = sqrt(alpha*delta - beta*eta)` is real and nonnegative.
- `U0 = alpha + beta`, `U1 = eta + delta`, and `u = U0*U1 - K^2`.
- Form `T` with diagonal blocks `alpha*XX* + beta*YY*` and `eta*XX* + delta*YY*`, and off-diagonal blocks `K*XY*` and `K*YX*`.

Minimize the residual

`R = S(T) - (alpha+eta)*S(XX*) - (beta+delta)*S(YY*) - g(u)`,

where `S(P) = -Tr(P ln P)` and `g(u) = h((1+sqrt(1-4u))/2)`. The paper asserts `R >= 0` and explicitly identifies equality when `X = Y`. The latter is a known equality family, not a claimed exhaustive classification.

Verify the pinned source hash before a future run. Validate coefficient constraints, normalization, Hermiticity, trace, and positivity explicitly for every retained candidate. Do not repair a materially infeasible candidate by clipping or normalization after recording its objective.

## Three bounded search tracks

1. **Search away from obvious equality.** Use shapes `2x2`, `2x3`, and `3x2`. As an initial restricted domain, require each coefficient to be at least `0.02`, both `K^2` and `u` to be at least `0.005`, and `||XX*YY* - YY*XX*||_F >= 0.03`. First find feasible starting points; do not assume every proposed combination is feasible. Run independent constrained local searches from different feasible starts. These extra restrictions select an informative subdomain; they are not hypotheses added to the theorem. Preserve unconstrained baseline examples separately. Accept an optimizer's result only after independently rechecking feasibility.

2. **Probe local sharpness.** Start with `X = Y` and perturb one matrix along fixed complex directions, renormalizing the perturbed matrix as part of the input parameterization. Use amplitudes `10^-1` through `10^-8`. Include full-rank and nearly rank-one starting matrices, and record residual versus amplitude. Test whether the observed behavior is quadratic, flatter, or compatible with singular logarithmic terms. Use directional curvature only as a diagnostic; unstable finite differences are not evidence of negative curvature. Any claimed scaling law remains an empirical observation until justified analytically.

3. **Probe coefficient and rank boundaries.** Approach `K = 0`, `u = 0`, vanishing coefficient rows, and rank-deficient Gram matrices along documented paths. Keep these runs separate from the interior constrained search. Record which limits have exactly known equality and which exhibit genuinely unexplained small residuals.

## Identifiability and numerical traps

Minimizing `R` without restrictions will tend to recover known equality examples. A small optimum by itself therefore says little. Also, `X != Y` in Frobenius distance does not establish separation from equality. Relative global phases can change their distance while leaving the relevant entropy unchanged, and simultaneous right-unitary multiplication of `X` and `Y` preserves all three Gram products. A common left unitary conjugates the output and likewise preserves its entropy. These symmetries produce unidentifiable directions and zero curvature in redundant coordinates.

Control normalization, align removable phases when measuring distance, and account for these gauge directions before interpreting a Hessian or a perturbation exponent. Do not claim that the noncommuting-Gram constraint excludes every possible equality family. A complete equality characterization is itself an unresolved question for this proposed study.

Near singular matrices, entropy is sensitive to tiny eigenvalues, and subtracting nearly equal entropies can overwhelm a small residual. Eigenvalue clipping, finite-difference step size, and an optimizer's feasibility tolerance can all create artificial improvements. Log raw feasibility errors and spectral diagnostics alongside the objective.

## Independent confirmation and suspected failures

Use two independently assembled spectral calculations for the best candidates:

- Directly construct `T` and diagonalize it with a Hermitian eigensolver.
- Reconstruct `T` from the two Gram factorizations and mixture weights in the pinned proof, and calculate its spectrum from squared singular values of the combined factor. Calculate `S(XX*)` and `S(YY*)` independently from singular values as well.

Compare the reconstructed matrix, trace, spectrum, and residual against the direct route. The factorization formulas involving row sums or `u` require separate handling when a denominator vanishes; do not apply the interior formula blindly at endpoints.

If a negative residual appears, save its full input immediately, then recompute the same candidate at 80 and 160 decimal digits with an independent high-precision Hermitian spectral calculation. Recheck the hypotheses at that precision and report whether the sign and magnitude persist. Preserve the original candidate even if refinement removes the discrepancy. High precision is not a rigorous interval bound. A confirmed numerical discrepancy is a candidate counterexample requiring further checking; it is not an automatic disproof or permission to announce a theorem failure.

## Compute budget and reproducibility

The proposed first run has a **10-minute wall-clock limit**, a maximum of **128 optimization starts**, and a maximum of **1,500 objective evaluations per start**. Allocate work across the three tracks before launching; these are total limits, not a separate allowance for each track. Reserve the final two minutes for validation and artifact writing. Expensive confirmation work must fit within the same limit or remain explicitly pending.

On the described machine with 32 logical CPUs, use at most **24 worker processes** and **one BLAS/OpenMP thread per worker**, configured before importing numerical libraries. Lower concurrency if memory pressure or interactive use makes that appropriate. On Windows, use process spawning with a guarded program entry point. Give each worker its own derived random seed and output journal. The controller must enforce the global deadline, stop dispatching starts in time to drain workers, and retain completed records if interrupted.

Checkpoint every candidate improvement in append-only JSONL. Save full real and imaginary matrix entries, coefficients, random seed, initialization, optimizer settings and termination reason, feasibility errors, spectra, objective evaluations, elapsed time, source commit/hash, and library versions. Save suspected failures before any polishing or projection. Merge worker journals only after preserving their originals, and keep a small set of complete replayable candidate files for independent confirmation.

## Expected deliverable and limits

A useful outcome is a reproducible map of sharp or nearly sharp cases, reliable local-scaling observations, or a carefully preserved discrepancy. A null search should report its domain, constraints, budgets, and attained residuals without treating the absence of a counterexample as proof.

Local searches do not certify a global minimum, a derivative calculation in redundant coordinates does not identify equality, finite dimensions do not cover all rectangular shapes, and high-precision evaluation does not validate the universal theorem. Any proposed equality or stability relationship must be clearly labeled a conjecture until a proof is supplied.
