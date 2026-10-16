# First reproducibility checkpoint — 2026-10-17

All quantities below are finite numerical measurements. The tests do not
prove the source mathematics or certify floating-point error bounds.

| Artifact | Tested scope | Observed result |
|---|---|---|
| Unit tests | 15 tests: endpoints, unital case, relabeling, invalid input, independent Kraus path, grid optimization | All passed |
| Quantum audit | 36 parameter pairs; 432 two-/three-qubit entropy samples; 72 random block ensembles; 72 product phase-pair ensembles | Passed at disclosed absolute tolerance 2e-10 bits |
| Scalar vs matrix path | Phase-pair Holevo information computed via scalar formula vs independent Kraus matrices/eigenspectra | Maximum difference about 1.55e-15 bits |
| Rectangular thermal audit | 10,000 seeded plus 240 explicit boundary/saturation cases; six matrix shapes | No violation exceeding tolerance 2e-10 nats |
| Thermal residual | Minimum `S(T)-RHS`; equality examples included | -8.77e-15 nats, compatible with roundoff at the chosen tolerance |
| Thermal equality cases | Maximum absolute residual when X=Y | About 1.10e-14 nats |
| Parameter scan | 41 by 41 pairs of gamma and nu | 1,681 CSV rows, finite values in [0,1] bits |
| Optimizer benchmark | 4,281 cases per run, three runs; 300 separate 2,049-point grid checks | Median .343 seconds on this machine; max grid excess 2.59e-15 bits |
| Catalogue parser | Source metadata, unique paths, counts, subject mapping | 7 checks passed; 719 manuscripts, 372 families |

The benchmark is a local wall-time measurement, not a speedup comparison.
Residuals inside tolerance are not asserted to be exact nonnegative values.
The worst sampled thermal input is retained in the JSON, allowing reanalysis.

Machine-readable details and seeds:

- [Quantum audit](../results/quantum_audit.json)
- [Thermal audit](../results/thermal_audit.json)
- [Benchmark](../results/benchmark.json)
- [CSV parameter scan](../results/gad_grid.csv)

The initial audit environment was Windows, Python 3.14.3, NumPy 2.5.4.
Source commit: `1581d4cbdd69a0faf34b2089614fe2a814316a6a`.
