---
date: 2026-08-24
branch: main
status: draft
tags:
  - installer
  - distribution
  - versioning
---

# Installer Update Mechanism — Requirements Spec

**Slug:** `installer-update-mechanism` · **Target repo:** project-specs · **Date:** 2026-08-24
**Status:** Draft — complete. All 3 open questions closed by owner decision 2026-08-24; ready for `/create_plan`.
**Decision record:** `thoughts/decisions/framework-distribution-and-updates.md` (ADR-001, Option D)

---

## 1. Problem Statement

A developer who installs this framework into another repository cannot tell whether the copy they have is current, and cannot bring it up to date without knowing where the framework's own clone sits on their machine.

Three concrete failures, verified against the installer and against the live install in `agent-readiness-cli`:

1. **No record of what was installed.** The installer writes no source URL, no commit reference, and no install date into the target repository. Confirming that an install is current requires diffing the target against a clone by hand.
2. **The update flag does not fetch.** Update mode re-copies whatever files sit in the local clone at that moment. If that clone is behind the source repository, the update installs stale files and reports success.
3. **Updates destroy local edits without warning.** The PR description template is overwritten on every run. The convention documents and the standards registry are deleted and re-copied, so a project-local convention or a project-local standards entry is lost with no message.

Two further gaps block the workaround paths:

4. **Symlink mode covers half the framework.** It links the agent and command directories only. The convention documents and the standards registry are always copied, so a symlinked install still goes stale on the documents that `/check_standards` reads.
5. **The installer requires a pre-existing local clone.** There is no way to install or update directly from the source repository URL, so a fresh machine or a CI runner cannot install without a manual clone step first.

**Who is affected:** every developer using the framework in a repository other than this one. Today that is one person across at least one consumer repository; the framework is being handed to others.

---

## 2. Desired Outcome

A developer working inside a consumer repository can answer two questions and take one action, without leaving that repository and without knowing where the framework source lives:

- *Is my install current?* One command reports current or behind, says how far behind, and lists what changed.
- *Bring me up to date.* One command fetches the source, updates the installed files, and reports which files it left alone because the developer had edited them.

Each consumer repository controls its own version. Upgrading one repository does not move any other. A developer can hold a repository on a fixed version and stay there across updates.

The framework files stay out of the consumer repository's git history, as they are today.

---

## 3. Acceptance Criteria

Vocabulary used below, all solution-neutral:

- **installer** — the program the developer runs to install or update the framework.
- **source repository** — the git repository the framework is published from.
- **target repository** — the repository the framework is installed into.
- **install record** — the file the installer writes into the target repository to describe the current install.
- **convention documents** and **standards registry** — the two file sets the installer copies today that symlink mode does not cover.

### Install record

**AC-1 — A fresh install writes an install record.**
`mode: automated`
Given a target repository with no prior install, when the installer completes, then an install record exists in the target repository stating the record's own format version, the source repository location, the requested reference, the exact source revision installed, the provider, the install mode, and the time of the install.

**AC-2 — The install record carries a content fingerprint for every file the installer wrote.**
`mode: automated`
Given a completed install, when the install record is read, then it lists every file the installer wrote together with a fingerprint of that file's content, and each listed fingerprint equals the fingerprint computed from the file on disk.

**AC-3 — An installer reading an install record of an unknown format version refuses to act on it.**
`mode: automated`
Given an install record whose format version is higher than the version the installer understands, when the developer runs an update, then the installer changes no file, exits with a failure status, and reports that the record was written by a newer installer.

### Installing and updating from the source repository

**AC-4 — The installer installs from a source repository location with no pre-existing local clone.**
`mode: automated`
Given a machine with no local copy of the framework, when the developer runs the installer against a target repository and supplies the source repository location, then the framework installs into the target repository and the install record states that location.

**AC-5 — An update fetches the source before copying.**
`mode: automated`
Given an install whose record states revision A, and the source repository has since advanced to revision B, when the developer runs an update, then the installed files match revision B and the install record states revision B.

**AC-6 — An update needs no source location from the developer.**
`mode: automated`
Given a target repository containing an install record, when the developer runs an update from inside that target repository and supplies no source location, then the update completes using the source location and reference stated in the record.

**AC-7 — Running the same update twice changes nothing the second time.**
`mode: automated`
Given a completed update and no change in the source repository, when the developer runs the update again, then every installed file has the same content as before, and the install record differs only in its install time.

**AC-8 — A failed fetch leaves the existing install untouched.**
`mode: automated`
Given an install record whose source repository cannot be reached, when the developer runs an update, then every installed file keeps its previous content, the install record is unchanged, and the installer exits with a failure status and names the source it could not reach.

### Protecting the developer's own edits

**AC-9 — An update keeps a file the developer edited.**
`mode: automated`
Given an installed file whose current content fingerprint differs from the fingerprint in the install record, when the developer runs an update, then that file's content is unchanged and the installer's output names the file as kept.

**AC-10 — An update replaces a file the developer did not edit.**
`mode: automated`
Given an installed file whose current content fingerprint matches the fingerprint in the install record, and the source repository has a different version of that file, when the developer runs an update, then the file on disk matches the source version.

**AC-11 — An update never overwrites the project's own configuration file.**
`mode: automated`
Given a target repository whose project configuration file has been customized, when the developer runs an update, then that file's content is unchanged.

**AC-12 — An update on an install made before this feature existed completes and says protection was unavailable.**
`mode: automated`
Given a target repository holding an install with no install record, when the developer runs an update, then the update completes, an install record is written, and the output states that edited-file protection could not be applied for this run.

### Reporting staleness

**AC-13 — The staleness report names how far behind an install is.**
`mode: automated`
Given an install record stating revision A and a source repository whose reference has advanced past A, when the developer runs the staleness check, then the output states that the install is behind and states the number of source revisions between A and the current one.

**AC-14 — The staleness report lists what changed.**
`mode: automated`
Given an install that is behind, when the developer runs the staleness check, then the output includes the change-log entries the source repository added between the installed revision and the current one.

**AC-15 — The staleness check exits with a failure status when behind, and success when current.**
`mode: automated`
Given an install that is behind, when the developer runs the staleness check, then the exit status is non-zero; given an install at the current revision, the same check exits zero and states that the install is current.

### Pinning a version

**AC-16 — A developer can install a named reference.**
`mode: automated`
Given a source repository holding more than one reference, when the developer installs and names one of them, then the installed files match that reference and the install record states both the requested reference and the exact revision it resolved to.

**AC-17 — An update on a pinned install stays on its pinned reference.**
`mode: automated`
Given an install record naming a fixed revision, when the developer runs an update without naming a different reference, then the installed files still match that revision and the installer reports that the install is pinned.

**AC-17b — The staleness check reports a newer revision even on a pinned install.**
`mode: automated`
Given an install pinned to a fixed revision, and the reference that pin was taken from has since advanced, when the developer runs the staleness check, then the output states that the install is pinned, names the newer revision available on that reference, and does not change any installed file.

**AC-18 — A developer can move a pinned install to a different reference.**
`mode: automated`
Given a pinned install, when the developer runs an update and names a different reference, then the installed files match the new reference and the install record states it.

### Symlink mode

**AC-19 — Symlink mode covers the convention documents and the standards registry.**
`mode: automated`
Given a target repository installed in symlink mode for the default provider, when a file in the source repository's convention documents or standards registry changes, then reading the corresponding file through the target repository returns the changed content without re-running the installer.

**AC-20 — Symlink mode is refused for any provider that needs a format conversion.**
`mode: automated`
Given a provider whose install converts source files into another format, when the developer asks for symlink mode, then the installer reports that symlink mode is unavailable for that provider and completes the install by copying.

### Discoverability

**AC-21 — The staleness check and the update are reachable from inside an agent session.**
`mode: automated`
Given the framework installed for the default provider, when the developer lists the available commands, then a command exists whose stated purpose is to check for and apply framework updates, and it carries the frontmatter fields every command in this framework requires.

**AC-22 — The framework's own documentation explains how to update an existing install.**
`mode: automated`
Given the framework's main documentation, when it is read, then it contains a section on updating an existing install that names the staleness check, the update, and how to pin a reference.

**AC-23 — The recommended ignore list in the documentation includes the install record.**
`mode: automated`
Given the documented list of paths a consumer repository is advised to keep out of git, when it is read, then the install record's path appears in it.

**Retired identifiers:** none. AC-17b was inserted after the first draft under the suffix rule, so no identifier was renumbered.

---

## 4. Scope Boundaries

Explicitly **out of scope** for this work:

1. **Publishing the framework as an installable package** (pip, npm, or similar). ADR-001 records this as the follow-on step once other teams depend on the framework. Nothing here blocks it.
2. **Cutting a first release tag and restructuring the change log.** Named-reference pinning (AC-16) works against branches and revisions without any tag existing. Tagging is listed under Dependencies, not here.
3. **Merging a developer's edits with upstream changes.** When a file has been edited, the installer keeps it and says so (AC-9). It does not attempt a three-way merge, produce conflict markers, or offer to reconcile the two versions.
4. **Changing whether consumer repositories commit or ignore the framework files.** Consumer repositories keep ignoring them. This work adds one more ignored path (AC-23).
5. **Uninstall or rollback to a previous install.** A developer who wants an earlier version names that reference and updates to it (AC-18). There is no separate uninstall action and no stored history of past installs.
6. **Automatic or scheduled update checks.** Nothing runs on a timer, on shell start, or on agent session start. The developer runs the check.
7. **Sharing one install across developers on a team.** Each developer installs into their own working copy.
8. **Migrating the existing install in any consumer repository.** AC-12 makes an update work against a record-less install; performing that update in any specific repository is a separate task.
9. **Changing what the installer installs.** The set of files copied, the provider conversions, and the destination paths stay as they are, apart from symlink mode's coverage (AC-19).
10. **Verifying that the source repository is authentic.** No signature checking, no revision allow-list, no supply-chain verification of the fetched source.
11. **Windows support.** The installer targets macOS and Linux shells, as it does today.

---

## 5. Assumptions

**Confirmed** — verified against the repository during this spec:

- **ASM-1.** The installer copies six file sets into a target repository: agents, commands, convention documents, the standards registry, the project configuration file, and the PR description template. Verified by reading the installer end to end.
- **ASM-2.** Symlink mode is applied only to the agent and command directories. The convention documents and the standards registry are copied unconditionally in every mode. Verified at the installer's directory-install helper and at its two convention and standards blocks.
- **ASM-3.** Update mode does not fetch. It resolves its source from the directory the installer script itself sits in. Verified: the script sets its source directory from its own location and never invokes git.
- **ASM-4.** The PR description template is overwritten on every run, including update runs. Verified.
- **ASM-5.** The project configuration file is written only when absent, so update runs preserve it. Verified.
- **ASM-6.** In `agent-readiness-cli`, every path the installer writes is listed in that repository's ignore file, so no framework file enters its history. Verified.
- **ASM-7.** The source repository has no tags, and its change log keeps every entry under an unreleased heading. Verified.
- **ASM-8.** The installer already depends on `python3` and PyYAML to read provider manifests, so this work introduces no new language runtime.
- **ASM-9.** The framework publishes its read-only agents through a separate community-skills channel. That channel carries only those agents and is unaffected by this work.
- **ASM-10.** The framework's change log follows Keep a Changelog headings, so AC-14's per-revision entries can be extracted from it.
- **ASM-11.** The live install in `agent-readiness-cli` currently matches the source repository byte for byte, so no drift has to be reconciled as part of this work. Verified by directory diff.

**Needs confirmation** — believed true, not verified:

- **ASM-12.** Every machine that runs an update has `git` installed and network access to the source repository at update time.
- **ASM-13.** The developer running an update has write permission to a per-user cache location outside the target repository.
- **ASM-14.** No consumer repository has intentionally edited an installed convention document or standards entry that an update would now report as kept. If any has, AC-9 preserves it and the report makes it visible.

---

## 6. Dependencies

- **Git and network access** on the machine running an update (see ASM-12). The staleness check and the update both fail cleanly without them (AC-8).
- **A cache location for fetched sources** outside the target repository (see ASM-13).
- **A way to run one named test group individually** in this repository. The repository's configuration already defines this, and the existing validation script already supports selecting a single check by name, so the pairing gate can bind each automated criterion here without new infrastructure.
- **A first release tag** is *not* a blocker for this work, but pinning is more useful once tags exist. Cutting one is tracked in ADR-001's action list.
- **No unresolved team decision** blocks the work beyond the three open questions in section 7.

---

## 7. Resolved Decisions

All questions raised during drafting are closed. Owner decisions, 2026-08-24, binding on the plan.

| ID | Decision | Effect on the criteria |
|---|---|---|
| **D-1** | The install record stays out of the consumer repository's git history, ignored alongside every other framework file. | AC-23 stands as written. No CI staleness gate is possible in a consumer repository, and that is accepted. |
| **D-2** | An update fetches the source repository by default. No separate flag is needed for the common case. | AC-5 and AC-6 stand as written. AC-8 becomes the load-bearing failure path: an unreachable source must leave the install untouched and fail loudly. |
| **D-3** | The staleness check reports a newer revision on a pinned install rather than staying silent. It reports; it never moves the pin. | New **AC-17b**. AC-17 is unchanged: an update on a pinned install still stays on its pinned revision. |

No open questions remain.

## 8. Standards Notes

Checked against the standards registry, filtered to the planning stage and to statements that apply at all stages. No acceptance criterion above conflicts with an enforced standard. Two notes carried forward, neither of which blocks this spec:

- **Command naming.** AC-21 adds a command. Enforced naming standards require command filenames in snake_case, frontmatter carrying name, description, and model, a frontmatter name matching the filename stem, and a model value that is a semantic tier rather than a literal model name. AC-21 states the frontmatter requirement without naming the file, leaving the name to the plan.
- **PR stacking.** Enforced review-stage standards require stacking a PR when its diff exceeds 1,000 lines, and recommend stacking above 500 lines or when a change spans more than three files across more than one architectural layer. This work touches the installer, the convention or documentation set, a new command, and a new test harness, so it will very likely cross a stacking threshold. The plan should decompose it into layers.

---

## 9. Verification of this spec

- [x] Every criterion has a pass/fail test.
- [x] Every criterion carries a unique identifier and exactly one mode line.
- [x] No criterion names a test, a file path, or a test framework.
- [x] No criterion is `manual-only`, so no manual-only approval section is required.
- [x] Scope boundaries state what is out of scope, with 11 entries.
- [x] Assumptions listed: 11 confirmed, 3 needing confirmation.
- [x] **Open questions resolved** — all 3 closed by owner decision on 2026-08-24 and recorded in section 7 as D-1, D-2, and D-3.
