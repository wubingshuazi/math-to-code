# Third-party notices for the lazy-scs experiment

These notices accompany experimental patches, replay tools and public
benchmark inputs. The repository's [Apache-2.0 license](../../../LICENSE)
covers its new project materials; the upstream software and data retain
the licenses identified below. Full third-party license texts are kept
in [licenses/](licenses/).

**Only the new engineering in this project is labeled 100% GPT-generated.**
That statement does not attribute the original mathematical result,
original solver, established matching algorithms, dependencies or corpus
to this project's GPT contribution. The user supplied authorization,
computing resources and GitHub hosting. These files do not imply approval
or endorsement by OpenAI, the upstream maintainers, Andrew Gallant or Adobe.

## Mathematical source

OpenAI, *A Polynomial-Time 2-Approximation for Shortest Common Superstring*,
September 24, 2026, family 128 in the OpenAI mathematics release:
[pinned paper and sources](https://github.com/openai/math/tree/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/A-Polynomial-Time-2-Approximation-for-Shortest-Common-Superstring-September-24-2026).
The mathematics repository is pinned to
`1581d4cbdd69a0faf34b2089614fe2a814316a6a`; its
[original license](https://github.com/openai/math/blob/1581d4cbdd69a0faf34b2089614fe2a814316a6a/LICENSE)
is Apache-2.0. Mathematical authorship remains as recorded by that source.
The factor-two approximation result is not a new theorem of this project.

The trim patch is an implementation optimization using the established
Aho–Corasick multi-pattern string-matching algorithm of Alfred V. Aho and
Margaret J. Corasick. This project does not claim invention of that method
or of suffix automata.

## Original solver: lazy-scs

- Source: [nurric-ai/lazy-scs](https://github.com/nurric-ai/lazy-scs/tree/4ee86724b770c54bad400fe077b297288b087c4b).
- Pinned commit: `4ee86724b770c54bad400fe077b297288b087c4b`.
- Original notice: **Copyright (c) 2026 Krushna Dere**.
- License: MIT; [unaltered license copy](licenses/lazy-scs-MIT.txt).
- Original license SHA-256:
  `af59ef4a8b9f8bec95a3b7a4d06a935c6062225797d1ccd5c2237f905f3163c1`.

Patch context, the original approximation construction, suffix-automaton
implementation, command-line interface and independent lower-bound
checker originate in that software. Modified files identify the new
experimental engineering. Preserve the original MIT notice when sharing
substantial copies of the patched solver. The provenance index records
which original files and bytes were used.

## Matcher dependencies added by the trim patch

| Package | Source and version | Copyright notice | License used here |
| --- | --- | --- | --- |
| `aho-corasick` | [BurntSushi/aho-corasick](https://github.com/BurntSushi/aho-corasick), crate 1.1.5 | Copyright (c) 2015 Andrew Gallant | MIT, from the upstream `Unlicense OR MIT` choice; [full copy](licenses/aho-corasick-1.1.5-MIT.txt). |
| `memchr` | [BurntSushi/memchr](https://github.com/BurntSushi/memchr), crate 2.8.3 | Copyright (c) 2015 Andrew Gallant | MIT, from the upstream `Unlicense OR MIT` choice; [full copy](licenses/memchr-2.8.3-MIT.txt). |

Both MIT license copies match the corresponding downloaded crate's
`LICENSE-MIT` bytes, SHA-256:
`0f96a83840e146e43c0ec96a22ec1f392e0680e6c1226e6f3ba87e0740af850f`.
The final patch pins the versions and crate archive checksums in Cargo.lock:

```text
aho-corasick 1.1.5
c982642fa9e8606056828ee9a8505737230110bb1099153c79efe865c59d12ba
memchr 2.8.3
cf8baf1c55e62ffcace7a9f06f4bd9cd3f0c4beb022d3b367256b91b87513d98
```

The Rust package manifests and implementation credits remain with their
authors and contributors. The optional Python-binding feature inherited
from upstream is not enabled in this native CLI experiment; a distribution
that enables other features must also retain their dependency notices.

## Public benchmark dictionary: Adobe Glyph List

Adobe Glyph List 2.0, table date September 20, 2002:
[official repository](https://github.com/adobe-type-tools/agl-aglfn/tree/4036a9ca80a62f64f9de4f7321a9a045ad0ecfd6).

**Copyright 2002-2019 Adobe (http://www.adobe.com/).**

The source commit is `4036a9ca80a62f64f9de4f7321a9a045ad0ecfd6`.
The benchmark extracts glyph names from `glyphlist.txt`, omitting mapping
values and comments for solver input. Development/holdout splitting and
subsetting are new experiment preparation steps, not changes to the
meaning of the Adobe mappings. The original complete file and its
copyright/license header remain alongside downloaded benchmark inputs.

License: BSD-3-Clause. The source's separate `LICENSE.md` is copied without
editing to [adobe-agl-BSD-3-Clause.txt](licenses/adobe-agl-BSD-3-Clause.txt),
SHA-256 `58147d341e7a34aa2196862395a34d2fd95716c41d5ed26efb59ab0e12f92089`.
Original `glyphlist.txt` SHA-256:
`a3b2f61ced9f3644cc0d4ecde5c59df34ca286c689d9484a43a710a81c466789`.
Retain the Adobe copyright notice, conditions and disclaimer with derived
benchmark data. Adobe's name does not endorse this solver or its results.

## New contribution and distribution scope

New contributions comprise candidate patch code, injected-failure and
differential tests, instrumentation, reproducible input preparation,
independent output checks, benchmark drivers, research records and these
documents. No blanket GPT authorship or relicensing claim is made over
upstream code or data. Standalone license copies preserve their original
wording; this notice file records where they apply.
