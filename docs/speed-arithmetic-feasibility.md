# Arithmetic speedup feasibility: families 107 and 138

Checked 2026-10-17, Asia/Shanghai. New analysis: 100% GPT-generated.
Source commit: `openai/math@1581d4cbdd69a0faf34b2089614fe2a814316a6a`.

## 107: not currently a finite BLAS replacement

Read the actual [matrix-multiplication manuscript](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Matrix-Multiplication-Nine-Fourths-October-2-2026/build/paper.tex).
Its introduction explicitly scopes the theorem to the asymptotic arithmetic
exponent and does not specify a competitive finite matrix size. In the
final algorithm paragraph, it fixes epsilon, then uses existence of a fixed
size u and a rank decomposition of T_u of length below u^(9/4+delta).
That existence argument does not give us a small concrete decomposition
with coefficients, a practical crossover, or floating-point stability.

Searching finite rank decompositions could itself be a substantial research
project. This inspection has not found an explicit implementation target
that should outperform mature matrix-multiplication kernels on this laptop.
No performance prediction follows just from replacing exponent 3 by 2.25.

Fetched manuscript bytes: 43,060. SHA-256:
`c396f2580a711b8b9e51ecf1265cb0e691acd745943f81bfc14ec0df209e1028`.

## 138: the advertised branch has an explicit input guard

Read the actual [Subset Sum implementation](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Subset-Sum-in-Time-2-power-0-49n-October-4-2026/build/sections/implementation.tex),
plus introduction, numerical and filtering sections. Near the end of the
correctness/runtime proof, the program requires `b^100000 <= 2^n`, in
addition to a fixed sufficiently large cutoff. Here b is maximum input
integer bit length, n is the number of input integers. For b=32 this already
requires n>=500,000; for b=64, n>=600,000. An exponential-time algorithm at
these n values is outside a physical local experiment.

On a failed guard or below the cutoff, the supplied program uses classical
meet-in-the-middle. Its stated bound before absorption is
`K0 * 2^(0.489995*n) * (n+b+2)^K`; the positive exponent slack absorbs that
fixed polynomial only asymptotically. Removing the guard and reducing its
precision/caps would require a separate correctness/error analysis.

Therefore direct reproduction is unsuitable for a one-to-two-month practical
speedup commitment. This does not rule out useful independent subset-sum
engineering or a future simplification of the construction.

Fetched implementation bytes: 18,224. SHA-256:
`ef78713f1e782ccb8c0360aa2ff68e0145cef9105371423e2617215d0d6e3aea`.
