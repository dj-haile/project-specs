---
date: 2026-08-24
branch: feature/installer-update-mechanism
status: complete
validated_at_code_state: "git:1db2bd86cd58f0c4899e2486923cd2cbf0ff26ff"
tags:
  - installer
  - validation
---

## Validation Report: Installer Update Mechanism

Plan: `thoughts/shared/plans/2026-08-24-installer-update-mechanism-plan.md`
Spec: `thoughts/shared/specs/2026-08-24-installer-update-mechanism-spec.md`
Evidence: `thoughts/shared/evidence/2026-08-24-installer-update-mechanism.md`

### Plan Review Findings (adversarial review of the plan itself)

Performed inline per the subagent-fallback contract.

- **[blocking — found and fixed during this validation] The plan authorized a per-file copy engine but never said what happens to files the installer did not write.** `sync_tree` as built pruned anything present in the target and absent from the source, so a command the developer wrote into `.claude/commands/` was silently deleted by an update. Reproduced against a real install before fixing. Two further layers surfaced underneath it: `install_dir_plain` still ran `rm -rf "$dest"` before syncing (`setup.sh`, inherited from the `cp -r` it replaced), which wiped `agents/` and `commands/` before protection could apply — so an edit to an installed *command* was also lost, a case no test covered; and the record was built by walking the installed directories, so after one update it claimed the developer's own file and the next update pruned it on that authority. All three fixed; the installer now only ever overwrites or deletes paths its own record says it wrote. Regression guard `check_update_keeps_files_the_installer_never_wrote` added and verified to fail with the fix reverted.
- **[concern] The spec's scope boundary 3 says the installer will not merge a developer's edits with upstream changes, and the plan inherits that.** That is the right call for this work, but it leaves a real hole a user will hit: when a kept file *also* changed upstream, the developer now silently holds an old version of a file that moved. `/specs_update` is told to say so, but nothing in the installer detects it. Worth a future criterion.
- **[concern] Three of the spec's assumptions were never confirmed and are still unconfirmed.** ASM-12 (git and network present) and ASM-13 (a writable cache directory) are now partly covered by code — a failed fetch exits cleanly — but a non-writable cache path is not handled gracefully; `mkdir -p` fails under `set -e` and the run dies without a useful message. No test covers it.
- **[note] The plan's phase-4 success criteria listed AC-10 and AC-11 as needing red-then-green evidence.** Neither could produce it. Caught during implementation, not planning: a plan cannot tell, from the criterion text alone, whether behavior already exists. Resolved as D-4.

### Implementation Status

✓ Phase 1: Install record — fully implemented
✓ Phase 2: Fetch and install from a source URL — fully implemented
✓ Phase 3: Update that fetches, and holds a pin — fully implemented
✓ Phase 4: Keep the files the developer edited — fully implemented, plus three defects found and fixed
✓ Phase 5: Staleness report — fully implemented
✓ Phase 6: Link mode coverage, the command, and the documentation — fully implemented

### Automated Verification Results

✓ `python3 scripts/test_installer.py` — 26 groups
✓ `python3 scripts/validate.py` — 29 agent/command files, configs, manifests, skills, links
✓ `python3 scripts/run_evals.py` — 53 routing assertions, no description collisions
✓ `python3 standards/extractor.py --check` — registry current, 42 statements
✓ `python3 scripts/build_skills.py` — no drift in `skills/.curated`
✓ Installer smoke test — all three providers × copy and link

_A green pipeline is not a verdict — the accounting below decides the overall result._

### Acceptance Criteria Accounting

| Criterion | Mode | Bound group | Red | Green | Strength | Verdict |
|---|---|---|---|---|---|---|
| `AC-1` | automated | `scripts/test_installer.py::check_fresh_install_writes_record` | ✓ | ✓ | single-group | pass |
| `AC-2` | automated | `scripts/test_installer.py::check_record_hashes_match_disk` | ✓ | ✓ | single-group | pass |
| `AC-3` | automated | `scripts/test_installer.py::check_future_schema_refused` | ✓ | ✓ | single-group | pass |
| `AC-4` | automated | `scripts/test_installer.py::check_install_from_url_without_clone` | ✓ | ✓ | single-group | pass |
| `AC-5` | automated | `scripts/test_installer.py::check_update_fetches_new_revision` | ✓ | ✓ | single-group | pass |
| `AC-6` | automated | `scripts/test_installer.py::check_update_without_source_argument` | ✓ | ✓ | single-group | pass |
| `AC-7` | automated | `scripts/test_installer.py::check_repeat_update_is_stable` | ✓ | ✓ | single-group | pass |
| `AC-8` | automated | `scripts/test_installer.py::check_failed_fetch_leaves_install_intact` | ✓ | ✓ | single-group | pass |
| `AC-9` | automated | `scripts/test_installer.py::check_update_keeps_edited_file` | ✓ | ✓ | single-group | pass |
| `AC-12` | automated | `scripts/test_installer.py::check_update_without_record_warns` | ✓ | ✓ | single-group | pass |
| `AC-13` | automated | `scripts/test_installer.py::check_staleness_reports_distance` | ✓ | ✓ | single-group | pass |
| `AC-14` | automated | `scripts/test_installer.py::check_staleness_lists_changelog_entries` | ✓ | ✓ | single-group | pass |
| `AC-15` | automated | `scripts/test_installer.py::check_staleness_exit_status` | ✓ | ✓ | single-group | pass |
| `AC-16` | automated | `scripts/test_installer.py::check_install_named_reference` | ✓ | ✓ | single-group | pass |
| `AC-17` | automated | `scripts/test_installer.py::check_update_keeps_pin` | ✓ | ✓ | single-group | pass |
| `AC-17b` | automated | `scripts/test_installer.py::check_staleness_reports_on_pinned_install` | ✓ | ✓ | single-group | pass |
| `AC-18` | automated | `scripts/test_installer.py::check_update_moves_pin` | ✓ | ✓ | single-group | pass |
| `AC-19` | automated | `scripts/test_installer.py::check_link_mode_covers_conventions_and_standards` | ✓ | ✓ | single-group | pass |
| `AC-21` | automated | `scripts/test_installer.py::check_update_command_exists_and_parses` | ✓ | ✓ | single-group | pass |
| `AC-22` | automated | `scripts/test_installer.py::check_readme_documents_updating` | ✓ | ✓ | single-group | pass |
| `AC-23` | automated | `scripts/test_installer.py::check_documented_ignore_list_includes_record` | ✓ | ✓ | single-group | pass |

Retired before validation, per D-4: AC-10, AC-11, AC-20. Each described behavior that already worked and so could not carry failing-first evidence. Their tests remain in `scripts/test_installer.py` as regression guards bound to no criterion, alongside `check_link_mode_refused_with_fetched_source` and `check_update_keeps_files_the_installer_never_wrote`.

Overall gate result: **success**
Re-run set: **all 21 bound criteria** (no file in `thoughts/shared/validations/` carried `validated_at_code_state:`, so the touched set is every bound criterion) · sample: `scripts/test_installer.py::check_update_keeps_pin` (hash `74092dba` → index 17) · **agrees**

All 42 stored records (21 red, 21 green) were re-executed at their stored code states using a detached git worktree, across the 12 distinct revisions they reference. Every stored outcome reproduced: no red record passed, no green record failed, no command failed to re-run.

### Standards Compliance

Filtered to `sdlc_stage: implementation` and `all`; 29 statements apply.

No blocking findings. Checked directly:

- `must-command-filenames-use-snakecase`, `must-commands-include-yaml-frontmatter-name-description`, `must-frontmatter-name-match-file-stem-model-value` — `commands/core/specs_update.md` passes all three (`specs_update`, name matches stem, `model: quick`).
- `must-engineers-regenerate-standardsstatementsjson-commit` — `conventions/criterion-binding.md` changed and `standards/statements.json` is regenerated in the same branch.
- `must-acceptance-criterion-bound-exactly-individually`, `must-not-test-group-bound-more-criterion` — 21 criteria, 21 rows, no group serving two.
- `must-evidence-record-contain-command-codestate-output`, `must-records-codestate-differ-red-records-same-criterion` — all 42 records complete; every red/green pair sits at different revisions.
- `must-not-spec-criterion-name-test-file-path-test` — checked mechanically against the spec; no criterion names a test, path, or framework.
- `must-500-lines-split-into-focused-sub-files-router` — largest convention is 398 lines.
- `should-commands-stay-under-300-lines-possible` — the new command is 83 lines.

One recommendation, not a block:

- `should-engineers-run-researchcodebase-ticketresearch-before-createplan` — `/research_codebase` was not invoked as a command. The research it prescribes was performed inline before planning (every file the plan modifies was read in full, with line references carried into the plan), which satisfies the intent, but the command's own record does not exist.

### Code Review Findings

**Matches plan:**
- Install record shape matches the plan's design sketch, with `track` and `pinned` as specified (`scripts/installer_support.py`).
- Mirror clone plus `git archive` export, never a checkout, as the plan's approach section argued (`setup.sh`, `fetch_source`).
- Test groups follow the `CHECKS` registry pattern from `scripts/validate.py:397-449`, so the configured `test_group_command` binds them with no config change.
- All tests use `file://` remotes; no group touches the network.

**Deviations from plan, each recorded in the plan document:**
- The AC-5 group was rewritten mid-phase: as first written it supplied `--from` and so passed on first contact, testing the previous phase's work rather than its own.
- The closing summary was changed to stop printing paths into the temporary export directory, which is deleted before a reader could follow them.
- Three defects fixed inside phase 4 (macOS symlinked temp paths; a helper failure hidden by a process substitution, which made the installer report success having copied nothing; a kept file's edited content being adopted as the new fingerprint baseline, which would have let the following update overwrite it).
- The data-loss defect above, found during this validation.

**Potential issues:**
- A non-writable cache directory is not handled gracefully (see the concern above).
- `--check` exits 1 on a pinned install that is behind. Defensible — a newer revision does exist — but a project pinned deliberately will fail a CI gate every run. Watch it in use.

### Manual Testing Required

- [x] Install from the real GitHub URL into an empty directory with no clone present
- [x] Update from inside a target with no arguments; confirm it uses the recorded source
- [x] Edit two installed files, update three times, confirm both survive every time
- [x] Add a project-local command, update three times, confirm it survives and stays out of the record
- [x] Run an update against an unreachable source; confirm nothing changes
- [x] Read the staleness report for a behind install and for a pinned one
- [ ] Run `/specs_update` inside a real agent session (not exercised; the command's file is validated, its behavior in-session is not)

### Recommendations

1. Cut the tags before merge lands anywhere public: `v1.0.0` on `f6f7a63`, `v2.0.0` on `main` afterwards. Until `v2.0.0` exists, the README's pinning example names a tag that cannot be resolved.
2. Split this branch into a stack before review. The code diff is ~2,100 lines across twelve files, which crosses the enforced 1,000-line rule twice over.
3. Consider a future criterion for the kept-file-also-changed-upstream case (concern above).
4. Handle a non-writable cache directory with a message rather than a bare `set -e` exit.
