---
date: 2026-08-24
branch: feature/installer-update-mechanism
status: ready-for-review
tags:
  - installer
  - stacked-pr
---

# Stack: Installer Update Mechanism

Base: `main`
Source branch: `feature/installer-update-mechanism`
Plan: `thoughts/shared/plans/2026-08-24-installer-update-mechanism-plan.md`
Spec: `thoughts/shared/specs/2026-08-24-installer-update-mechanism-spec.md`
Validation: `thoughts/shared/validations/2026-08-24-installer-update-mechanism.md`
Decision record: `thoughts/decisions/framework-distribution-and-updates.md`

Split by phase, because that is how the work was built and verified. Each layer
is a contiguous run of the original commits, so the stack is a replay of the
branch rather than a re-cut of it — no cherry-pick conflicts, and each layer's
red-then-green evidence sits in the same layer as the code it grades.

| # | Branch | Layer | Code files | Code lines | Total lines | Depends on |
|---|--------|-------|-----------|-----------|------------|------------|
| 1 | `feature/installer-update-1-install-record` | Install record + test harness | 4 | ~630 | ~1760 | `main` |
| 2 | `feature/installer-update-2-fetch-source` | Fetch from a git URL, with refs | 5 | ~335 | ~450 | layer 1 |
| 3 | `feature/installer-update-3-update-path` | `--update` that fetches and holds a pin | 5 | ~325 | ~570 | layer 2 |
| 4 | `feature/installer-update-4-protect-edits` | Per-file sync that keeps edits | 3 | ~320 | ~390 | layer 3 |
| 5 | `feature/installer-update-5-staleness-report` | `--check` staleness report | 3 | ~250 | ~375 | layer 4 |
| 6 | `feature/installer-update-6-link-command-docs` | Link mode, `/specs_update`, docs, 2.0.0 | 7 | ~520 | ~805 | layer 5 |

Layer 1's total is inflated by the decision record, spec, and plan (~1,000 lines
of prose). Its code is 630 lines across four files. Layer 6 carries the
data-loss fix found during validation plus all the documentation.

Every layer was verified green on its own in a detached worktree:
`validate.py`, `run_evals.py`, `standards/extractor.py --check`, and
`test_installer.py` all pass at each tip, with the installer test count growing
3 → 5 → 12 → 15 → 19 → 26 as each layer adds its groups.

## Review questions

### Layer 1: Install record + test harness

- The record's `files` map is the trust root for everything above it. Is a
  SHA-256 content hash the right identity for "the installer wrote this", or
  should it also record size or mtime to catch a hash collision that isn't one?
- `assert_record_readable` refuses a record whose `schema` is higher than the
  installer understands, and refuses one with no usable `schema` at all. Is
  hard-failing right, or should an unreadable record degrade to "treat as no
  record" so a corrupted file cannot brick every future run?
- The test fixtures copy the real repository into a temp git repo rather than
  building a stub. That keeps tests honest but couples them to repo layout.
  Is `SOURCE_SKIP` in `scripts/test_installer.py` the right exclusion list?

### Layer 2: Fetch from a git URL

- The cache key is the first 16 hex characters of a SHA-256 of the source URL.
  Two URLs for the same repo (SSH and HTTPS) therefore get separate mirrors.
  Wasteful but safe — is that the trade you want?
- `git archive | tar -x` is used instead of a checkout so two projects can pin
  different revisions without sharing a working tree. Does that lose anything
  you rely on — submodules, LFS, `.gitattributes` filters?
- A `--ref` naming a branch tracks it; a tag or a raw revision pins it. Is
  resolving "is this a branch" via `show-ref --verify refs/heads/<ref>` robust
  against a tag and a branch sharing a name?

### Layer 3: `--update` that fetches

- **Behavior change.** `--update` no longer copies from the directory beside
  the script; it fetches the recorded source. Someone iterating on the
  framework locally who ran `--update` to push working-tree changes into a test
  project now gets origin's committed state instead. Is `--from=<local path>`
  an acceptable answer for that workflow, or does it need its own flag?
- The pin is held by re-resolving the recorded `commit`, then restoring the
  recorded `ref` name for display. Read `resolve_source` in `setup.sh` — is
  that indirection clear enough to survive the next edit?
- A failed fetch exits before the first destination write, which is what makes
  "nothing changed" true. Is there any path that writes before `resolve_source`
  returns?

### Layer 4: Per-file sync that keeps edits

- The copy engine moved from `cp -r` to a Python per-file sync. Pruning,
  symlink replacement, and empty-directory removal all now live in
  `sync_tree`. Is the prune conservative enough after the layer-6 fix?
- A fingerprint records what the installer *wrote*, never what is on disk, so a
  kept file stays protected across repeated updates. The kept set is computed
  before any write and passed in rather than re-derived. Does anything else in
  the run re-derive it?
- Three defects were found here during implementation: macOS symlinked temp
  paths, a helper crash hidden by a process substitution, and the fingerprint
  baseline being overwritten. Are there other places where a helper's exit
  status is discarded?

### Layer 5: `--check` staleness report

- `--check` exits 1 when a newer revision exists, including on a deliberately
  pinned install. A pinned project therefore fails a CI gate on every run.
  Should a pin exit 0 and report, or is failing correct?
- Change-log lines are extracted with `git diff old..new -- CHANGELOG.md` and
  filtered to additions. A reworded line shows as an addition. Good enough?
- The report reads `track` from the record. If a tracked branch is deleted
  upstream, the check errors out. Should it fall back to the default branch?

### Layer 6: Link mode, `/specs_update`, docs, 2.0.0

- **This layer carries the data-loss fix found during validation.** An update
  used to delete a command the developer wrote into `.claude/commands/`, and
  `install_dir_plain` wiped whole directories before the per-file sync could
  protect them. Read `sync_tree`'s `known` parameter and the `foreign` action:
  is "the installer only touches what its record says it wrote" the right rule,
  and is it applied everywhere — including `sync_file_into`?
- Link mode now symlinks `conventions/` as a whole directory but the two
  standards files individually, because a target may keep its own files in
  `standards/`. Is that asymmetry going to confuse someone?
- The changelog calls this 2.0.0 on the strength of `--update` changing
  behavior. Do the evidence-field renames (`edge`→`outcome`, `result`→`output`)
  and the `slice`→`phase` vocabulary change belong in the same major, or should
  they have been called out separately?
- `/specs_update` is `model: quick`. It runs two commands and reads their
  output — is that tier right, given it has to explain a kept-file conflict to
  a user?

## Known follow-ups (not in this stack)

1. Cut tags: `v1.0.0` on `f6f7a63`, `v2.0.0` on `main` after merge. Until
   `v2.0.0` exists, the README's pinning example names an unresolvable tag.
2. A kept file that also changed upstream is not detected. The developer holds
   an old version of a moved file and only `/specs_update`'s prose mentions it.
3. A non-writable cache directory fails with a bare `set -e` exit, not a
   message.
