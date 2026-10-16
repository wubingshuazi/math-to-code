# Family 276: implementation and scope

Source: OpenAI, *Classical capacity and entropy inequalities for generalized
amplitude damping*, September 24, 2026, [pinned manuscript source](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Classical-capacity-and-entropy-inequalities-for-generalized-amplitude-damping-September-24-2026/build/paper.tex).

## Formula and conventions

The input qubit has diagonal populations `(1-p,p)`. Damping `gamma` and
stationary excited-state population `nu` lie in `[0,1]`. The output excited
population is `t=(1-gamma)*p+gamma*nu`. Off-diagonal entries are multiplied
by `sqrt(1-gamma)`. The two equiprobable pure signals differ by phase pi.

For a pure signal their output determinant is

```text
v = gamma*nu*(1-nu) + gamma*(1-gamma)*(p-nu)^2
e(p) = H2((1-sqrt(1-4*v))/2)
f(p) = H2(t)-e(p)
```

`H2` uses logarithm base 2, unlike the source's entropy-in-nats convention.
The numerical routine maximizes `f` on `[0,1]`. The source proves concavity
of the scalar objective; a golden-section search exploits that property.
It does not solve an arbitrary quantum-channel ensemble optimization.
The small eigenvalue is evaluated as `2*v/(1+sqrt(1-4*v))` to avoid
cancellation near pure outputs. Endpoint and unital cases have explicit
solutions. Thermal reflection reduces `nu>1/2` to `1-nu`.

At `gamma=0` the result is 1 bit/use. At `gamma=1` it is 0. At `nu=1/2`
the maximizing population is `p=1/2`. At full damping all populations are
equally good; the API chooses `p=1/2`.

## What is new here

The scalar one-use optimization is prior work, explicitly acknowledged by
the source. For example, Hou and Fang, *The Holevo capacity of a generalized
amplitude-damping channel*, Chinese Physics 16 (2007), 1843–1847,
[DOI](https://doi.org/10.1088/1009-1963/16/7/006).

The 2026 manuscript's broader claim concerns additivity for arbitrary
finite block lengths and arbitrary finite-dimensional partner channels.
This project adds a small dependency-free engineering implementation and
explicit numerical stress tests of that manuscript's entropy inequalities.
These are reproducibility artifacts, not a new proof or a claim of first
implementation.

## Independent numerical checks

The matrix audits construct the channel from Kraus operators, apply it to
states, and diagonalize the output. This computational path differs from
substituting a population into the scalar expression. They check trace,
positivity, the opposite-phase ensemble, random ensembles, and entangled
inputs. A second audit directly tests the rectangular thermal inequality
that supports the source's arbitrary-partner extension.

Seeds and samples are finite; a passing run rules out only detectable
violations among those samples. It cannot establish additivity at arbitrary
dimensions or validate the source's Lean formalization. No Lean proof is
compiled in this project. All optimizations and eigenspectra use ordinary
floating point; the reported search interval is not a certified enclosure.
Near reset channels the objective can be flat to machine precision, so the
reported maximizing population should not be read as a rigorous unique
optimizer. No speedup over QuTIpy or other libraries has been measured.
