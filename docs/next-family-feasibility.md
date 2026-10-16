# Constructive-family feasibility pass

Source pin: OpenAI mathematics collection commit
`1581d4cbdd69a0faf34b2089614fe2a814316a6a`, reviewed 2026-10-17.

The third engineering pilot selects family 131, degree-preserving network
sampling. It has short executable updates, an existing practical use as a
network null model, and small state spaces that can be completely enumerated.
The useful software target is correct proposal timing plus exact finite-state
distribution checks, alongside a practical Curveball backend.

Two other candidates were inspected before this choice:

| Family | Actual construction detail | Engineering decision |
|---|---|---|
| [115: contingency tables](https://github.com/openai/math/tree/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Exact-Uniform-Sampling-of-Contingency-Tables-with-Arbitrary-Margins-September-24-2026) | Parameters include `d=10+(m+1)(n+1)`, padding powers `d^12,d^20`, outer-chain length `d^200(k+b)^2`, and a rare exact-correction tabulation with exponential work. Even a 2x2 input gives d=19. | A direct transcription is not a useful small-machine sampler. Existing table methods are better engineering baselines until this construction can be simplified. |
| [142: prime-field factorization](https://github.com/openai/math/tree/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Deterministic-Polynomial-Factorization-over-Prime-Fields-October-4-2026) | The supplied complexity includes a small-prime cutoff `p<=B^200000` and polynomial exponents up to 500000 or larger; the new branch needs substantial norm-equation/divisor machinery. | The easy branch would reproduce standard Berlekamp work. Defer the complete construction and use mature finite-field libraries when a practical task needs factorization. |

The graph pilot builds on established switching and Curveball methods. Its
specific contribution is an inspectable, theorem-aligned implementation,
reproducible network output, and a complete small-state demonstration of how
discarding rejected steps biases a null model. Details and primary prior-art
links are in [the graph method](graph-sampling-method.md).
