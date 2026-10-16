# Stage 04 — Release confirmed and local authentication repaired

Status: complete. Client date: 2026-10-17, Asia/Shanghai.

Published, non-draft release confirmed through GitHub API:
https://github.com/wubingshuazi/math-to-code/releases/tag/v0.1.0

The release points to checkpoint commit
`3e8c4e7bc80e478a0cc2793abbe6a9374105908b`. Its runtime and audit code are
identical to the four-job CI-validated implementation commit `4572d1e...`.
Five assets were confirmed: wheel (12,448 bytes), quantum audit JSON,
thermal audit JSON, CSV scan, and SHA256SUMS. Local git status was clean.

## Local credential-helper failure and fix

Initial `gh repo create --push` succeeded, but a later plain `git push`
stalled in its inherited credential helper. The remote still had the first
commit. Stopped only the current tool's PowerShell/push/helper process tree,
then configured THIS REPOSITORY's credential helper to reuse the existing
authenticated GitHub CLI session:

```console
git config --local credential.helper ""
git config --local --add credential.helper "!gh auth git-credential"
git push
```

The push then completed in seconds. No tokens were printed or written into
project files. The release was created only after confirming that push.
The local `.git/config` retains this fix; it is not part of the public repo.
On a new machine, use its own authenticated GitHub configuration.

No user applications were closed. No always-running worker or future
automation was started. The proposed study in docs/NEXT_RESEARCH.md remains
unexecuted and should not be presented as completed research.
