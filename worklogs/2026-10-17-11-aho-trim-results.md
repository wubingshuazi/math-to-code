# Stage 11 — first measured native speedup

2026-10-17, Asia/Shanghai. Continue from stage10; user said to continue
producing results and explicitly allows mature methods for actual speed.
New engineering100%GPT; user compute/hosting and all upstream credit retained.

## Final result and scope

Pinned nurric-ai/lazy-scs4ee86724b770c54bad400fe077b297288b087c4b.
Replace only Sam::trim plus Cargo dependency files; solve/count/approx/
verification bytes unchanged. Final sam SHA256
9ea0e06dd0c6d8062aed1c9ef252404c230f80d6ec2ad741b5e5b90d77907213.
Aho latest-start pass then a FRESH earliest-end pass gives identical cuts;
overlapping matches required. Builder failure falls back to original SAM.
Dependency aho-corasick=1.1.5,memchr2.8.3; MIT texts preserved.

Final authoritative report: results/scs_aho_trim_batch_heldout_final.json.
Same heldout Adobe glyph dictionary,512/2092nested names,9processes per
variant per size,40SAME-case solves per process. Balanced randomized AB/BA,
seed1282028. Both clean binaries omit all profiling. --verify enabled.
Native full process-wall medians:
-512:439449600ns baseline,354509900ns candidate,19.3286556638%reduction.
-2092:1545607700ns baseline,1220099600ns candidate,21.0602017575%reduction.
36processes/1440solves; every output byte/certificate identical,0failures.
This passes narrow repeated-case real-corpus gate, not independent datasets,
single-call latency, universal application speedup or measured memory gain.
Checked Python harness wall is a separate report metric; do not mix it in.

Development batch18.47%/21.55%. Clean v1 heldout20.16%/23.02% retained;
review then required builder-error fallback, froze v1 source, rebuilt final,
reran all heldout timing. No normal-strategy parameter tuning on holdout.
Single-process synthetic/dev screen remains roughly-1.4%..11.3%synthetic;
the published claim is the final batch table, not that older screen.

## Correctness/reproducibility

Final clean candidate Rust release tests6passed,0failed. Includes binary
exhaustion,1000seeded random tests,independent legacy/direct oracles,overlap,
crosscut abab->[ab,ba]->bab,Unicode/arbitrary bytes,duplicates/contained/
empty patterns,missing-patternpanic,and injected real Err-builder fallback.
The library permits binary inputs; CLI lossy UTF8 and empty JSON constraints
are handled explicitly by the separate CLI checker rather than hidden.

Independent read-only review checked112actual file hashes (bothEXEs,
scripts,inputmanifest,all36rawcaptures,batchfiles,patches,clean13filetrees),
37journal records,all1440instances,medians,plus6patch combinations in memory.
No discrepancy. No extra benchmark was run during review.

Patch/index variants preserve original,profile-original,event-sweep,
aho-trim-v1,profile-aho-trim-v1,finalaho-trim. Preparation restores exact
13pinned source files,checks/applypatches,and verifies finalsourcehashes.
Offline fresh replay .verification/scs-replay-aho-002 passed. First replay
failed because Git autocrlf modified Cargo.lock; retained that attempt,
fixed prepare to git -c core.autocrlf=false -c core.eol=lf apply.
Online fresh reconstruction is covered by the new cross-platform CI.

Important: native JSONL journal bytes are CRLF on this Windows machine.
Stage10 Git initially normalized that journal, so its report hash differed
after checkout. This commit restores the original retained bytes, marks
native reports/journals/patchindex/patches -text. No measurement changed.
Current stage10journal SHA d5e2660f19b5019d4f6beb946fa057fbecd704d8714736b56f514086cf7f5d33.
Finaljournal SHA3107f458ff76b76a5ae5e78bc67a293654ac79896f0d21628052d44f08c9da61.

## Local builds and persistent artifacts

Toolchain/helper/ASCII details remain stage10; actual clean EXEs:
C:/Users/lenovo/math-speed-build-targets/clean-base/release/scs-rs.exe
C:/Users/lenovo/math-speed-build-targets/clean-aho/release/scs-rs.exe
Final SHA859cfc4e801be1a14231195cbab7dfc834d4bf9edbdc77d61306e5408e0e04e4 baseline,
362b03db0df39fd1c69c62804b85f85efd0bfd5fc2c938b59518686ce6c6eb2f candidate.
PE imports are Windows system DLLs only; no extra Rust/MinGW DLL required.
Local GNU builds need actual ASCII Cargo target directory, not merely a
junction. Python runtime remains0.3.0; new component tagscs-aho-trim-v0.1.0.

Ignored input snapshots run-001,run-002,heldout-001 stay untouched. Allraw
stdout/stderr remain .verification/scs-native-output/batch-heldout-final.
Rawreports/journals are tracked; publication bundle preserves inputs,
manifests,rawcaptures,patches,licenses and exact executables. See build
provenance JSON for all hashes. No full downloaded implementation in Git.

## Publication checkpoint

Source/scripts/results prepared. Windows/Linux native CI and the six
existing runtime/research jobs must pass before publishing the component.
Final release asset hashes/tag/code commit will be recorded in stage12.
Human authorization already includes publishing to this user's GitHub;
do not ask again. Do not contact upstream/create third-party PRs.

After publication: new independent real corpora and mixed-input batches,
then peak memory and integration. Preserve negative event-sweep result and
all timeouts. Do not rerun frozen data without a concrete unresolved issue.
