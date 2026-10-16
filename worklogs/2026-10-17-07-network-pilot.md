# Stage 07 — Degree-preserving network sampling pilot

Client date2026-10-17. This checkpoint records ongoing implementation before
the next release. User explicitly encouraged continued useful research.

## Choice and source

Selected family131, pinned commit1581d4cbdd69a0faf34b2089614fe2a814316a6a.
Two alternatives inspected by subagent:115contingency-table sampler has
large padding/runtimepowers, includingd^200;142factorization has enormous
polynomialexponents and a large standard-Berlekamp branch. See
docs/next-family-feasibility.md. Graph131 offers executable local updates
and a concrete network null-model application.

Preserved sources and hashes: research/graph131/sources.json.
Exactmethod/priorart/derivation: docs/graph-sampling-method.md.

## Important source fidelity

Paper switchstep: halfhold; uniform4vertexset; uniformoneof6ordered pairs
ofdistinctperfectmatchings; switchonlyifoldpairpresent/newpairabsent.
Otheredgesunrestricted. Offdiagvalidneighbor1/[12C(n,4)]. Everyattempt
counts, includingrejects. Source2n^8bound uses this particularclock.

Curveballbackend: uniformvertexpair, preservepair-edge/commonneighbors,
uniformlyreassignalloutside singletonneighbors accordingtoold rowcount,
includingthecurrentassignment. Noextra halfhold. Its P=averageE_a isPSD;
sourceH²>=H impliesgap>=1/C(n,2). This is a derived bound for a known
algorithm, not an attribution of the original Curveball method to us.

## Concrete application pitfall

For labeled degreevector(2,2,2,2,2,2), thereare70graphs:60six-cycles and
10pairsoftriangles. Switch-neighbor counts12versus18. Uniformstationary
two-triangleprobability1/7. Discardingholds/rejections andkeepingonlychanged
states produces jump-chainstationaryprobability1/5. Expectedtrianglecount
changes2/7to2/5. Exactenumerationauditwillreproduce this distinction.

NetworkXdouble_edge_swap counts successfulswaps and uses anotherproposal;
it is a degree-preserving rewiringAPI, not the identical paperkernel.
Our contribution is explicitproposalclock, exactsmall-statechecks and
reproduciblelabelednetworkoutput. Avoid calling an existingAPI defective.

## Implemented so far

- math_to_code/graphs.py stdlib: strictsimplegraphvalidation, deterministic
  Havel-Hakimi, two kernels, attempted-step clock, reproduciblesampling,
  integerconservative mixingbound. `sample` takes spacingsteps before every
  returnedgraph, includingfirst. Zero-sample requests do no work.
- CLI sample-graphs and graph-bound, example100graphs inresults/.
- 8core tests passed, including1000step degree/seed trajectories perbackend.
- Equal20,000attemptbenchmarks onregulargraphs n16,32,64,128. Source-switch
  changes become rare as sparse n grows; Curveballchange rates were92–99.8%.
  Compare actualmixing with finite-stateTV audit, not acceptancealone.
- scripts/benchmark_graphs.py and results/graph_benchmark.json.
- Full independent exactmatrixaudit and optionalreferencetests inprogress.

## Resource note

Two subagents returnedusage-limiterrors; the primarysession remainedusable.
Currentappusagequeryshowedordinaryusageallowed. No resetcreditwas consumed.
Researchsourceagent continued andcompletedpinnedsources/docs; it now handles
the independentgraphaudit. If workstops, readthischeckpoint andcheckactual
filesbefore restarting sourcecollection.

## Next completion steps

Finish graph_audit.json and reference tests; inspect failures, if any.
Make a compact mixing/biasfigure. Add how-to example and resultreport,
updatehandoff/state, runboundedCI andpublish completedv0.3.0.
