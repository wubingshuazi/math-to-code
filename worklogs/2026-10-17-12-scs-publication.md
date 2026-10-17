# Stage 12 — native speed component published

2026-10-17, Asia/Shanghai. Publication complete after all required checks.
Release https://github.com/wubingshuazi/math-to-code/releases/tag/scs-aho-trim-v0.1.0
Code/tag commit3c3cb6b54cbd11c9dbfde5b8b820fe35f5c08314.
Python runtime remains0.3.0; this Rust component is a separate release.

## Validation

All8CIjobs passed for that exact commit:
-Native Windows/Linux:actions/runs/39038657473 (online pinned download,
hash-checked preparation,6Rusttests,lockedbuildboth,31tinycases).
-Existing runtime/research6jobs:actions/runs/39038657493.

Final reported benchmark remains stage11:19.33%/21.06%native batch-time
reduction on one Adobe dictionary's nested heldout sizes. No change to
frozen inputs,normal algorithm or measured EXEs after final timing.
Extracted release executables passed31independent tinycases again; the
same per-file hashes are verified after packaging-only license additions.

## Assets and provenance

Six uploaded assets, all GitHub server SHA-256 digests match local bytes:
WindowsZIP1872386bytes; reproductionZIP2700540bytes; finalpatch10570bytes;
finalreport2096262bytes; buildprovenance9663bytes; SHA256SUMS466bytes.
Full URLs/hashes/delivery-check details in results/scs_release_artifacts.json.
Final WinZIP SHA d7d9cc594b186ffe40c989e77ea206011d44694b3275d417e4a8a399b9ce677f.
ReproductionZIP SHA17546c0acd60be63682695a02b2b53e6b96f364d6755a51118d590db2b9abd7d.

ReproductionZIP contains143files including every final raw capture and
all three input manifests/sets/licenses,plus current scripts and exact
stage10driver fromad269fa. WindowsZIP includes original/candidateEXEs,
example,licenses,Rustdistributionnotices,projectLICENSE/NOTICE/CREDITS.
Independent agent verified ZIP CRC/inner SHA,rawcaptures/inputs/report and
binary consistency. Source rebuild still needs public pinned downloads
and Rust dependencies; existing binaries/inputs can be checked offline.

First local package attempt retained under .buildcheck/releases/...v0.1.0
failed due Python helper loop variable shadowing archive name. Corrected
helper emitted-002 and passed CRC/hash/smoke. Review then asked to add
Windows root LICENSE/NOTICE/CREDITS and fix relative license link; final
bundle-003 contains exactly that packaging-only adjustment. EXEs unchanged.
Those6final assets were uploaded to draft,checked,then publicly published.
Tagref independently confirmed points directly to tested code commit.

Delivery check: all6GitHub cryptographic server digests match final local
bytes/sizes. Direct download roundtrip verified3smallassets. Large CDN
downloads stalled locally; stopped our hung gh downloader after retaining
partialfiles. Alternative assetAPI also failed/stalled; stopped only
our own exact gh/Python processes. Large download transport was not fully
verified from this network; do not claim6successful download roundtrips.
This does not change upload hashes,local ZIP checks or measured binaries.

Git native push again reset connection. .buildcheck/api_push.py uploaded
the exact tree/commit through ghAPI; GitHub connector update_ref performed
lease-checked fast-forward fromad269fa to3c3cb6b. No force or reset.
Release publication used existing human authorization. No upstream message
or third-party PR was created; no unrelated programs were closed.

## Resume without repeating completed work

Read HANDOFF/PROJECT_STATE and docs/SCS_SPEED_RESULTS.md. Frozen data,
all failed attempts,oldv1,fallbackfinalsource and source index are retained.
Local helper .buildcheck/native_cargo.py and ASCII source/target paths
remain as documented in stage10. Release artifacts are local-003.

Next meaningful research is independent real dictionaries and mixed-input
batch streams,then memory and integration. The current evidence does not
establish gains for arbitrary data,single-call latency,fonts in production,
or native performance on Linux. Cross-platform CI is correctness evidence.
Do not restart source screening or repeat frozen benchmarks just to consume
compute. No automation/background research was created by this release.
