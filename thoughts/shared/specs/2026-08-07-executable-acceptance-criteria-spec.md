# Executable Acceptance Criteria — Requirements Spec

**Slug:** `executable-acceptance-criteria` · **Target repo:** project-specs · **Date:** 2026-08-07
**Status:** Revision 3 — upgraded to labeled format; manual-only set APPROVED 2026-08-07 — complete under its own rules
**Author:** spec-author persona (A2), dispatched per agent-personas catalog

---

## Revision log

| Change | Why |
|---|---|
| AC-3, AC-6, AC-12 reworded: the **plan** binds tests, the spec assigns ID + mode only. | Owner decision on OQ-1. Restores solution-neutrality and removes the conflict with `spec.md:191`. |
| Pairing unit changed from "test" to **named test group** (class / describe block / file) throughout AC-3, AC-7, AC-8. | Owner decision on OQ-6. |
| AC-17 amended to cover sampled re-runs. | Owner decision on OQ-4 introduces sampling, which would have made AC-17 unsatisfiable unless the sample is selected deterministically. Found in self-review. |
| New AC-30 (single-group invocation config + degradation), AC-31 (evidence record contents), AC-32 (re-run sampling), AC-33 (dogfooding mapping), AC-34 (degraded evidence labeling). | Adopting the resolved defaults for OQ-3, OQ-4, OQ-5. |
| ASM-16 – ASM-19 promoted to **Confirmed**. New ASM-20 – ASM-24 added from further verification. | Owner decisions plus fresh evidence gathered for revision 2. |
| OQ-1 – OQ-8 marked resolved with decisions retained inline; new OQ-9 – OQ-13 opened. | Two of the new ones are verified structural findings, not speculation. |
| **Revision 3 upgrade (in place, additive only).** Inserted one `mode:` line after every criterion heading; inserted the four fixed labels (*Why not automated / Steps / Pass-fail / Performed by*) into each manual-only block; added the `## Manual-Only Approval` section. No criterion sentence was reworded, restructured, reordered, or deleted; nothing was bound to a test name. Split: 5 automated, 31 manual-only, 36 total (incl. AC-35, added post-rev-2 with D-10). | This document became legacy under its own AC-19/AC-21 once the feature shipped; `/spec` Step 5 applied to it. |
| **Correction to the coordinator's rationale for OQ-7.** The claim "ticket_oneshot inherits the gate automatically because it invokes validate_plan" is **false**. `commands/integrations/ticket_oneshot.md` chains `/ticket_research` → `/ticket_plan` → `/ticket_impl` → `/describe_pr` (`:31, :40, :49, :54`) and contains **no** reference to `validate_plan`, `/spec`, or the Definition of Done. The out-of-scope decision stands; the rationale does not. See ASM-20, ASM-21, OQ-9. | Evidence standard: a scope decision resting on a false premise is a silent hole. |

Identifiers are never reassigned (AC-1 applied to this document itself). No AC ID from revision 1 changed meaning; none are retired.

---

## Resolved decisions and defaults

Owner-authoritative (binding):

| ID | Decision |
|---|---|
| D-1 (was OQ-1) | The **plan** binds tests. The spec assigns each criterion a stable ID and a mode (`automated` \| `manual-only`) and nothing more. `/create_plan` names the concrete test group per automated criterion. |
| D-2 (was OQ-2) | The gate is a **command procedure** whose pairing and red→green verdicts are reproducible from artifacts alone (AC-17), backed by **re-runnable** evidence records. A shipped deterministic checker is an explicit future-phase candidate, out of scope here. |
| D-3 (was OQ-6) | The pairing unit is one **individually runnable named test group** (class, `describe` block, or file). Injectivity holds at group level: no group serves two criteria. |
| D-9 (was OQ-10) | The dogfooding split is **accepted**: this feature's own spec lands ~8 automated / ~21 manual-only criteria under AC-33's rule. Manual-only is a legitimate, visible state; a behavioral harness that could flip prompt-following criteria to automated is a future project, not reopened here. Owner decision, 2026-08-07. |
| D-10 (was OQ-13) | Degraded evidence blocks **by stakes**: for criteria touching deny-list domains (auth, billing, data integrity, security), degraded evidence is not accepted — the blocking verdict applies (AC-35). Elsewhere, the degraded label (AC-34) suffices. Owner decision, 2026-08-07. |

Owner-approvable defaults (adopted here; reversible on review):

| ID | Default |
|---|---|
| D-4 (was OQ-3) | An **optional project-level configuration for invoking a single named test group**. When unset, red/green evidence **degrades** to full-suite runs with the paired group's result identified in output, reported as weaker evidence — never silently counted as equal. Key name/shape/template syntax are the plan's decisions. |
| D-5 (was OQ-4) | An evidence record contains: the **exact invocation command**, the **code-state reference** it ran against, and the **captured result**. `/validate_plan` re-runs at least one sampled paired group per validation from the recorded command. Evidence that cannot be re-run is treated as **absent**. |
| D-6 (was OQ-5) | **Dogfooding, stated as a decision:** for this repo's own changes, the assertions in `scripts/validate.py`, `scripts/run_evals.py`, and the `build_skills.py` drift check are the named test groups. No new harness. Criteria no script assertion can reach are labeled `manual-only` under AC-4/AC-5. |
| D-7 (was OQ-7) | Other commands out of scope. `founder_mode` exempt by construction (retro-documentation; failing-first impossible); noting that in its own doc is a future one-line change. `ticket_oneshot` out of scope — but it does **not** currently inherit the gate (see revision-log correction and OQ-9). |
| D-8 (was OQ-8) | `manual-only` criteria under `ci_mode: true` yield a **deferred verdict a human must close** — non-success, distinguishable from a defect block, non-halting. Not a hard block. |


---

## Manual-Only Approval

```
approved_by: Dj Haile (recorded via chat approval of the full 31-item list)
approved_at: 2026-08-07
```

Per AC-5, the manual-only set below is presented for explicit human approval. The document is not complete under its own rules until `approved_by` and `approved_at` are filled by the owner. **31 of 36 criteria are manual-only; 5 are automated** (AC-22, AC-24, AC-27, AC-28, AC-29).

- **Group A — prompt-following behavior of `/spec` and `/create_plan` (7):** AC-1, AC-2, AC-3, AC-3b, AC-4, AC-5, AC-6 — identifier assignment, mode labeling, binding, solution-neutrality, completeness, approval gating, and plan refusal are all markdown-command behaviors no script assertion reaches (D-6).
- **Group B — `/implement_plan` and evidence production (8):** AC-7, AC-8, AC-9, AC-10, AC-11, AC-30, AC-31, AC-34 — evidence records, first-run-pass rejection, checkbox suppression, precedence, invocation-path selection, and degraded labeling are command behaviors.
- **Group C — the `/validate_plan` gate (9):** AC-12, AC-13, AC-14, AC-15, AC-16, AC-17, AC-18, AC-32, AC-35 — accounting, verdicts, reproducibility, sampling, and stakes-based blocking are command behaviors observable only by running the command.
- **Group D — legacy handling (3):** AC-19, AC-20, AC-21 — classification, unenforced wording, and the upgrade path are command behaviors.
- **Group E — deterministic check exists but cannot produce red evidence (4):** AC-23, AC-25, AC-26 (already-true invariants; binding would permanently block, per plan review-item-1) and AC-33 (the mapping is produced by `/create_plan`).

### Review notes (flagged, not fixed — `/spec` Step 5.1)

**(a) Pre-existing path-like tokens.** Many criterion blocks and `*Check:*` lines contain script names and `file:line` citations. Under AC-3b these would be forbidden in a **new** spec; here they are the subject matter — this spec is about those files — not test bindings. The author must either accept this as a standing carve-out for framework-self-referential specs or reword in a future revision.

**(b) `*Check:*` lines predate the four-element format.** They now sit alongside the *Steps* / *Pass/fail* labels and partially duplicate them; retained verbatim per the additive-only rule. A future revision may fold them in.

---

## 1. Problem Statement

`/spec` emits acceptance criteria as given/when/then prose (`commands/core/spec.md:50-59`). Nothing downstream binds a criterion to a mechanical check.

The chain leaks at three joints:

- **Spec → plan.** `create_plan` requires only that "every acceptance criterion from the spec maps to at least one phase" (`create_plan.md:547`). A phase is a unit of work, not a check. A criterion can map to a phase whose success criteria never exercise it.
- **Plan → implementation.** `implement_plan` verifies against *the plan's* success criteria (`implement_plan.md:71-78`), which are generic build/test/lint commands (`create_plan.md:296-302`). No step ties a passing suite to a specific criterion, and no step requires a test to have failed first.
- **Implementation → validation.** `validate_plan` requires "each spec acceptance criterion has an explicit pass/fail verdict" (`validate_plan.md:233`), but that verdict is produced by a model or human reading prose against code. Its own Red Flags section names the failure mode (`validate_plan.md:224`).

**Who has the problem.** The repo owner and any team installing project-specs. Cost of not solving it: an acceptance criterion can be silently dropped while build, tests, lint, and the validation report all stay green. The standing Definition of Done already asserts the correct bar (`references/definition-of-done.md:21`) but supplies no per-criterion mechanism, so the item is satisfiable by assertion.

---

## 2. Desired Outcome

For any work driven by a spec produced after this change:

1. Every acceptance criterion is labeled at spec time with exactly one verification mode — **automated** or **manual-only** — and carries a stable identifier. The spec names no tests.
2. `/create_plan` binds every automated criterion to exactly one individually runnable named test group, injectively, before the plan is complete.
3. Every automated criterion has a **re-runnable** evidence record showing its paired group failing against the pre-change code and passing against the post-change code. A group that passed on first contact is not evidence.
4. `/validate_plan` emits one record per criterion, re-runs a deterministically sampled paired group, and returns a **blocking** verdict if any automated criterion is unbound, or any paired group lacks a re-runnable failing-first record.
5. Manual-only criteria stay visibly unresolved until a human records a verdict. In `ci_mode`, they produce a deferred, non-halting, non-success verdict.
6. Specs written before this change keep working and are reported as *unenforced legacy*, never as *passed*.
7. The framework's four CI jobs stay green and the changed command files remain single-source, provider-neutral markdown.

Observable end state for the owner: "if a criterion gets skipped, validation goes red on its own — I don't have to catch it."

---

## 3. Acceptance Criteria

### A. Spec-time labeling and traceability

**AC-1 — Criterion identity.**
`mode: manual-only`
- *Why not automated:* asserts `/spec`'s identifier-assignment behavior in a markdown command; no assertion in the repo's three scripts can reach it (D-6).
- *Steps:* Run `/spec` twice on the same subject, deleting one criterion on the second pass, then list every identifier in both outputs.
- *Pass/fail:* Pass if identifiers are unique within each document and no identifier refers to a different criterion across the two; fail on any reuse.
- *Performed by:* repo owner (Dj)
Given a spec produced by `/spec`, when the document is declared complete, then every acceptance criterion carries an identifier unique within that document, and no identifier from a prior revision is ever reassigned to a different criterion (a deleted criterion retires its identifier).
*Check:* parse criteria; assert uniqueness; diff two revisions and assert no identifier changed referent.

**AC-2 — Mode is declared, exactly once.**
`mode: manual-only`
- *Why not automated:* asserts `/spec`'s labeling behavior in a markdown command; unreachable by script assertion (D-6).
- *Steps:* Inspect every criterion in a freshly produced spec for its mode line.
- *Pass/fail:* Pass if each criterion carries exactly one token from {automated, manual-only}; fail on zero, two, or an unrecognized token.
- *Performed by:* repo owner (Dj)
Given any acceptance criterion, when the spec is declared complete, then it is labeled with exactly one mode from the closed set {automated, manual-only}. Zero labels, two labels, or an unrecognized label makes the spec incomplete.

**AC-3 — Plan-time one-to-one binding (revised per D-1, D-3).**
`mode: manual-only`
- *Why not automated:* the binding is produced by `/create_plan` prose; no script assertion can inspect a generated plan (D-6).
- *Steps:* Run `/create_plan` on a spec with at least two automated criteria and extract the criterion→group map from the resulting plan.
- *Pass/fail:* Pass if every automated criterion names exactly one individually runnable group and no group appears twice; fail on any missing, duplicated, or shared group.
- *Performed by:* repo owner (Dj)
Given a criterion labeled `automated`, when `/create_plan` declares the plan complete, then the plan binds that criterion to exactly one **individually runnable named test group** (class, `describe` block, or file), and the criterion→group map is **injective at group level**.
*Check:* build the map from the plan; assert every automated criterion has exactly one group and no group repeats.

**AC-3b — The spec stays solution-neutral (negative, new in rev 2).**
`mode: manual-only`
- *Why not automated:* asserts a property of `/spec`'s generated output, not of any file in this repo; unreachable by script assertion (D-6).
- *Steps:* Search a freshly produced spec for test identifiers, file paths, and framework names attached to individual criteria.
- *Pass/fail:* Pass if criteria carry mode labels only; fail if any criterion names a test, path, or framework.
- *Performed by:* repo owner (Dj)
Given a spec produced by `/spec`, when inspected, then it contains no test identifiers, file paths, or framework names for any criterion. Mode labels only.
*Check:* assert no criterion carries a test-name field; the existing `spec.md:191` verification item still passes.

**AC-4 — Manual-only criteria are fully specified.**
`mode: manual-only`
- *Why not automated:* completeness of the four elements is enforced by command procedure inside `/spec`; unreachable by script assertion (D-6).
- *Steps:* For each manual-only criterion in a freshly produced spec, check for all four labels.
- *Pass/fail:* Pass if all four elements are present on every manual-only criterion; fail if any is missing.
- *Performed by:* repo owner (Dj)
Given a criterion labeled `manual-only`, when the spec is declared complete, then it records: (a) why automation is not feasible, (b) exact steps, (c) the observable pass/fail condition, (d) who performs it. Any missing element makes the spec incomplete.

**AC-5 — Manual-only requires recorded human approval (negative).**
`mode: manual-only`
- *Why not automated:* the approval-before-save interaction, including its `ci_mode` branch, is a markdown command behavior (D-6).
- *Steps:* Finalize a spec containing an unapproved manual-only criterion twice — once interactively, once with `ci_mode: true`.
- *Pass/fail:* Pass if the interactive run refuses to save as complete until approval is recorded and the `ci_mode` run stops and reports; fail if either writes a complete spec.
- *Performed by:* repo owner (Dj)
Given one or more `manual-only` criteria, when `/spec` finalizes, then it must **not** save the spec as complete until the manual-only set and per-criterion reasons have been presented to a human and approval recorded. Under `ci_mode: true`, it stops and reports rather than self-approving.

**AC-6 — No plan completes with an unbound automated criterion (negative, revised per D-1).**
`mode: manual-only`
- *Why not automated:* the refusal is a `/create_plan` command behavior; unreachable by script assertion (D-6).
- *Steps:* Run `/create_plan` against a spec with one automated criterion deliberately left unbound.
- *Pass/fail:* Pass if the plan is not declared complete and the unbound identifier is named in the refusal; fail if the plan completes.
- *Performed by:* repo owner (Dj)
Given a post-change spec, when `/create_plan` would declare the plan complete while at least one `automated` criterion lacks a test-group binding, then it must **not** declare the plan complete; it reports the unbound criterion identifiers and stops. (Parallel to `spec.md:79`.)

### B. Failing-first evidence

**AC-7 — Red evidence exists (revised per D-3).**
`mode: manual-only`
- *Why not automated:* red-record production is an `/implement_plan` command behavior in a downstream project; unreachable by script assertion (D-6).
- *Steps:* Implement one criterion, then inspect its red record for group name, code-state reference, and observed failure.
- *Pass/fail:* Pass if a failing run against pre-change code is recorded with all three elements; fail if any is missing or no red record exists.
- *Performed by:* repo owner (Dj)
Given an automated criterion and its bound test group, when the work satisfying that criterion is implemented, then a record exists showing that **group failing** against the pre-change code, identifying the group, the code-state reference, and the observed failure.

**AC-8 — Green evidence exists and is distinguishable (revised per D-3).**
`mode: manual-only`
- *Why not automated:* green-record production and code-state comparison are `/implement_plan` command behaviors (D-6).
- *Steps:* Inspect the green record and compare its code-state reference against the red record's.
- *Pass/fail:* Pass if a passing run is recorded and the two code-state references differ; fail if they match or the record is absent.
- *Performed by:* repo owner (Dj)
Given the same criterion, when implementation completes, then a record exists showing that **group passing**, identifying group and code-state reference, where that reference differs from the red record's.

**AC-9 — A first-run pass is not evidence (negative).**
`mode: manual-only`
- *Why not automated:* the rejection is a judgment step inside a markdown command; unreachable by script assertion (D-6).
- *Steps:* Seed a tautological test group, record its first run against pre-change code, and read the resulting criterion verdict.
- *Pass/fail:* Pass if the criterion reports unsatisfied and names both possible causes; fail if it reports passed.
- *Performed by:* repo owner (Dj)
Given a bound group whose first recorded run against pre-change code **passes**, then that run must **not** satisfy AC-7. Reported as unsatisfied, naming both possible causes: the group does not discriminate the change, or the behavior already exists.

**AC-10 — No completion without red evidence (negative).**
`mode: manual-only`
- *Why not automated:* checkbox suppression is an `/implement_plan` command behavior (D-6).
- *Steps:* Delete the red record, then run `/implement_plan` up to the bound plan item.
- *Pass/fail:* Pass if the checkbox stays unchecked and the missing failing-first evidence is reported; fail if the item is checked off.
- *Performed by:* repo owner (Dj)
Given an automated criterion with no red record, when `/implement_plan` reaches the plan item bound to it, then it must **not** check that item off, and must report the missing failing-first evidence.

**AC-11 — Red→green does not displace existing checks.**
`mode: manual-only`
- *Why not automated:* the precedence rule is applied by command procedure across `/implement_plan` and `/validate_plan` (D-6).
- *Steps:* Produce valid red→green evidence for every automated criterion while leaving one pre-existing suite test failing, then assess completion.
- *Pass/fail:* Pass if the work is not reported complete; fail if valid evidence alone completes it.
- *Performed by:* repo owner (Dj)
Given valid red and green evidence for every automated criterion, the pre-existing obligations (full suite passing, no regressions — `definition-of-done.md:19-22`, `implement_plan.md:144-148`) still apply unchanged.

**AC-30 — Single-group invocation, with defined degradation (new, per D-4).**
`mode: manual-only`
- *Why not automated:* invocation-path selection happens inside a markdown command in a downstream project; unreachable by script assertion (D-6).
- *Steps:* Produce evidence three ways — configured single-group run; full-suite run with the group's result identifiable in output; full-suite run without it.
- *Pass/fail:* Pass if the first two are accepted and the third is rejected; fail if the unattributable run is accepted.
- *Performed by:* repo owner (Dj)
Given a downstream project with single-group invocation configured, when red or green evidence is produced, then only the bound group is executed and the record reflects that. Given a project without it, evidence may come from a full-suite run **provided the bound group's individual result is identifiable in the captured output**; a full-suite run where it is not identifiable does **not** satisfy AC-7/AC-8.

**AC-31 — Evidence record contents (new, per D-5).**
`mode: manual-only`
- *Why not automated:* record-contents enforcement is a command behavior over artifacts that live outside this repo (D-6).
- *Steps:* Inspect each red and green record for invocation command, code-state reference, and captured result.
- *Pass/fail:* Pass if all three elements are present; fail — record treated as absent — if any is missing.
- *Performed by:* repo owner (Dj)
Given any red or green evidence record, then it contains all three of: exact invocation command, code-state reference, captured result. A record missing any element is treated as absent.

**AC-34 — Degraded evidence is labeled and never counted equal (negative, new, per D-4).**
`mode: manual-only`
- *Why not automated:* the labeling appears in `/validate_plan`'s generated report prose; unreachable by script assertion (D-6).
- *Steps:* Produce degraded evidence, run `/validate_plan`, and read that criterion's record and surrounding wording.
- *Pass/fail:* Pass if the record is marked degraded with a reason and no wording equates it to single-group evidence; fail otherwise.
- *Performed by:* repo owner (Dj)
Given evidence produced via the degraded full-suite path, when `/validate_plan` reports, then that criterion's record is marked degraded with the reason, and the report must **not** present it as equivalent to single-group evidence.

**AC-35 — Degraded evidence blocks on high-stakes criteria (negative, new, per D-10).**
`mode: manual-only`
- *Why not automated:* the stakes-based blocking verdict is a `/validate_plan` command behavior; no script assertion reaches a generated report (D-6).
- *Steps:* Run `/validate_plan` three times — a deny-list-domain criterion with only degraded evidence; the same criterion with single-group evidence; a `none`-stakes criterion with degraded evidence.
- *Pass/fail:* Pass if the outcomes are block, pass, and labeled-not-blocked respectively; fail on any other combination.
- *Performed by:* repo owner (Dj)
Given a criterion whose subject matter touches a deny-list domain (auth, billing, data integrity, security), when its only evidence is degraded (full-suite path per AC-30), then `/validate_plan` applies the blocking verdict for that criterion, naming the domain match and the missing single-group configuration as the remediation. Deny-list domain identification is recorded in the plan alongside the binding (the plan's decision per D-1), so the gate reads it from artifacts, not judgment (consistent with AC-17).
*Check:* seeded high-stakes criterion with degraded evidence → block; same criterion with single-group evidence → pass; non-deny-list criterion with degraded evidence → labeled, not blocked.

### C. `validate_plan` gate behavior

**AC-12 — Complete per-criterion accounting (revised per D-1).**
`mode: manual-only`
- *Why not automated:* the accounting is generated report content from a markdown command (D-6).
- *Steps:* Run `/validate_plan`, count records against the spec's criterion count, and inspect each record's fields.
- *Pass/fail:* Pass if counts match exactly and all seven fields are present per record; fail on any omission or merge.
- *Performed by:* repo owner (Dj)
Given spec, plan, and implementation, when `/validate_plan` runs, then its report contains exactly one record per acceptance criterion — no omissions, no merges — each carrying: identifier, mode, **bound test group from the plan** (or "none"), red evidence status, green evidence status, evidence strength (single-group or degraded), verdict.

**AC-13 — Block on unbound automated criterion.**
`mode: manual-only`
- *Why not automated:* the verdict is produced by `/validate_plan` prose; unreachable by script assertion (D-6).
- *Steps:* Remove one automated criterion's binding and run `/validate_plan`.
- *Pass/fail:* Pass if the overall verdict is the distinct blocking verdict and the identifier is named; fail on any pass-with-notes or pass-with-recommendations outcome.
- *Performed by:* repo owner (Dj)
Given any `automated` criterion with no bound test group, when `/validate_plan` completes, then the overall verdict is a distinct **blocking** verdict — not "pass with notes" — and the report names the criterion identifier.

**AC-14 — Block on never-failed group.**
`mode: manual-only`
- *Why not automated:* the verdict is a `/validate_plan` command behavior (D-6).
- *Steps:* Run `/validate_plan` twice — once with the red record removed, once with a red record showing a pass.
- *Pass/fail:* Pass if both runs produce the blocking verdict naming criterion and group; fail if either passes.
- *Performed by:* repo owner (Dj)
Given any bound group with no red record, or whose red record shows a pass, then the overall verdict is the blocking verdict and the report names criterion and group.

**AC-15 — Manual-only criteria never auto-pass (revised per D-8).**
`mode: manual-only`
- *Why not automated:* both the awaiting-human record and the `ci_mode` deferred verdict are `/validate_plan` command behaviors (D-6).
- *Steps:* Run `/validate_plan` with an unresolved manual-only criterion, interactively and again with `ci_mode: true`.
- *Pass/fail:* Pass if both results are non-success and distinguishable from a defect block, and the `ci_mode` run defers without halting; fail if either passes or hard-blocks.
- *Performed by:* repo owner (Dj)
Given a `manual-only` criterion with no recorded human verdict, when `/validate_plan` completes, then its record reads awaiting-human-verdict, the overall result is **not success**, and the reason is distinguishable from an AC-13/AC-14 defect block. Under `ci_mode: true`, the run produces a **deferred verdict** — non-success, distinguishable, **non-halting** — that a human must close.

**AC-16 — Green pipeline cannot mask a skipped criterion (negative).**
`mode: manual-only`
- *Why not automated:* the non-success rule is a `/validate_plan` command behavior; unreachable by script assertion (D-6).
- *Steps:* Make every plan-named check pass while leaving one criterion unbound, then run `/validate_plan`.
- *Pass/fail:* Pass if overall success is not reported; fail if it is.
- *Performed by:* repo owner (Dj)
Given a run where every automated check named by the plan passes but at least one spec criterion is unbound or lacks red evidence, then `/validate_plan` must **not** report overall success. The central regression scenario.

**AC-17 — The pairing gate is reproducible (amended in rev 2).**
`mode: manual-only`
- *Why not automated:* cross-validator reproducibility can only be observed by executing the markdown command more than once (D-6).
- *Steps:* Run the gate twice over identical artifacts, then have a second validator run it, and diff the pairing verdict set and the sampled group identity.
- *Pass/fail:* Pass if both diffs are empty; fail on any difference in verdicts or in which group was sampled.
- *Performed by:* repo owner (Dj), plus one independent validator
Given identical spec, plan, evidence records, and repository state, when the pairing and red→green portion of `/validate_plan` executes twice, or by two independent validators, then those per-criterion verdicts are identical. Under AC-32's sampling, **the sampled group must be selected by a rule that is a function of the artifact set alone**, so two independent validators select the same group. Judgment-based findings elsewhere may differ; the pairing gate may not.

**AC-32 — Sampled re-run; non-re-runnable evidence is absent (new, per D-5).**
`mode: manual-only`
- *Why not automated:* sampling and the absent-evidence rule are `/validate_plan` command behaviors (D-6).
- *Steps:* Run `/validate_plan` three times — re-run agrees with the record; recorded command not re-runnable; re-run contradicts the record.
- *Pass/fail:* Pass if the three outcomes are pass, block, block respectively; fail on any other combination.
- *Performed by:* repo owner (Dj)
Given a validation run, `/validate_plan` re-runs **at least one** bound group using its recorded invocation command, selected per AC-17's deterministic rule. If the recorded command cannot be re-run, or its result contradicts the record, that criterion's evidence is **absent** and AC-14's blocking verdict applies.
*Check:* three seeded cases — re-run agrees, re-run impossible, re-run contradicts — produce pass, block, block.

**AC-18 — The gate reads the spec, not the plan's restatement.**
`mode: manual-only`
- *Why not automated:* source-of-truth selection is a `/validate_plan` command behavior (D-6).
- *Steps:* Delete a criterion's phase reference from the plan, then run `/validate_plan`.
- *Pass/fail:* Pass if the criterion still appears with an unbound/unverified verdict; fail if it disappears from the accounting.
- *Performed by:* repo owner (Dj)
Given a plan whose phase list omits a criterion present in the spec, that criterion still appears in the per-criterion accounting with an unbound/unverified verdict.

### D. Backward compatibility

**AC-19 — Legacy specs do not break the pipeline.**
`mode: manual-only`
- *Why not automated:* legacy classification is a behavior of three markdown commands; unreachable by script assertion (D-6).
- *Steps:* Run `/create_plan`, `/implement_plan`, and `/validate_plan` against a pre-change spec.
- *Pass/fail:* Pass if none errors and each classifies the spec as legacy-unlabeled; fail on any error or on silent normal handling.
- *Performed by:* repo owner (Dj)
Given a pre-change spec (no identifiers, modes, bindings), all three commands proceed without error and classify it legacy-unlabeled. Enforcement keys on the spec's own format, not the run date.

**AC-20 — Legacy is reported as unenforced, never as passed (negative).**
`mode: manual-only`
- *Why not automated:* the wording lives in `/validate_plan`'s generated report (D-6).
- *Steps:* Run `/validate_plan` on a legacy spec and read the gate section of the report.
- *Pass/fail:* Pass if it states the gate was not enforced and why, with no pass-claim; fail if any wording implies the gate passed.
- *Performed by:* repo owner (Dj)
Given a legacy spec, `/validate_plan` states the pairing gate was not enforced and why, and must **not** state or imply the gate passed.

**AC-21 — Upgrade path preserves original intent.**
`mode: manual-only`
- *Why not automated:* the upgrade is a `/spec` command behavior over an arbitrary prior document (D-6).
- *Steps:* Re-invoke `/spec` on a legacy spec and diff original against upgraded criterion text.
- *Pass/fail:* Pass if every change is additive or explicitly listed and mode assignments are listed for review; fail on any silent rewording.
- *Performed by:* repo owner (Dj)
Given a legacy spec, when `/spec` is re-invoked to upgrade it, the result preserves each original criterion's text without silent rewording, adds identifiers and modes, and lists the assignments for human review. (Bindings are added later by `/create_plan`, per D-1.)

### E. Framework constraints and the framework's own CI

**AC-22 — Structural validation passes.**
`mode: automated`

`python3 scripts/validate.py` exits 0 on the changed tree (`validate.py:43-48`, `:153-163`).

**AC-23 — Provider neutrality preserved (negative).**
`mode: manual-only`
- *Why not automated:* a deterministic check exists — `validate.py`'s literal-model-name grep — but it asserts an already-true invariant, so it can never produce failing-first red evidence and binding it would permanently block (plan review-item-1).
- *Steps:* Read the changed command files for literal model names and provider-named conditionals, then compare top-level key sets across the provider manifests.
- *Pass/fail:* Pass if no literal model name or provider-named conditional appears and all manifest key sets are identical; fail otherwise.
- *Performed by:* repo owner (Dj)

No literal model name in changed files; behavior varying by provider goes through a capability flag present in **all** manifests (`conventions/provider-portability.md:42-50`), never provider-named conditionals.

**AC-24 — Routing evals pass; description edits covered.**
`mode: automated`

`python3 scripts/run_evals.py` exits 0; any changed `description` gains ≥1 positive and ≥1 negative case in `evals/cases/`.

**AC-25 — Install path unchanged across providers.**
`mode: manual-only`
- *Why not automated:* the installer smoke test covers this deterministically but asserts an already-true invariant — installs already pass — so no failing-first red evidence is possible and binding it would permanently block (plan review-item-1).
- *Steps:* Run the installer for `claude`, `codex`, and `cursor` against fresh directories and confirm the changed files came from the single neutral source.
- *Pass/fail:* Pass if all three installs succeed with no per-provider fork; fail on any install failure or forked file.
- *Performed by:* repo owner (Dj)

Installer smoke test passes for claude/codex/cursor from the single neutral source.

**AC-26 — Generated skills stay in sync.**
`mode: manual-only`
- *Why not automated:* the skills-drift diff covers this deterministically but asserts an already-true invariant, so no failing-first red evidence exists and binding it would permanently block (plan review-item-1).
- *Steps:* Run the skills build, then diff the curated skills directory, and check whether the change touched the agents directory.
- *Pass/fail:* Pass if the diff is clean and any agents change has its regenerated output committed in the same change; fail otherwise.
- *Performed by:* repo owner (Dj)

`build_skills.py` → clean `git diff --exit-code skills/.curated`.

**AC-27 — Behavioral sections carry the new rules.**
`mode: automated`

Each changed core command's "Common Shortcuts to Avoid" gains ≥1 row naming the likeliest evasion of the gate; "Red Flags" and "Verification" reference the new obligation.

**AC-28 — No duplicated normative text across commands (negative).**
`mode: automated`

No normative gate-defining paragraph appears verbatim in more than one command; shared rules referenced by resolvable relative link.

**AC-29 — File size discipline.**
`mode: automated`

Baselines: `spec.md` 193, `implement_plan.md` 149, `validate_plan.md` 236, `create_plan.md` 549 (already over — must not grow further without extraction) per `three-layer-architecture.md:182-185`.

**AC-33 — Dogfooding mapping is explicit (new, per D-6).**
`mode: manual-only`
- *Why not automated:* the mapping is produced and reported by `/create_plan`; no assertion in the repo's three scripts can reach a generated plan (D-6).
- *Steps:* Read this document's mode lines against the plan's dogfooding table, confirm the split was reported before the plan was declared complete, and inspect the diff for a new test harness.
- *Pass/fail:* Pass if every criterion carries a mode, the split is stated, and no new harness appears in the diff; fail otherwise.
- *Performed by:* repo owner (Dj)
Given this change's own spec, when planned, every criterion gets a mode under AC-2 by this rule: criteria checkable by an assertion in the three scripts are `automated` and bound to that named assertion as their group; **all others — including every criterion describing prompt-following behavior — are `manual-only`**, with AC-4's four elements and AC-5's recorded approval. No new harness. The split is reported to the owner before the plan is declared complete.
*Consequence, stated plainly:* roughly Group E is automated and Groups A–D are manual-only. See OQ-10.

---

## 4. Scope Boundaries

**Explicitly IN**

- Requirement-level changes to `commands/core/spec.md`, `create_plan.md`, `implement_plan.md`, `validate_plan.md`.
- Criterion identity and mode at spec time; test-group binding at plan time; failing-first re-runnable evidence; the blocking gate; sampled re-run.
- Optional single-group invocation config plus degradation behavior (D-4).
- Manual-only treatment, `ci_mode` deferred verdicts, legacy specs.
- Keeping the four CI jobs green; provider-neutral source.

**Explicitly OUT**

- **A shipped deterministic checker** — future-phase candidate per D-2.
- **All syntax and format design** — identifier scheme, label rendering, evidence format/storage, config key name, deterministic sample-rule form: the plan's decisions.
- **New agents** (`AGENTS.md:141-143`).
- **Test-framework selection / per-language runner integration** downstream.
- **Test-quality grading beyond red→green** — no coverage thresholds, no mutation testing, no assertion-strength analysis.
- **Changing criterion prose-quality rules** (`spec.md:148`, `:179`).
- **Automatic batch migration** of existing specs (AC-21 is operator-invoked).
- **DoD restructuring** (`definition-of-done.md:21` must not be contradicted or duplicated).
- **`founder_mode`** (exempt by construction, D-7); **`ticket_oneshot`, `local_review`, `iterate_plan`, `debug`** (D-7 — for `ticket_oneshot` this leaves a verified, currently-open bypass; see OQ-9).
- **Downstream projects' own CI pipelines.**
- **Provider capability expansion.**

---

## 5. Assumptions

| # | Assumption | Status | Evidence / Owner |
|---|---|---|---|
| ASM-1 | `/spec` emits criteria as unlabeled prose, no identifiers/binding. | **Verified** | `spec.md:50-59`. |
| ASM-2 | `create_plan` binds only at phase granularity. | **Verified** | `create_plan.md:547`, `:537`. |
| ASM-3 | `implement_plan` has no per-criterion/failing-first concept. | **Verified** | `implement_plan.md:71-78`, `:144-148`. |
| ASM-4 | `validate_plan` already asks for a per-criterion verdict. | **Verified** | `validate_plan.md:233`, `:224`. |
| ASM-5 | Red→green bar exists project-wide, unenforced, not criterion-scoped. | **Verified** | `definition-of-done.md:21`. |
| ASM-6 | `validate.py` scope as stated. | **Verified** | `validate.py:43-48`, `:89-118`, `:153-163`. |
| ASM-7 | `run_evals.py` indexes only frontmatter name+description; 0.72 threshold. | **Verified** | `run_evals.py:163-181`, `:53`. |
| ASM-8 | `build_skills.py` exports agents only. | **Verified** | `build_skills.py:95` + docstring. |
| ASM-9 | CI = four jobs. | **Verified** | `.github/workflows/validate.yml:9-89`. |
| ASM-10 | Zero `/spec`-produced specs in this repo pre-change. | **Verified** | `thoughts/` listing. |
| ASM-11 | No test framework/`tests/` dir; three scripts only. | **Verified** | Glob empty. |
| ASM-12 | No test-command key in config. | **Verified** | Full read of `specs.config.example.yaml`. |
| ASM-13 | Manifest capabilities: subagents, mcp, tool_frontmatter, model_pinnable — no code execution. | **Verified** | `provider-portability.md:42-47`. |
| ASM-14 | Manifests share top-level keys, checked at install. | **Verified** | `provider-portability.md:50`. |
| ASM-15 | `ci_mode` honored explicitly only by `/commit` today. | **Verified** | `specs.config.example.yaml:68`; `commit.md:15,23,30`. |
| ASM-16 | Downstream projects may hold pre-change specs the owner cannot enumerate. | **Confirmed** | Owner, 2026-08-07. AC-19/20/21 must-have. |
| ASM-17 | Gate holds across all providers (procedural, no execution capability needed this phase). | **Confirmed** | D-2. |
| ASM-18 | "Named automated test" = individually runnable, group granularity. | **Confirmed** | D-3. |
| ASM-19 | `validate_plan` is the blocking point; `create_plan`/`implement_plan` refuse locally. | **Confirmed** | D-1, D-2. |
| ASM-20 | **`ticket_oneshot` never invokes `/validate_plan`** — chains ticket_research → ticket_plan → ticket_impl → describe_pr; no mention of validation, `/spec`, or DoD. | **Verified** | `ticket_oneshot.md:31,:40,:49,:54`; grep for `validate` empty. Contradicts the coordinator rationale for D-7. |
| ASM-21 | `definition-of-done.md:14` registers validate_plan, local_review, ticket_oneshot, founder_mode as applying the checklist, but only validate_plan (`:194`) and local_review (`:341`) reference it. Pre-existing gap. | **Verified** | Repo-wide grep. |
| ASM-22 | An optional config key won't break structural validation (`validate.py` requires only provider+project_name). | **Verified** | `validate.py:50`, `:177-183`. |
| ASM-23 | None of the three scripts supports selective single-check invocation — this repo operates in AC-30's degraded mode unless the plan adds it. | **Verified** | `validate.py:167`; `run_evals.py:276-286`; `build_skills.py:130-131`. |
| ASM-24 | Only Group E maps to script assertions; Groups A–D describe prompt-following behavior no script can reach. | **Verified** | Script docstrings. Drives AC-33, OQ-10. |

---

## 6. Dependencies

| # | Dependency | Status |
|---|---|---|
| DEP-1 | Binding location decision. | **Resolved** — D-1. |
| DEP-2 | "Mechanical" meaning decision. | **Resolved** — D-2. |
| DEP-3 | Single-group invocation path. | **Resolved by default** — D-4 (AC-30, AC-34). |
| DEP-4 | Evidence durability/trust. | **Resolved by default** — D-5 (AC-31, AC-32). |
| DEP-5 | Provider execution-capability reality. | **Deferred** — revisit if the future checker is built. |
| DEP-6 | DoD consistency; any DoD edit is separate/coordinated. | Open, standing. |
| DEP-7 | `evals/cases/*.json` updates if descriptions change. | Open, conditional. |
| DEP-8 | `create_plan.md` over size guideline; additions require extraction. | Open, blocking for plan structure. |
| DEP-9 | `ci_mode` in validate_plan. | **Resolved** — D-8 (first ci_mode behavior for validate_plan, ASM-15). |
| DEP-10 | Deterministic sample-selection rule must be defined for AC-17+AC-32 to co-hold. | **New, blocking for the plan.** |
| DEP-11 | Whether `ticket_oneshot` is remediated separately (ASM-20/21). | **New, non-blocking here; blocking for real-world coverage.** OQ-9. |
| DEP-12 | Modes assigned to this document's own criteria (AC-33) before plan completion. | **New, blocking for the plan.** |

---

## 7. Open Questions

Resolved (retained for traceability): OQ-1→D-1 · OQ-2→D-2 · OQ-3→D-4 · OQ-4→D-5 · OQ-5→D-6 · OQ-6→D-3 · OQ-7→D-7 (rationale corrected; see OQ-9) · OQ-8→D-8 · **OQ-9→accepted 2026-08-07** (owner accepts the out-of-scope bypass for this feature; the Definition-of-Done wiring for `ticket_oneshot`/`founder_mode` is being remediated as a separate, already-started task, which closes the ASM-21 gap; full pairing-gate inheritance for `ticket_oneshot` remains future work) · **OQ-10→D-9** (split accepted) · **OQ-13→D-10** (stakes-based blocking, AC-35).

Remaining — both settled by the plan as it goes; neither blocks starting `/create_plan`:

**OQ-11 — What is the deterministic sample-selection rule?**
Plan's decision (DEP-10), but "sample randomly" is excluded by AC-17 now, so the plan does not rediscover it late.

**OQ-12 — Is one sampled group per validation enough?**
Floor of one re-verifies 5% of evidence on a 20-criterion spec. A proportion, or "one plus every criterion touched since last validation," are the obvious alternatives.

---

**Adversarial self-review notes (revision 2).** Four things changed under attack: (1) AC-32's sampling silently broke AC-17 — fixed by requiring artifact-determined sample selection (DEP-10). (2) D-1 created a new way to violate `spec.md:191` — AC-3b added as an explicit negative. (3) D-6's dogfooding collided with AC-3 injectivity (three scripts cannot supply twenty distinct groups) — AC-33 states the actual mapping rule and its consequence. (4) The coordinator's rationale for scoping out `ticket_oneshot` is contradicted by the file itself — scope retained as directed, rationale corrected with evidence, residual hole carried as OQ-9. One criterion remains deliberately unwritten: "the bound group actually asserts the criterion's behavior rather than something adjacent" is not mechanically checkable — carried by AC-9, AC-32, and the test-quality out-of-scope note rather than softened.
