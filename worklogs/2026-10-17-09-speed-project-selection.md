# Stage 09 — Select an actual software speedup project

User steering: devote roughly one or two months of spare compute and model
allowance to making useful software faster, preferably by applying OpenAI
math manuscripts. This changes the next priority after the completed graph
release. No new recurring automation, goal budget, third-party PR or message
was requested or created. An optional scope preference is pending: whether
practical speedups may also use methods outside this manuscript collection.

## Decisions and evidence

Read AGENTS, HANDOFF, state, stage 08 and catalogue. Three independent
agents read actual constructions and mature software. Their reports are
docs/speed-{strings,graphs,other}-feasibility.md. Root separately inspected
107 matrix multiplication and 138 Subset Sum; see arithmetic feasibility.
The primary new recommendation and staged plan is
docs/LONG_TERM_SPEED_PROJECT.md.

120 and 121 cannot activate their advertised fast branches at physical
input sizes under the supplied construction. 107 supplies an asymptotic
existence argument, not a ready finite matrix-multiplication kernel. 138's
bit guard makes its new branch physically inaccessible for ordinary word
sizes. These are implementation-selection rejections, not disproofs.
325 is a possible narrow matrix-function experiment, but older scalar and
Faber results already supply relevant constant-two bounds. 104 is a
secondary exact formal-verification-game solver candidate.

## Primary bounded pilot: existing family-128 software

Upstream software: nurric-ai/lazy-scs at
`4ee86724b770c54bad400fe077b297288b087c4b`. Its count computation collects
successor step-function breakpoints, then repeats a binary-search query
for every successor at every breakpoint. An event sweep can preserve the
same output while updating only changes. This is a source-inferred hotspot;
its actual whole-program cost has not yet been measured.

Root implemented experiments/scs_event_sweep.py as a Python structural
model, including an independently scanned integer-length reference. Run:

```console
python experiments/scs_event_sweep.py
```

505 cases passed: seed 1282026, 500 random and 5 boundary cases. Every
breakpoint list and integer-length value agreed. Independent agent review
found no issue with lo/hi handling or zero-net-change events; a second seed
1282027 passed 1,005 cases. Synthetic model median ratios 1.03–17.58 appear
in results/scs_event_sweep_probe.json with raw repeats and script hash.
These timings do not establish a Rust or full-solver acceleration.

The 505-case report is the persisted primary experiment; the second seed
was a read-only reviewer check. Do not overwrite raw results on a new run;
pass a separate output path. A native implementation must still be compared
against real SAM-produced tables, full r/f/bumps/W and solver certificates.

Downloaded lazy_scs-1.0.0-cp39-abi3-win_amd64.whl and installed it only in
ignored .buildcheck/lazy-scs-env. Native API with verify=True returned
superstring abcde and lower_bound 5 for abc/bcd/cde. This establishes
Windows/Python functionality only; the wheel-to-source-commit mapping is
not verified. Build both future benchmark variants from the pinned source.

No C++/Rust toolchain was on PATH, no Visual Studio installation was found
by vswhere at its standard path, and no WSL distribution was listed.
Installing a dedicated build toolchain is a next implementation step, not
a reason to claim the project cannot proceed. Hardware verified via CIM:
i9-14900HX, 24 cores /32 threads, 31.7 GiB RAM, RTX4060 Laptop GPU.

## Stop/go and next concrete actions

1. Build same-commit native baseline and stage timers; profile representative
   input classes and record count-function distributions.
2. Patch the event sweep with exact state-by-state parity; leave independent
   verification separate. Profile before additional memory-layout work.
3. Only start the month-long development phase after a named real workload
   shows median end-to-end time reduced >=15% or peak memory reduced >=25%,
   with preserved quality and no material regression on other classes.
4. If counts occupy <15% of runtime, drop this hotspot or select another
   measured stage. Do not turn Python microbenchmark ratios into solver claims.

New experimental work stays separate from the dependency-free v0.3.0 runtime.
All three previous releases remain available. Publish the new feasibility
record in our own repository; no new solver release is ready yet.
