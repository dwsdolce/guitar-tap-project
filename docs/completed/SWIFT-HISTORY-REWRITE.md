# Swift history rewritten before GuitarTap went public (2026-10-10)

Before `dwsdolce/GuitarTap` was made public its history was audited (owner, 2026-10-10). One thing could not be
published: `Tests/Beta Testers.xlsx` — six beta testers' names and email addresses — in four versions between March
(`a3ee452`) and August (`77af1b4`, when `Tests/` moved to the hub, where the file remains, private). An Apple
app-specific notarisation password was also in the history (`Distribution/build_mac`, March to `6bd346e` in August),
but it had already been public in guitar_tap's history since April and had been revoked, so it decided nothing.

**What was done** — option (a), keeping the history (owner):

- The history was rewritten with `git filter-repo --path "Tests/Beta Testers.xlsx" --invert-paths --prune-empty
  never`: only that file is removed. `--prune-empty never` keeps the two commits that touched nothing else, so the
  commit count — the build number — is unchanged (562).
- Verified against a full mirror of the original: the same commits, the same three tags (`1.0.1`, `1.0.2`,
  `Beta_release_1.0`), an identical current tree; the file and every tester's address in no commit; 92 commits from
  before the file kept their hashes; every rewritten commit differs from its original only by the file, and ten
  commit messages had their citations of other commits updated to the new hashes.
- The original repository was renamed `dwsdolce/GuitarTap-archive` (private) and the rewritten history pushed to a
  new `dwsdolce/GuitarTap` — not force-pushed over the old one, because GitHub keeps force-pushed-away commits
  reachable by hash. A mirror backup is at `/Users/dws/src/GuitarTap-backup-2026-10-10.git` on the owner's Mac.

**Reading an old Swift hash.** Swift hashes cited before 2026-10-10 — in these docs, the Issues, commit messages in the
other repositories — are the archive's. [`swift-commit-map.txt`](swift-commit-map.txt) gives each one's new hash
(old → new, full hashes). Files that store a Swift hash as data — the oracle's and every baseline's `oracleVersion`
(`068f814`) — keep the old one until their next mint.
