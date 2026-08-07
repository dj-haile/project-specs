# Executable Acceptance Criteria — Requirements Spec

**Slug:** `executable-acceptance-criteria` · **Target repo:** project-specs · **Date:** 2026-08-07
**Status:** Revision 2 — OQs resolved, ready for `/create_plan`
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
Given a spec produced by `/spec`, when the document is declared complete, then every acceptance criterion carries an identifier unique within that document, and no identifier from a prior revision is ever reassigned to a different criterion (a deleted criterion retires its identifier).
*Check:* parse criteria; assert uniqueness; diff two revisions and assert no identifier changed referent.

**AC-2 — Mode is declared, exactly once.**
Given any acceptance criterion, when the spec is declared complete, then it is labeled with exactly one mode from the closed set {automated, manual-only}. Zero labels, two labels, or an unrecognized label makes the spec incomplete.

**AC-3 — Plan-time one-to-one binding (revised per D-1, D-3).**
Given a criterion labeled `automated`, when `/create_plan` declares the plan complete, then the plan binds that criterion to exactly one **individually runnable named test group** (class, `describe` block, or file), and the criterion→group map is **injective at group level**.
*Check:* build the map from the plan; assert every automated criterion has exactly one group and no group repeats.

**AC-3b — The spec stays solution-neutral (negative, new in rev 2).**
Given a spec produced by `/spec`, when inspected, then it contains no test identifiers, file paths, or framework names for any criterion. Mode labels only.
*Check:* assert no criterion carries a test-name field; the existing `spec.md:191` verification item still passes.

**AC-4 — Manual-only criteria are fully specified.**
Given a criterion labeled `manual-only`, when the spec is declared complete, then it records: (a) why automation is not feasible, (b) exact steps, (c) the observable pass/fail condition, (d) who performs it. Any missing element makes the spec incomplete.

**AC-5 — Manual-only requires recorded human approval (negative).**
Given one or more `manual-only` criteria, when `/spec` finalizes, then it must **not** save the spec as complete until the manual-only set and per-criterion reasons have been presented to a human and approval recorded. Under `ci_mode: true`, it stops and reports rather than self-approving.

**AC-6 — No plan completes with an unbound automated criterion (negative, revised per D-1).**
Given a post-change spec, when `/create_plan` would declare the plan complete while at least one `automated` criterion lacks a test-group binding, then it must **not** declare the plan complete; it reports the unbound criterion identifiers and stops. (Parallel to `spec.md:79`.)

### B. Failing-first evidence

**AC-7 — Red evidence exists (revised per D-3).**
Given an automated criterion and its bound test group, when the work satisfying that criterion is implemented, then a record exists showing that **group failing** against the pre-change code, identifying the group, the code-state reference, and the observed failure.

**AC-8 — Green evidence exists and is distinguishable (revised per D-3).**
Given the same criterion, when implementation completes, then a record exists showing that **group passing**, identifying group and code-state reference, where that reference differs from the red record's.

**AC-9 — A first-run pass is not evidence (negative).**
Given a bound group whose first recorded run against pre-change code **passes**, then that run must **not** satisfy AC-7. Reported as unsatisfied, naming both possible causes: the group does not discriminate the change, or the behavior already exists.

**AC-10 — No completion without red evidence (negative).**
Given an automated criterion with no red record, when `/implement_plan` reaches the plan item bound to it, then it must **not** check that item off, and must report the missing failing-first evidence.

**AC-11 — Red→green does not displace existing checks.**
Given valid red and green evidence for every automated criterion, the pre-existing obligations (full suite passing, no regressions — `definition-of-done.md:19-22`, `implement_plan.md:144-148`) still apply unchanged.

**AC-30 — Single-group invocation, with defined degradation (new, per D-4).**
Given a downstream project with single-group invocation configured, when red or green evidence is produced, then only the bound group is executed and the record reflects that. Given a project without it, evidence may come from a full-suite run **provided the bound group's individual result is identifiable in the captured output**; a full-suite run where it is not identifiable does **not** satisfy AC-7/AC-8.

**AC-31 — Evidence record contents (new, per D-5).**
Given any red or green evidence record, then it contains all three of: exact invocation command, code-state reference, captured result. A record missing any element is treated as absent.

**AC-34 — Degraded evidence is labeled and never counted equal (negative, new, per D-4).**
Given evidence produced via the degraded full-suite path, when `/validate_plan` reports, then that criterion's record is marked degraded with the reason, and the report must **not** present it as equivalent to single-group evidence.

**AC-35 — Degraded evidence blocks on high-stakes criteria (negative, new, per D-10).**
Given a criterion whose subject matter touches a deny-list domain (auth, billing, data integrity, security), when its only evidence is degraded (full-suite path per AC-30), then `/validate_plan` applies the blocking verdict for that criterion, naming the domain match and the missing single-group configuration as the remediation. Deny-list domain identification is recorded in the plan alongside the binding (the plan's decision per D-1), so the gate reads it from artifacts, not judgment (consistent with AC-17).
*Check:* seeded high-stakes criterion with degraded evidence → block; same criterion with single-group evidence → pass; non-deny-list criterion with degraded evidence → labeled, not blocked.

### C. `validate_plan` gate behavior

**AC-12 — Complete per-criterion accounting (revised per D-1).**
Given spec, plan, and implementation, when `/validate_plan` runs, then its report contains exactly one record per acceptance criterion — no omissions, no merges — each carrying: identifier, mode, **bound test group from the plan** (or "none"), red evidence status, green evidence status, evidence strength (single-group or degraded), verdict.

**AC-13 — Block on unbound automated criterion.**
Given any `automated` criterion with no bound test group, when `/validate_plan` completes, then the overall verdict is a distinct **blocking** verdict — not "pass with notes" — and the report names the criterion identifier.

**AC-14 — Block on never-failed group.**
Given any bound group with no red record, or whose red record shows a pass, then the overall verdict is the blocking verdict and the report names criterion and group.

**AC-15 — Manual-only criteria never auto-pass (revised per D-8).**
Given a `manual-only` criterion with no recorded human verdict, when `/validate_plan` completes, then its record reads awaiting-human-verdict, the overall result is **not success**, and the reason is distinguishable from an AC-13/AC-14 defect block. Under `ci_mode: true`, the run produces a **deferred verdict** — non-success, distinguishable, **non-halting** — that a human must close.

**AC-16 — Green pipeline cannot mask a skipped criterion (negative).**
Given a run where every automated check named by the plan passes but at least one spec criterion is unbound or lacks red evidence, then `/validate_plan` must **not** report overall success. The central regression scenario.

**AC-17 — The pairing gate is reproducible (amended in rev 2).**
Given identical spec, plan, evidence records, and repository state, when the pairing and red→green portion of `/validate_plan` executes twice, or by two independent validators, then those per-criterion verdicts are identical. Under AC-32's sampling, **the sampled group must be selected by a rule that is a function of the artifact set alone**, so two independent validators select the same group. Judgment-based findings elsewhere may differ; the pairing gate may not.

**AC-32 — Sampled re-run; non-re-runnable evidence is absent (new, per D-5).**
Given a validation run, `/validate_plan` re-runs **at least one** bound group using its recorded invocation command, selected per AC-17's deterministic rule. If the recorded command cannot be re-run, or its result contradicts the record, that criterion's evidence is **absent** and AC-14's blocking verdict applies.
*Check:* three seeded cases — re-run agrees, re-run impossible, re-run contradicts — produce pass, block, block.

**AC-18 — The gate reads the spec, not the plan's restatement.**
Given a plan whose phase list omits a criterion present in the spec, that criterion still appears in the per-criterion accounting with an unbound/unverified verdict.

### D. Backward compatibility

**AC-19 — Legacy specs do not break the pipeline.**
Given a pre-change spec (no identifiers, modes, bindings), all three commands proceed without error and classify it legacy-unlabeled. Enforcement keys on the spec's own format, not the run date.

**AC-20 — Legacy is reported as unenforced, never as passed (negative).**
Given a legacy spec, `/validate_plan` states the pairing gate was not enforced and why, and must **not** state or imply the gate passed.

**AC-21 — Upgrade path preserves original intent.**
Given a legacy spec, when `/spec` is re-invoked to upgrade it, the result preserves each original criterion's text without silent rewording, adds identifiers and modes, and lists the assignments for human review. (Bindings are added later by `/create_plan`, per D-1.)

### E. Framework constraints and the framework's own CI

**AC-22 — Structural validation passes.** `python3 scripts/validate.py` exits 0 on the changed tree (`validate.py:43-48`, `:153-163`).

**AC-23 — Provider neutrality preserved (negative).** No literal model name in changed files; behavior varying by provider goes through a capability flag present in **all** manifests (`conventions/provider-portability.md:42-50`), never provider-named conditionals.

**AC-24 — Routing evals pass; description edits covered.** `python3 scripts/run_evals.py` exits 0; any changed `description` gains ≥1 positive and ≥1 negative case in `evals/cases/`.

**AC-25 — Install path unchanged across providers.** Installer smoke test passes for claude/codex/cursor from the single neutral source.

**AC-26 — Generated skills stay in sync.** `build_skills.py` → clean `git diff --exit-code skills/.curated`.

**AC-27 — Behavioral sections carry the new rules.** Each changed core command's "Common Shortcuts to Avoid" gains ≥1 row naming the likeliest evasion of the gate; "Red Flags" and "Verification" reference the new obligation.

**AC-28 — No duplicated normative text across commands (negative).** No normative gate-defining paragraph appears verbatim in more than one command; shared rules referenced by resolvable relative link.

**AC-29 — File size discipline.** Baselines: `spec.md` 193, `implement_plan.md` 149, `validate_plan.md` 236, `create_plan.md` 549 (already over — must not grow further without extraction) per `three-layer-architecture.md:182-185`.

**AC-33 — Dogfooding mapping is explicit (new, per D-6).**
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
