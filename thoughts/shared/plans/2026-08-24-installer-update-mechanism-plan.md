---
date: 2026-08-24
branch: main
status: draft
tags:
  - installer
  - distribution
  - versioning
---

# Installer Update Mechanism — Implementation Plan

**Grades against:** `thoughts/shared/specs/2026-08-24-installer-update-mechanism-spec.md`, 22 criteria (AC-1 … AC-23, including AC-17b; AC-10 and AC-11 retired under D-4). Every phase cites the criteria it satisfies.
**Decision record:** `thoughts/decisions/framework-distribution-and-updates.md` (ADR-001, Option D).
**Open questions:** none. The spec's three questions were closed as D-1, D-2, and D-3 on 2026-08-24.

---

## Overview

Teach the installer to record what it installed, fetch its own source, report when an install is behind, and stop destroying files the developer edited. Add a test harness that can exercise installer behavior, because the repository currently has no way to test shell behavior at all.

---

## Current State Analysis

Read in full during planning: `setup.sh` (483 lines), `scripts/validate.py`, `providers/claude/manifest.yaml`, `.github/workflows/validate.yml`, `specs.config.yaml`, `README.md`, `conventions/criterion-binding.md`, `conventions/program-design.md`.

### Key discoveries

- **The installer resolves its source from its own location.** `setup.sh:23` sets `SCRIPT_DIR` from `BASH_SOURCE`, and every later copy reads from it. Nothing in the file invokes `git`. Making the source configurable means introducing one indirection and changing every read site.
- **Copying is directory-at-a-time.** `install_dir_plain` (`setup.sh:218-234`) does `rm -rf "$dest"` then `cp -r`. Per-file decisions (AC-9, AC-10) cannot be layered on top of that; the copy engine has to become per-file.
- **Link mode reaches only two of six file sets.** `install_dir_plain` is called for `agents/` and `commands/` only (`setup.sh:329-330`). Conventions (`setup.sh:345-357`) and standards (`setup.sh:364-370`) use `cp` unconditionally in every mode.
- **The PR template is overwritten every run** (`setup.sh:425-428`), with no existence check. The project config is the opposite — written only when absent (`setup.sh:406`), which is why it survives updates.
- **A test pattern already exists and fits.** `scripts/validate.py:397-406` keeps a `CHECKS` registry keyed by group name, exposes `--list-checks`, and runs exactly one group under `--check <name>`. This repository's `specs.config.yaml` sets `test_group_command: "python3 {file} --check {name}"`, so any new script following that shape is bindable with no config change.
- **CI already exercises the installer.** `.github/workflows/validate.yml` has an `install-smoke-test` job that runs `setup.sh --yes` into `/tmp/test-project` for all three providers and asserts layout. It is inline shell, not named groups, so it cannot be bound to a criterion — but it proves installer testing works in CI without extra tooling.
- **Adding a command is cheap.** `scripts/run_evals.py:63` requires a case file only for the four names in `CORE_ROUTED`. A new command needs valid frontmatter (`validate.py:112-149`) and a description that does not collide above 0.72 cosine similarity with an existing one.
- **The README documents no ignore list.** AC-23 assumes a documented list of paths to keep out of git. No such list exists in `README.md` today, so this plan creates it rather than editing it.
- **The README's version claim is already stale.** `README.md:235` says "Current version: **1.0.0**" while `CHANGELOG.md` keeps every entry under `[Unreleased]` and the repository has no git tags. Noted, not fixed here — see Recommendations.

---

## Desired End State

From inside a consumer repository, a developer runs one command to learn whether the framework install is current and what changed, and one command to bring it up to date. The update fetches on its own, keeps files the developer edited, and never leaves a half-written install behind when the network fails. Each consumer repository holds its own version, and a pinned repository stays pinned while still being told that a newer revision exists.

Verified by: 24 named test groups in a new installer test script, one per acceptance criterion, each individually runnable.

---

## What We're NOT Doing

Carried from the spec's scope boundaries, unchanged:

1. No pip or npm package.
2. No first release tag and no change-log restructuring in this work.
3. No merging of the developer's edits with upstream — keep-and-report only, no conflict markers.
4. No change to consumer repositories committing versus ignoring framework files.
5. No uninstall and no rollback history.
6. No scheduled or automatic update checks.
7. No shared installs across a team.
8. No migration of the existing install in `agent-readiness-cli`.
9. No change to which file sets are installed or where they land, apart from link mode's coverage.
10. No signature checking or supply-chain verification of the fetched source.
11. No Windows support.

Added by this plan:

12. **No rewrite of the existing CI smoke-test job.** The new installer test script runs alongside it. Folding the smoke test into the script is a later cleanup.
13. **No fix for the README's stale version claim** — recorded under Recommendations instead, so this change stays inside the spec's scope.

---

## Criterion Bindings

Every group lives in `scripts/test_installer.py` and is run with `python3 scripts/test_installer.py --check <name>`, matching this repository's configured `test_group_command`. No group serves two criteria.

Stakes domains are filled from the keyword table in `conventions/criterion-binding.md` §3 by matching each criterion's own spec text. The match is mechanical, not a judgment: AC-21 lands on `auth` because its text contains "session" (in "agent session"), which is a listed `auth` keyword. That is the rule working as written, and it means AC-21 must not rest on degraded evidence.

| Criterion | Test group | Invocation | Stakes domain | Phase |
|---|---|---|---|---|
| `AC-1` | `scripts/test_installer.py::check_fresh_install_writes_record` | `python3 scripts/test_installer.py --check check_fresh_install_writes_record` | `none` | 1 |
| `AC-2` | `scripts/test_installer.py::check_record_hashes_match_disk` | `python3 scripts/test_installer.py --check check_record_hashes_match_disk` | `none` | 1 |
| `AC-3` | `scripts/test_installer.py::check_future_schema_refused` | `python3 scripts/test_installer.py --check check_future_schema_refused` | `none` | 1 |
| `AC-4` | `scripts/test_installer.py::check_install_from_url_without_clone` | `python3 scripts/test_installer.py --check check_install_from_url_without_clone` | `none` | 2 |
| `AC-16` | `scripts/test_installer.py::check_install_named_reference` | `python3 scripts/test_installer.py --check check_install_named_reference` | `none` | 2 |
| `AC-5` | `scripts/test_installer.py::check_update_fetches_new_revision` | `python3 scripts/test_installer.py --check check_update_fetches_new_revision` | `none` | 3 |
| `AC-6` | `scripts/test_installer.py::check_update_without_source_argument` | `python3 scripts/test_installer.py --check check_update_without_source_argument` | `none` | 3 |
| `AC-7` | `scripts/test_installer.py::check_repeat_update_is_stable` | `python3 scripts/test_installer.py --check check_repeat_update_is_stable` | `none` | 3 |
| `AC-8` | `scripts/test_installer.py::check_failed_fetch_leaves_install_intact` | `python3 scripts/test_installer.py --check check_failed_fetch_leaves_install_intact` | `none` | 3 |
| `AC-12` | `scripts/test_installer.py::check_update_without_record_warns` | `python3 scripts/test_installer.py --check check_update_without_record_warns` | `none` | 3 |
| `AC-17` | `scripts/test_installer.py::check_update_keeps_pin` | `python3 scripts/test_installer.py --check check_update_keeps_pin` | `none` | 3 |
| `AC-18` | `scripts/test_installer.py::check_update_moves_pin` | `python3 scripts/test_installer.py --check check_update_moves_pin` | `none` | 3 |
| `AC-9` | `scripts/test_installer.py::check_update_keeps_edited_file` | `python3 scripts/test_installer.py --check check_update_keeps_edited_file` | `none` | 4 |
| `AC-13` | `scripts/test_installer.py::check_staleness_reports_distance` | `python3 scripts/test_installer.py --check check_staleness_reports_distance` | `none` | 5 |
| `AC-14` | `scripts/test_installer.py::check_staleness_lists_changelog_entries` | `python3 scripts/test_installer.py --check check_staleness_lists_changelog_entries` | `none` | 5 |
| `AC-15` | `scripts/test_installer.py::check_staleness_exit_status` | `python3 scripts/test_installer.py --check check_staleness_exit_status` | `none` | 5 |
| `AC-17b` | `scripts/test_installer.py::check_staleness_reports_on_pinned_install` | `python3 scripts/test_installer.py --check check_staleness_reports_on_pinned_install` | `none` | 5 |
| `AC-19` | `scripts/test_installer.py::check_link_mode_covers_conventions_and_standards` | `python3 scripts/test_installer.py --check check_link_mode_covers_conventions_and_standards` | `none` | 6 |
| `AC-20` | `scripts/test_installer.py::check_link_mode_refused_for_transform_provider` | `python3 scripts/test_installer.py --check check_link_mode_refused_for_transform_provider` | `none` | 6 |
| `AC-21` | `scripts/test_installer.py::check_update_command_exists_and_parses` | `python3 scripts/test_installer.py --check check_update_command_exists_and_parses` | `auth` | 6 |
| `AC-22` | `scripts/test_installer.py::check_readme_documents_updating` | `python3 scripts/test_installer.py --check check_readme_documents_updating` | `none` | 6 |
| `AC-23` | `scripts/test_installer.py::check_documented_ignore_list_includes_record` | `python3 scripts/test_installer.py --check check_documented_ignore_list_includes_record` | `none` | 6 |

**Evidence file**: `thoughts/shared/evidence/2026-08-24-installer-update-mechanism.md`

**Manual-only criteria**: none. The spec carries no `manual-only` criterion, so no approval record applies.

**Regression tests, bound to no criterion.** Two groups in the same script guard behavior that predates this work: `check_update_replaces_untouched_file` and `check_update_preserves_project_config`. Both passed before any code was written, so neither can carry failing-first evidence. They were retired as acceptance criteria under D-4 and kept as tests. They run on every CI build; nothing binds to them, and nothing in this plan is checked off on their result.

---

## Implementation Approach

Three decisions shape everything below.

**The record and the copy engine move to Python; the flow stays in Bash.** The installer already requires `python3` and PyYAML for provider manifests (`setup.sh:82-107`), so no new runtime is introduced. Hashing, JSON, and per-file copy decisions are painful and non-portable in shell — `sha256sum` versus `shasum -a 256` alone would need a platform branch. Bash keeps argument parsing, manifest reads, provider branching, and output. A new `scripts/installer_support.py` owns the record and the file sync.

**Fetching uses a mirror clone plus an archive export, never a checkout.** Two consumer repositories can pin different revisions of the same source. A shared cache that checks refs in and out would fight itself. Instead the cache holds `git clone --mirror`, and each install exports one revision with `git archive <commit> | tar -x` into a temporary directory. Concurrent installs at different revisions cannot collide, and the export is a clean tree with no `.git` to copy by accident.

**Tests use local `file://` git remotes, so no test touches the network.** Each group builds a small source repository in a temporary directory, commits it, optionally advances it, and installs from `file://` that path. Cache and target directories are also temporary. Nothing outside the temporary directory is read or written.

---

## Program Design

### Call-Stack Changes

```
setup.sh main
    → parse args
+   → cmd_check "$TARGET_PATH"                 # new: staleness path, returns before installing
+       → installer_support.py read-record
+       → fetch_source (cache only, no export)
+       → git rev-list --count <installed>..<head>
+       → installer_support.py changelog-between
+   → resolve_source                           # new: decides where source files are read from
+       → installer_support.py read-record      # update mode with no --from: source comes from the record
+       → fetch_source "$SOURCE_URL" "$REF"    # new
+           → git clone --mirror | git fetch --prune
+           → git rev-parse "<ref>^{commit}"
+           → git archive <commit> | tar -x -C "$TMP_SRC"
    → manifest_get (unchanged)
+   → installer_support.py protected-paths      # new: which files the developer edited
-   → install_dir_plain  [rm -rf + cp -r]      # removed: cannot make per-file decisions
+   → sync_tree                                # new: per-file copy honoring protection
+       → installer_support.py sync
+           → hash each source and destination file
+           → skip protected, write the rest
+           → emit one record line per file
    → install conventions
-       → cp -r (every mode)                   # removed
+       → sync_tree (copy mode)                # new
+       → ln -s   (link mode)                  # new: link mode now reaches conventions
    → install standards
-       → cp two files (every mode)            # removed
+       → sync_tree (copy mode)                # new
+       → ln -s per file (link mode)           # new: link mode now reaches standards
    → write specs.config.yaml when absent (unchanged)
-   → cp templates/pr_description.md           # removed: unconditional overwrite
+   → sync_tree for the PR template            # new: protected like every other file
+   → installer_support.py write-record        # new
    → print summary
+       → list files kept because the developer edited them
```

### File-Tree Changes

```
project-specs/
~ setup.sh                                    # modified: source indirection, fetch, --check, per-file sync, record write, link coverage
  scripts/
+   installer_support.py                      # new: record read/write, hashing, protection, file sync, changelog diff
+   test_installer.py                         # new: 24 named test groups, --check/--list-checks registry
  commands/core/
+   specs_update.md                           # new: /specs_update — check for and apply framework updates
~ README.md                                   # modified: "Updating an install" section, recommended ignore list
~ .github/workflows/validate.yml              # modified: new installer-behavior job
  thoughts/shared/evidence/
+   2026-08-24-installer-update-mechanism.md  # new: red/green records for all 24 criteria
```

Installed into a consumer repository (not files of this repository):

```
<target>/
+ .project-specs.json                         # new: the install record; ignored, per D-1
```

### Key Types and Signatures

```python
# scripts/installer_support.py
SCHEMA = 1                      # bump only on a breaking record change

@dataclass
class SyncResult:
    rel: str                    # path relative to the target root
    action: str                 # "written" | "kept" | "unchanged" | "linked"
    digest: str                 # "sha256:<hex>", or "" for a symlink

def file_hash(path: Path) -> str
def read_record(target: Path) -> dict | None            # None when absent
def write_record(target: Path, *, source: str, ref: str, track: str,
                 commit: str, provider: str, mode: str, pinned: bool,
                 files: dict[str, str]) -> None
def assert_schema_supported(record: dict) -> None       # raises on schema > SCHEMA
def protected_paths(target: Path, record: dict | None) -> set[str]
def sync_tree(src: Path, dest: Path, target_root: Path,
              protected: set[str]) -> list[SyncResult]
def changelog_between(mirror: Path, old: str, new: str, path: str) -> str
```

```bash
# setup.sh — new functions
resolve_source            # sets SRC_DIR, SOURCE_URL, REF, TRACK, COMMIT, PINNED
fetch_source url ref      # echoes "<export_dir> <commit> <resolved_ref> <pinned>"
cmd_check target          # prints the staleness report; exit 1 when behind, 0 when current
sync_tree src dest label  # per-file install honoring PROTECTED; appends to RECORD_FILES
write_record target       # calls installer_support.py write-record
```

Record shape written into a consumer repository:

```json
{
  "schema": 1,
  "source": "git@github.com:dj-haile/project-specs.git",
  "ref": "main",
  "track": "main",
  "commit": "20a0e94…",
  "pinned": false,
  "provider": "claude",
  "mode": "copy",
  "installed_at": "2026-08-24T09:12:00Z",
  "files": {
    ".claude/conventions/naming-conventions.md": "sha256:9f2c…",
    "standards/statements.json": "sha256:41ab…",
    "pr_description.md": "sha256:7d10…"
  }
}
```

`ref` is what the developer asked for. `commit` is what it resolved to. `track` is the branch staleness is measured against — the ref itself when it names a branch, otherwise the source repository's default branch, which is what lets a pinned install still be told a newer revision exists (AC-17b). `pinned` is true when `ref` names a tag or a raw revision rather than a branch.

---

## Phase 1: Install record — tracer bullet through Bash, Python, and the test harness

Satisfies **AC-1, AC-2, AC-3**.

### Overview

The thinnest path that touches every layer this work will use: the installer calls new Python, the Python writes a record, and a new test script installs into a temporary directory and checks the result. No fetching and no protection yet.

### Changes Required

**1. `scripts/installer_support.py`** (new)
Implement `SCHEMA`, `file_hash`, `read_record`, `write_record`, and `assert_schema_supported`. Expose a small subcommand interface (`write-record`, `read-record`) so Bash can call it. Records are written with sorted keys and a trailing newline so a diff of two records is readable.

**2. `setup.sh`** (modified)
Collect every written file into a `RECORD_FILES` array as the existing copy steps run, then call `write_record` before the summary. In this phase the copy engine is unchanged — only the bookkeeping is added. `commit` is filled from `git -C "$SRC_DIR" rev-parse HEAD` when the source directory is a git working copy, and left empty otherwise. `assert_schema_supported` runs at the start of any run that finds an existing record.

**3. `scripts/test_installer.py`** (new)
The `CHECKS` registry, `--check`, and `--list-checks`, modeled on `scripts/validate.py:397-449`. A fixture builder that copies the minimum source tree into a temporary directory and commits it. The three groups for AC-1, AC-2, AC-3.

**4. `.github/workflows/validate.yml`** (modified)
New `installer-behavior` job running `python3 scripts/test_installer.py`.

### Success Criteria

**Automated:**
- [x] `python3 scripts/test_installer.py --check check_fresh_install_writes_record` passes (AC-1)
- [x] `python3 scripts/test_installer.py --check check_record_hashes_match_disk` passes (AC-2)
- [x] `python3 scripts/test_installer.py --check check_future_schema_refused` passes (AC-3)
- [x] Each of the three groups was recorded failing before the change and passing after it, per the pairing gate
- [x] `python3 scripts/validate.py` passes
- [x] The existing `install-smoke-test` job still passes for all three providers

**Manual:**
- [ ] Install into a scratch directory by hand and read the record — the field names and the timestamp are legible to a person

**Implementation note:** pause after this phase for confirmation before continuing. It fixes the record shape, and every later phase depends on it.

---

## Phase 2: Fetch and install from a source URL

Satisfies **AC-4, AC-16**.

### Overview

Add the cache, the fetch, and the revision export, so an install works with no local clone and can name a reference.

### Changes Required

**1. `setup.sh`** (modified)
Add `--from=<git-url>` and `--ref=<name>`. Add `fetch_source`: mirror-clone into `${SPECS_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/project-specs}/<hash of url>`, fetch, resolve `<ref>^{commit}`, export with `git archive | tar -x` into a temporary directory, and remove that directory on exit. Add `resolve_source`, which sets `SRC_DIR` to the export when a source URL is given and to `SCRIPT_DIR` otherwise. Set `track` and `pinned` from whether the resolved ref is a branch.

**2. `scripts/test_installer.py`** (modified)
Fixture helper that builds a `file://` source repository with two branches and a tag. Groups for AC-4 and AC-16.

**Deviation (in scope, `setup.sh` was already listed).** Pointing every read at the resolved source made the closing summary print paths into the temporary export, which is deleted when the installer exits. The summary now names the source repository and the installed convention path instead.

### Success Criteria

**Automated:**
- [x] `--check check_install_from_url_without_clone` passes (AC-4)
- [x] `--check check_install_named_reference` passes (AC-16)
- [x] Both groups have red-then-green evidence
- [x] No test reads or writes outside its temporary directory — asserted by pointing the cache at a temporary path in every group
- [x] Phase 1's three groups still pass

**Manual:**
- [x] Install into a scratch directory from the real GitHub URL and confirm the cache lands where expected

---

## Phase 3: Update that fetches, and holds a pin

Satisfies **AC-5, AC-6, AC-7, AC-8, AC-12, AC-17, AC-18**.

### Overview

Make `--update` read the record, fetch, re-install, and rewrite the record. Per D-2 the fetch is the default, so the failure path carries real weight: a source that cannot be reached must leave the install exactly as it was.

### Changes Required

**1. `setup.sh`** (modified)
`--update` with no `--from` reads `source`, `ref`, and `track` from the record. When the record is absent, the update proceeds against `SCRIPT_DIR`, writes a record, and prints that edited-file protection was unavailable for the run (AC-12). `fetch_source` failures exit non-zero before any destination file is touched (AC-8) — the export completes before the first write, so a failed fetch cannot leave a partial install. A record with `pinned: true` and no explicit `--ref` re-resolves the pinned revision and reports the pin (AC-17); an explicit `--ref` replaces it (AC-18).

**Deviation (in scope).** The AC-5 group first passed on contact because it supplied `--from`, which the fetch work already covered. A group that never fails is not evidence about the change, so it was rewritten to run the update with no source argument — the path this phase adds. No criterion text changed.

**2. `scripts/test_installer.py`** (modified)
Seven groups. The AC-8 group points the record at an unreachable path and asserts every installed file and the record are byte-identical afterwards. The AC-7 group runs the update twice and asserts the only difference in the record is `installed_at`.

### Success Criteria

**Automated:**
- [x] All seven groups for AC-5, AC-6, AC-7, AC-8, AC-12, AC-17, AC-18 pass, each with red-then-green evidence
- [x] Phases 1 and 2 still pass
- [x] `python3 scripts/validate.py` passes

**Manual:**
- [x] Run an update in a scratch install with the network disabled and confirm the failure message names the source and changes nothing

---

## Phase 4: Keep the files the developer edited

Satisfies **AC-9**. Also lands two regression tests bound to no criterion (see D-4).

### Overview

Replace the directory-at-a-time copy with a per-file sync that compares each destination file against the hash in the record. This is where the PR template stops being clobbered.

### Changes Required

**1. `scripts/installer_support.py`** (modified)
Implement `protected_paths` and `sync_tree`. A file is protected when the record holds a hash for it and the file on disk hashes differently. With no record, nothing is protected and the caller reports that (already handled in phase 3).

**Deviation (in scope).** Three defects surfaced during this phase and were fixed here: resolved and unresolved forms of a macOS temp path made every relative-path calculation fail; that failure was silent because the helper ran inside a process substitution, so the installer reported success having copied nothing; and a kept file had its edited content recorded as the new baseline, which would have let the following update overwrite it. The kept set is now computed before any write and passed to the record writer rather than re-derived after.

**2. `setup.sh`** (modified)
Replace `install_dir_plain`'s copy branch with `sync_tree`. Route conventions, standards, and the PR description template through it as well, removing the unconditional `cp` at `setup.sh:425-428`. Print a "kept your local changes" list in the summary. The project configuration file keeps its existing write-only-when-absent behavior — this phase adds a regression test for it, not new behavior.

**3. `scripts/test_installer.py`** (modified)
Three groups: one for AC-9, plus two regression tests that guard behavior predating this work.

### Success Criteria

**Automated:**
- [x] The AC-9 group passes with red-then-green evidence
- [x] Both regression groups pass; neither is treated as evidence for any criterion
- [x] Phases 1 through 3 still pass
- [x] The existing `install-smoke-test` job still passes for all three providers — the copy engine changed underneath it

**Manual:**
- [x] Edit an installed convention by hand, run an update, and confirm the edit survives and the summary names the file

---

## Phase 5: Staleness report

Satisfies **AC-13, AC-14, AC-15, AC-17b**.

### Overview

Add `--check`, which fetches into the cache, compares the installed revision against the tracked branch, and reports distance, change-log entries, and an exit status CI could gate on.

### Changes Required

**1. `scripts/installer_support.py`** (modified)
`changelog_between` returns the lines the change log gained between two revisions, read out of the mirror with `git diff <old>..<new> -- <path>` and filtered to additions.

**2. `setup.sh`** (modified)
`cmd_check` runs before any install work and returns without writing anything. Output states current or behind, the revision count (AC-13), the change-log additions (AC-14), and — on a pinned install — that the install is pinned plus the newer revision available on the tracked branch (AC-17b). Exit 1 when behind, 0 when current (AC-15).

**3. `scripts/test_installer.py`** (modified)
Four groups. The AC-14 fixture must add a change-log entry in the advancing commit so there is something to report.

### Success Criteria

**Automated:**
- [x] Groups for AC-13, AC-14, AC-15, AC-17b pass with red-then-green evidence
- [x] The AC-17b group asserts no installed file changed during the check
- [x] Phases 1 through 4 still pass

**Manual:**
- [x] Run the check against the real install in `agent-readiness-cli` and confirm the report reads clearly

---

## Phase 6: Link mode coverage, the command, and the documentation

Satisfies **AC-19, AC-20, AC-21, AC-22, AC-23**.

### Overview

Close the remaining gaps: link mode reaches the conventions and the standards registry, a command makes the check and the update reachable from an agent session, and the documentation explains both.

Merged from what would naturally be two phases, to respect the enforced standard that a stack stays at five or six layers. Both halves are small.

### Changes Required

**1. `setup.sh`** (modified)
In link mode for a provider whose transform is `copy`, symlink `conventions/` as a directory and the two standards files individually, matching how they are copied today. Record them with `action: "linked"` and no hash, so protection does not apply to a symlink. The existing refusal for transform providers (`setup.sh:186-189`) is unchanged; AC-20 adds its test.

**2. `commands/core/specs_update.md`** (new)
Frontmatter with `name: specs_update`, a description distinct enough to clear the 0.72 collision threshold in `scripts/run_evals.py:60`, and `model: quick` — the work is running two commands and reading their output. Not a gate command, so the four behavioral sections `validate.py` requires of `CORE_ROUTED` commands do not apply.

**3. `README.md`** (modified)
A new "Updating an install" subsection under Quick Start naming the check, the update, and how to pin. A recommended ignore list for consumer repositories that includes the record path — this list does not exist yet and is created here (AC-23).

**4. `scripts/test_installer.py`** (modified)
Five groups. AC-21 asserts a command file exists whose description states an update purpose and whose frontmatter passes the same field rules `validate.py` applies. AC-22 and AC-23 assert on the documentation's content.

### Success Criteria

**Automated:**
- [ ] Groups for AC-19, AC-20, AC-21, AC-22, AC-23 pass with red-then-green evidence
- [ ] `python3 scripts/validate.py` passes, including the link check on the new command file
- [ ] `python3 scripts/run_evals.py` passes — the new description collides with nothing
- [ ] All 24 groups pass in one run: `python3 scripts/test_installer.py`
- [ ] `python3 standards/extractor.py --check` passes

**Manual:**
- [ ] Invoke the new command in a scratch install and confirm it reports and updates as documented

---

## Testing Strategy

**Named groups.** 24 groups in `scripts/test_installer.py`, one per criterion, each runnable alone. The registry pattern is copied from `scripts/validate.py` so the invocation matches this repository's configured `test_group_command` with no config change.

**Fixtures.** Each group builds its own source repository, target directory, and cache under one temporary root, and removes it afterwards. Source repositories are created with `git init`, a commit, and where needed a second commit, a branch, or a tag. Every install points at `file://<tmp>`, so no group needs the network.

**What is deliberately not covered.** Real-network behavior against GitHub, and the three-provider layout assertions that the existing `install-smoke-test` job already covers. Duplicating those here would add runtime without adding signal.

**Manual testing steps.**
1. Install into a scratch directory from the real GitHub URL; read the record.
2. Edit an installed convention; run the update; confirm the edit survives and is named in the summary.
3. Run the check against `agent-readiness-cli`; confirm the report is legible.
4. Disable the network; run an update; confirm nothing changed and the error names the source.

---

## Migration Notes

Installs made before this change carry no record. AC-12 covers them: the first update completes, writes a record, and states that edited-file protection could not be applied for that run. From the second update onward, protection works normally. No manual migration step exists, and none is needed.

The one live install, in `agent-readiness-cli`, currently matches this repository byte for byte, so its first update has nothing to protect. Performing that update is out of scope here (scope boundary 8).

---

## Performance Considerations

The mirror clone is fetched once per source URL and reused. A fetch on an unchanged source is a few hundred milliseconds. Hashing the installed file set is roughly 60 small text files per run, which is not measurable next to the fetch.

---

## Standards Notes

Checked against the registry, filtered to `sdlc_stage: planning` and `all`. No finding blocks this plan.

- **Program design** (`MUST`, approved, planning stage): satisfied — all three parts are present above.
- **Command naming and frontmatter** (`MUST`, enforced): the new command uses a snake_case filename, a frontmatter `name` matching the file stem, and a semantic model tier rather than a literal model name.
- **PR stacking** (`MUST` above 1,000 lines, `SHOULD` above 500 or across layers, enforced, review stage): this plan is written as six stacked layers for exactly this reason. Each phase leaves the repository green on its own, and each depends only on the phases below it.
- **Research before planning** (`SHOULD`): satisfied — every file this plan modifies was read in full during planning.

## Recommendations (outside this plan's scope)

- `README.md:235` claims version 1.0.0 while the change log holds everything under `[Unreleased]` and no git tags exist. Reconcile these when cutting the first tag, which is ADR-001 action item 1.
- The existing inline `install-smoke-test` job in CI could later become named groups in `scripts/test_installer.py`, making its layout assertions bindable to criteria.

---

## References

- Spec: `thoughts/shared/specs/2026-08-24-installer-update-mechanism-spec.md`
- Decision record: `thoughts/decisions/framework-distribution-and-updates.md`
- Pairing gate rules: `conventions/criterion-binding.md` §1–§4
- Program design format: `conventions/program-design.md`
- Test registry pattern to copy: `scripts/validate.py:397-449`
- Existing installer CI coverage: `.github/workflows/validate.yml`, job `install-smoke-test`
