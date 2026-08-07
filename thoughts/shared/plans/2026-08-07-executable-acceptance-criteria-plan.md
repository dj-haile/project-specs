---
date: 2026-08-07
branch: feature/executable-acceptance-criteria
status: draft
tags:
  - acceptance-criteria
  - gate
  - dogfooding
---

# Executable Acceptance Criteria — Implementation Plan

**Grades against:** `thoughts/shared/specs/2026-08-07-executable-acceptance-criteria-spec.md`, acceptance criteria AC-1 … AC-35 (36 criteria including AC-3b). Every success criterion below cites the AC/D IDs it satisfies. This plan resolves the design decisions the spec delegated (spec `:212`) and carries **zero open questions**.

---

## Overview

Add a per-criterion pairing gate to the `/spec` → `/create_plan` → `/implement_plan` → `/validate_plan` chain: criteria get stable identifiers and one verification mode at spec time; plans bind each `automated` criterion to exactly one individually runnable named test group; implementations produce re-runnable red→green evidence; `/validate_plan` emits one record per criterion and returns a blocking verdict when a criterion is unbound or its group never failed.

All normative gate text lands in **one** new convention file that the four commands link to. `create_plan.md` shrinks below an enforced ceiling by extraction. The framework dogfoods its own gate against assertions in `scripts/validate.py` and `scripts/run_evals.py`.

---

## Current State Analysis

The chain leaks at three joints and the repo has no mechanism to catch it.

- `/spec` emits criteria as unlabeled given/when/then prose (`commands/core/spec.md:50-59`). No identifier, no mode.
- `/create_plan` requires only that each criterion "maps to at least one phase" (`commands/core/create_plan.md:547`). A phase is a unit of work, not a check.
- `/implement_plan` verifies against the plan's generic build/test commands (`commands/core/implement_plan.md:71-78`); nothing ties a passing suite to a criterion and nothing requires a prior failure.
- `/validate_plan` asks for a per-criterion verdict (`commands/core/validate_plan.md:233`) produced by a model reading prose; its own Red Flags section names the failure mode (`commands/core/validate_plan.md:224`).
- The standing Definition of Done already asserts the correct bar — "tests that fail without the change and pass with it" (`references/definition-of-done.md:21`) — with no per-criterion mechanism, so it is satisfiable by assertion.

Framework constraints in force: four CI jobs (`.github/workflows/validate.yml:9-89`), no new agents (`AGENTS.md:141-143`), provider-neutral single source (`conventions/provider-portability.md:8-21`), commands under ~300 lines (`conventions/three-layer-architecture.md:182-185`).

---

## Desired End State

For any spec produced after this change:

1. Every criterion carries a stable `AC-<n>` identifier and exactly one `mode:` label. The spec names no tests (AC-1, AC-2, AC-3b).
2. The plan carries a `## Criterion Bindings` table mapping every `automated` criterion to exactly one individually runnable named test group, injectively, with its stakes domain (AC-3, AC-6, AC-35).
3. Every automated criterion has red and green evidence records containing the exact invocation command, a re-runnable code-state reference, and the captured result (AC-7, AC-8, AC-31).
4. `/validate_plan` emits one record per spec criterion, re-runs a deterministically selected group, and returns `gate-blocked` on any unbound criterion or missing/passing red record (AC-12 … AC-18, AC-32).
5. Manual-only criteria stay `awaiting-human-verdict`; under `ci_mode: true` they yield `deferred` — non-success, non-halting (AC-15, D-8).
6. Legacy specs are reported `legacy-unenforced`, never `pass` (AC-19, AC-20, AC-21).
7. All four CI jobs green; source stays provider-neutral markdown (AC-22 … AC-29).

**Verification of end state:** `python3 scripts/validate.py` exits 0 with all seven named checks passing; `python3 scripts/run_evals.py` exits 0; `python3 scripts/build_skills.py && git diff --exit-code skills/.curated` clean; installer smoke test green for claude/codex/cursor; `wc -l` on the four core commands within the enforced budget.

### Key Discoveries

- **No repo-wide criterion identifier convention exists.** `conventions/naming-conventions.md:251-282` documents only ticket-ID patterns (`ENG-\d+`); nothing covers requirements or criteria. The `AC-<n>` labels in the spec are that document's own scheme. → the plan defines the scheme; it collides with nothing.
- **`validate.py` has no selective invocation.** `scripts/validate.py:166-210` runs every check from `main()`; there is no way to run one assertion. `scripts/run_evals.py:275-300` and `scripts/build_skills.py:130-131` are the same. This is ASM-23, and it makes AC-3's "individually runnable named test group" unsatisfiable for this repo's own bindings until a selector exists.
- **The AC-29 baselines in the spec are off by one for three files.** Measured with `wc -l`: `spec.md` 192, `create_plan.md` 549, `implement_plan.md` 148, `validate_plan.md` 235. The spec states 193 / 549 / 149 / 236 (`spec:191`). Only `create_plan.md` agrees. → the plan fixes the canonical measurement (`wc -l < file`) and enforces ceilings rather than baselines.
- **No literal model name appears in any command body.** `grep -rniE '(claude-|gpt-|gemini-|opus|sonnet|haiku)' commands/` returns nothing. Every capability flag referenced by a command (`capabilities.subagents` at `create_plan.md:60,115,483`, `spec.md:86`, `validate_plan.md:47,75,80`; `capabilities.mcp` at `conventions/ticket-integration.md:33`) exists in all three manifests (`providers/{claude,codex,cursor}/manifest.yaml`). → AC-23 already holds; no assertion can produce a failing run against it (see Decision 8).
- **`evals/cases/` has no `validate_plan.json`.** Cases exist for `spec`, `create_plan`, `implement_plan` but not `validate_plan`. → a coverage assertion over the four touched core commands fails today, giving AC-24 a genuine red state.
- **A `blocking`/`concern`/`note` severity vocabulary already exists** in `agents/plan-skeptic.md:76-107` and is imported by `commands/core/validate_plan.md:78-86,121-124`. → the gate's verdicts must be named distinctly to avoid collision (Decision 6).
- **`ci_mode` is honored only by `/commit`** (`specs.config.example.yaml:68`; `commands/core/commit.md:15,23,30`). `/validate_plan` gains the framework's second `ci_mode` behavior (DEP-9).
- **`thoughts/shared/` on disk holds `specs/`, `plans/`, `prs/`, `decisions/`.** No evidence or verdict artifacts exist anywhere. Frontmatter shape is documented at `conventions/thoughts-directory.md:88-110`. → new `evidence/` and `validations/` siblings follow the actual layout.
- **The repo has no root `specs.config.yaml`** (only `specs.config.example.yaml`). `scripts/validate.py:177-183` checks the example file for parseability only and `examples/**/specs.config.yaml` for `provider` + `project_name`; a root config is unchecked, so adding one is CI-safe (ASM-22).
- **`build_skills.py` exports `agents/*.md` only** (`scripts/build_skills.py:95` + docstring). This change touches no agent, so the drift check cannot fail before or after (see Decision 8).

---

## What We're NOT Doing

- **No shipped deterministic checker for the gate itself** (spec D-2). `/validate_plan` remains a command procedure. The new Python assertions are the *dogfood test groups*, not a gate implementation.
- **No new agents** (`AGENTS.md:141-143`), no edits to `agents/`.
- **No frontmatter `description` edits** on any command. This keeps DEP-7 closed and makes AC-24's conditional clause vacuous. Any implementer who finds a description edit necessary must stop and escalate.
- **No Definition of Done restructuring.** `references/definition-of-done.md:21` is linked, never restated or contradicted.
- **No changes to criterion prose-quality rules** (`spec.md:148`, `:179`).
- **No batch migration of existing specs.** AC-21's upgrade path is operator-invoked.
- **No changes to `founder_mode`, `ticket_oneshot`, `local_review`, `iterate_plan`, `debug`** (D-7). The verified `ticket_oneshot` bypass (ASM-20, OQ-9) stays open and is remediated elsewhere.
- **No test-framework selection or per-language runner integration.** The config key is a template; downstream projects fill it in.
- **No test-quality grading beyond red→green.** No coverage thresholds, no mutation testing.
- **No renumbering of `create_plan.md`'s Step headings** during extraction — the headings stay, only their bodies move.

---

## Implementation Approach

Two enabling phases, then five capability slices that each cut through the whole command chain, then a close-out.

The gate is a chain property: it only works when all four commands carry their part. So slices are cut by **capability**, not by file — Phase 3 delivers the minimum working gate end to end (a skipped criterion goes red on its own), and Phases 4–8 add evidence, degradation, sampling, manual handling, and legacy behavior on top of a working chain. No phase builds "all of spec.md, then all of create_plan.md."

Phases 1 and 2 come first because they are prerequisites, not because they are a horizontal layer: Phase 1 creates the named, individually runnable test groups without which no binding can exist, and Phase 2 creates the single normative source and the line-budget headroom without which no command edit can land.

**Expected CI state during implementation:** from the end of Phase 1 until Phase 9, `python3 scripts/validate.py` **exits 1** and the `structural` CI job is red on this branch. That failure *is* the red evidence for AC-22/AC-27/AC-28/AC-29. Do not "fix" it early; do not merge before Phase 9.

---

## Settled Design Decisions

These close the spec's delegated items (`spec:212`, OQ-11, OQ-12, D-4, D-5, D-10) and DEP-10/DEP-12. All normative text for them lives in **`conventions/criterion-binding.md`** (created in Phase 2).

### Decision 1 — Identifier scheme and mode-label rendering (AC-1, AC-2, AC-3b)

Identifier: `AC-<n>`, `n` a positive integer assigned in order of first appearance, never reused. A criterion inserted between published identifiers takes a lowercase-letter suffix ascending from `b` — `AC-3b` — so no existing identifier is renumbered. A deleted criterion retires its identifier, recorded on a `Retired identifiers:` line. This matches the source spec's own usage exactly; no migration is needed for it.

Rendering in a spec document — a criterion block is exactly this shape:

```markdown
**AC-7 — Red evidence exists.**
`mode: automated`
Given [precondition] when [action] then [expected result].
```

Parse rule: a block opens on a line matching `^\*\*(AC-\d+[a-z]?) — .+\*\*$`; the next non-blank line must match ``^`mode: (automated|manual-only)`$``. Exactly one mode line per block — zero, two, or an unrecognized value makes the spec incomplete (AC-2).

A `manual-only` block additionally carries all four AC-4 elements as fixed labels, in this order:

```markdown
`mode: manual-only`
- *Why not automated:* …
- *Steps:* …
- *Pass/fail:* …
- *Performed by:* …
```

AC-3b negative: a criterion block may contain the mode line and (for manual-only) the four labeled elements, and nothing else structured. No `group:`, `test:`, or `file:` field; no path-like token (`\S+\.(py|js|ts|tsx|go|rb|java|md)\b`); no test-framework name. `spec.md`'s Verification section carries this as an explicit item so `spec.md:191` still passes.

### Decision 2 — Criterion→test-group binding format in plans (AC-3, AC-6, AC-35)

The plan carries one section, `## Criterion Bindings`, containing exactly one row per `automated` criterion:

| Criterion | Test group | Invocation | Stakes domain | Phase |
|---|---|---|---|---|
| `AC-27` | `scripts/validate.py::check_gate_sections` | `python3 scripts/validate.py --check check_gate_sections` | `none` | 3 |

- **Test group** — `<path>::<name>` for a class / `describe` block / named assertion, or bare `<path>` for a file-level group (D-3). Injectivity is checked on this column: no value may repeat (AC-3). Nesting between a file-level group and a named group inside the same file is permitted and must be declared in the plan.
- **Invocation** — the literal command that runs *exactly* that group. Copied verbatim into evidence records.
- **Stakes domain** — closed vocabulary `none | auth | billing | data-integrity | security` (comma-separated if several). This is D-10/AC-35's record. Assignment is mechanical, not judgment: a criterion's stakes domain is the set of listed domains whose keyword set (enumerated in `conventions/criterion-binding.md`) appears in the criterion's own spec text. `/validate_plan` **reads this column and never re-derives it**, which is what keeps AC-35 inside AC-17's reproducibility guarantee. A bound criterion with a missing stakes value makes the plan incomplete under AC-6.
- **Phase** — the phase whose work satisfies the criterion. Determines which code state the red record is taken against (Decision 7).

`manual-only` criteria never appear in this table. They are listed in `## Manual-Only Criteria` with a pointer to the spec's AC-5 approval record.

### Decision 3 — Evidence record format and storage (AC-31, AC-7, AC-8, D-5)

Storage: `thoughts/shared/evidence/<YYYY-MM-DD>-<plan-slug>.md`, one file per plan, with the standard thoughts frontmatter (`conventions/thoughts-directory.md:88-99`). For this plan: `thoughts/shared/evidence/2026-08-07-executable-acceptance-criteria.md`.

Each record is one fenced `yaml` block. No parser is shipped; the format is fixed so a human or a model reads it identically:

```yaml
criterion: AC-27
group: scripts/validate.py::check_gate_sections
edge: red                     # red | green
command: "python3 scripts/validate.py --check check_gate_sections"
code_state: "git:9f2c1ab7e4d38c05b6119ad2f7e0c4413ab2d9f1"
result: |
  exit 1
  ERROR commands/core/spec.md: 'Common Shortcuts to Avoid' has no row containing 'pairing gate'
strength: single-group        # single-group | degraded
recorded_at: "2026-08-07T14:02:11Z"
```

- **The three AC-31 elements are `command`, `code_state`, `result`.** A record missing any one is treated as absent, which triggers AC-14's blocking verdict.
- **`code_state` must be re-runnable** (D-5). Accepted forms: `git:<40-hex sha>` for a commit, or `git:<40-hex sha>` produced by `git stash create` for an uncommitted state (this yields a real dangling commit reachable with `git checkout`). A working-tree reference such as `git:<sha>-dirty` is **not** re-runnable and makes the record absent under AC-32.
- **`code_state` of the green record must differ from the red record's** (AC-8).
- **`strength` is `single-group` when the invocation executes exactly the bound group and nothing else**, `degraded` when it executes a superset. Granularity is irrelevant: running `scripts/validate.py` for a criterion whose bound group *is* `scripts/validate.py` is `single-group`.
- A `degraded` record additionally requires `degraded_reason:` and its `result` must quote the output lines that individually identify the bound group's outcome. If the group's outcome is not identifiable, the record does not satisfy AC-7/AC-8 (AC-30).

Validation reports get a sibling location, `thoughts/shared/validations/<YYYY-MM-DD>-<plan-slug>.md`, carrying a `validated_at_code_state:` field. Decision 5's floor reads it.

### Decision 4 — Single-group invocation config (D-4, AC-30, AC-34)

Two optional top-level keys in `specs.config.yaml`, documented in `specs.config.example.yaml`:

```yaml
# --- Acceptance-criteria pairing gate ---
# Optional. Command template for running ONE named test group individually.
# Placeholders: {group} = the full group name from the plan's binding table;
# {file} = everything before the last "::"; {name} = everything after it.
# Unset (default) → red/green evidence degrades to full-suite runs (AC-30/AC-34).
test_group_command: ""     # e.g. "pytest -q {file}::{name}" | "npm test -- -t {name}"

# Optional. Used for a file-level group (a group name with no "::"), and as the
# full-suite fallback when test_group_command is unset.
test_suite_command: ""     # e.g. "pytest -q" | "npm test"
```

Template syntax is brace-delimited single-token substitution, matching the framework's existing `{thoughts_path}` convention (`commands/core/spec.md:14`, `create_plan.md:12`). No shell interpolation: the group name is inserted verbatim. Derivation of `{file}`/`{name}` splits on the **last** `::`; if there is none, `{file}` is the whole name, `{name}` is empty, and `test_suite_command` is used.

Degradation semantics: when `test_group_command` is unset and the bound group is not file-level, the evidence record sets `strength: degraded` with `degraded_reason: "test_group_command unset"`. `/validate_plan` then labels the record degraded and must not present it as equivalent to single-group evidence (AC-34). If the criterion's stakes domain is anything other than `none`, degraded evidence produces `gate-blocked`, naming the domain match and "set `test_group_command`" as the remediation (AC-35).

### Decision 5 — Deterministic sample selection and sampling floor (OQ-11, OQ-12, DEP-10, AC-17, AC-32)

**Selection rule — a pure function of the artifact set.** Random selection is excluded by AC-17.

1. Let `S` be the list of bound group names for every `automated` criterion holding **both** a red and a green record, sorted by byte value (`LC_ALL=C` ordering).
2. Let `H = SHA-256( "\n".join(green_code_state[g] for g in S) + "\n" )`, UTF-8 encoded, rendered lowercase hex.
3. Let `i = int(H[0:8], 16) mod len(S)`. The sampled group is `S[i]`.
4. If `len(S) == 0` there is nothing to sample; AC-13/AC-14 already produce the blocking verdict.

Reproducible by hand: `printf '%s\n' <green code_state values, in S order> | shasum -a 256`. Two independent validators reading the same artifacts derive the same `S`, the same `H`, and the same index — AC-17 holds. The hash input is the green code states, so the sample rotates as the code moves rather than pinning one group forever.

**Floor (OQ-12) — one plus every criterion touched since the last validation.** The re-run set is:

> `{ the deterministic sample }` ∪ `{ every bound criterion whose criterion text or bound group changed since the last recorded validation }`

"Last recorded validation" is the newest file in `thoughts/shared/validations/` carrying `validated_at_code_state:`. If none exists, the touched set is **all** bound criteria. Change detection is itself artifact-derived:

```bash
git diff --name-only <validated_at_code_state>..<current> -- <paths in bound group names>
git diff <validated_at_code_state>..<current> -- <spec file>   # criterion blocks that differ
```

Justification: a flat floor of one re-verifies 1/N of the evidence and never prioritizes — on a 20-criterion spec that is 5% coverage chosen without regard to risk. A flat proportion spends the same effort on evidence that provably cannot have gone stale. The touched set targets exactly the records most likely invalidated, and the rotating +1 keeps a nonzero, drifting audit over untouched evidence so the floor can never be zero. Both components are functions of the artifacts, so the whole rule stays inside AC-17.

For this plan specifically: five bound criteria, no prior validation → the first validation re-runs all five.

### Decision 6 — Verdict vocabulary (AC-12 … AC-16, AC-20, AC-34, AC-35)

Named distinctly from the existing `blocking`/`concern`/`note` severities that `/validate_plan` already imports from plan-skeptic (`agents/plan-skeptic.md:76-107`, `validate_plan.md:78-86`), so the two vocabularies never collide.

| Per-criterion verdict | When |
|---|---|
| `pass` | automated; bound; red + green present and well-formed; re-run agreed if sampled |
| `gate-blocked` | unbound automated criterion (AC-13); no red record, or red record shows a pass (AC-14, AC-9); re-run impossible or contradicts (AC-32); degraded evidence on a non-`none` stakes domain (AC-35) |
| `awaiting-human-verdict` | manual-only, no recorded human verdict (AC-15) |
| `deferred` | manual-only under `ci_mode: true` — non-success, non-halting, distinguishable from `gate-blocked` (AC-15, D-8) |
| `manual-pass` / `manual-fail` | a human recorded a verdict |
| `legacy-unenforced` | legacy spec; gate not enforced, reason stated (AC-19, AC-20) |

Overall run result: `success` only if every criterion is `pass` or `manual-pass`. Any `gate-blocked` → `blocked`. Otherwise → `incomplete` (non-success, non-blocking). This is what makes AC-16 hold: a fully green automated pipeline cannot produce `success` while any criterion is unbound or unevidenced.

### Decision 7 — "Pre-change code" for red evidence (AC-7, AC-9)

AC-7 requires the group to fail "against the pre-change code." Pre-change code means **the code state immediately before the specific change that satisfies that criterion**, identified by the `Phase` column of the binding table — not the branch point. This is the only reading under which a criterion satisfied in Phase 6 can have red evidence at all, and it is what makes the red record discriminating rather than incidental.

### Decision 8 — Criteria whose check cannot discriminate this change (AC-9, AC-14 vs AC-33)

**This is the load-bearing dogfooding decision and it needs the owner's eye (Review item 1).**

AC-33 assigns `automated` to any criterion an assertion in the three scripts can check. AC-9 says a group that passes on first contact is not evidence, and AC-14 turns a bound group with no red record into a blocking verdict. Applied together to invariant-preservation criteria — ones asserting that something already true stays true — the two rules conflict: the assertion passes before the change by construction, so the criterion can never obtain red evidence, so binding it guarantees a permanent block.

Ruling: **AC-33 assigns mode; AC-9 governs evidence validity. A criterion whose only available check cannot fail against the relevant pre-change state falls under AC-9's stated second cause — "the behavior already exists" — and is therefore labeled `manual-only` under AC-4/AC-5 rather than bound to a group it can never redden.** The existing CI check is recorded in the plan as a *supporting check*, explicitly not a binding, so nothing is lost operationally.

Applied here, this affects exactly three criteria (AC-23, AC-25, AC-26) — see the split below and Review item 1 for the alternative.

---

## Dogfooding: mode assignment for AC-1 … AC-35 (D-6, AC-33, DEP-12)

Rule applied, per D-6 and AC-33: `automated` only if a **named assertion in `scripts/validate.py`, `scripts/run_evals.py`, or the `build_skills.py` drift check** can check the criterion as stated **and** can produce a failing run against the relevant pre-change state (Decision 8). Everything else is `manual-only` with all four AC-4 elements and AC-5 approval. No new harness — the four new assertions live inside two existing scripts.

### Split: 5 automated · 31 manual-only · 36 total

**Automated (5) — bindings are injective at group level (AC-3), and none is unbound (AC-6):**

| Criterion | Test group | Invocation | Stakes | Phase |
|---|---|---|---|---|
| `AC-22` | `scripts/validate.py` | `python3 scripts/validate.py` | `none` | 9 |
| `AC-24` | `scripts/run_evals.py::check_core_command_coverage` | `python3 scripts/run_evals.py --check check_core_command_coverage` | `none` | 9 |
| `AC-27` | `scripts/validate.py::check_gate_sections` | `python3 scripts/validate.py --check check_gate_sections` | `none` | 3–8 |
| `AC-28` | `scripts/validate.py::check_gate_single_source` | `python3 scripts/validate.py --check check_gate_single_source` | `none` | 2 |
| `AC-29` | `scripts/validate.py::check_command_size_budget` | `python3 scripts/validate.py --check check_command_size_budget` | `none` | 2 |

Five distinct group names, no repeats — injectivity holds. `scripts/validate.py` (AC-22) is deliberately a **superset** of the three named checks inside it; this nesting is declared here rather than hidden. No criterion touches a deny-list domain, so AC-35 never fires for this plan's own bindings.

Red state for each, per Decision 7:
- `AC-27` — red on the pre-change tree: the token `pairing gate` appears in no command's Common Shortcuts / Red Flags / Verification section.
- `AC-28` — red on the pre-change tree: `conventions/criterion-binding.md` does not exist and no command links to it.
- `AC-29` — red on the pre-change tree: `create_plan.md` is 549 lines against an enforced ceiling of 500.
- `AC-24` — red on the pre-change tree: `evals/cases/validate_plan.json` does not exist.
- `AC-22` — red on the pre-change tree once Phase 1 lands: `validate.py` exits 1 because the three checks above fail.

**Manual-only (31)** — each gets AC-4's four elements in the spec and AC-5 recorded approval:

| Group | Criteria | Why no script assertion reaches them |
|---|---|---|
| A. Spec-time labeling | AC-1, AC-2, AC-3, AC-3b, AC-4, AC-5, AC-6 | Prompt-following behavior of `/spec` and `/create_plan`. The scripts read frontmatter and structure, not command behavior at runtime (ASM-24). |
| B. Failing-first evidence | AC-7, AC-8, AC-9, AC-10, AC-11, AC-30, AC-31, AC-34, AC-35 | Same — plus evidence records are produced by `/implement_plan` at runtime; no script observes them. |
| C. Gate behavior | AC-12, AC-13, AC-14, AC-15, AC-16, AC-17, AC-18, AC-32 | Runtime behavior of `/validate_plan`. |
| D. Backward compatibility | AC-19, AC-20, AC-21 | Runtime behavior across three commands against a legacy artifact. |
| E. Framework constraints | AC-23, AC-25, AC-26, AC-33 | See below. |

The four Group-E manual-only criteria, each with its supporting (non-binding) check:
- **AC-23** — provider neutrality. Verified as already holding (no literal model name in any command body; every referenced capability flag present in all three manifests). Non-discriminating per Decision 8. Supporting check: `scripts/validate.py:101-103` (`LITERAL_MODEL_PAT` on frontmatter), which is inside AC-22's group.
- **AC-25** — installer smoke test. The `install-smoke-test` CI job is not one of D-6's three enumerated sources, and it also cannot fail before the change. Supporting check: `.github/workflows/validate.yml:59-89`.
- **AC-26** — generated-skills drift. This change touches no file under `agents/`, and `build_skills.py` exports agents only (`scripts/build_skills.py:95`), so the drift check cannot fail before or after. Non-discriminating. Supporting check: `.github/workflows/validate.yml:38-52`.
- **AC-33** — this mapping being reported to the owner is an event, not a file property.

**Delta from the spec's estimate.** D-9 anticipated "~8 automated / ~21 manual-only." The actual totals are **5 / 31** over 36 criteria. Two sources of difference: the "~21" undercounts Groups A–D, which contain 27 criteria; and Decision 8 moves AC-23, AC-25, AC-26 out of the automated set. Review item 1 states the alternative reading and its cost.

---

## Program Design

### Command-chain diff

```
/spec
+ → assign AC-<n> + `mode:` per criterion            (Decision 1)
+ → require AC-4 four elements for manual-only
+ → record AC-5 human approval; stop under ci_mode
+ → upgrade path for legacy specs                    (AC-21)
/create_plan
+ → emit `## Criterion Bindings` (injective + stakes) (Decision 2)
+ → refuse completion on unbound automated criterion  (AC-6)
- →   [Step 4 body: Program Design]  → conventions/program-design.md
- →   [Sub-task Spawning body]       → conventions/subagent-fallback.md
/implement_plan
+ → record red before the satisfying change           (AC-7, Decision 7)
+ → record green after                                (AC-8)
+ → refuse to check off an item with no red record    (AC-10)
+ → mark strength / degraded_reason                   (AC-30, AC-34)
/validate_plan
+ → per-criterion accounting, sourced from the SPEC   (AC-12, AC-18)
+ → verdict vocabulary + overall result rule          (Decision 6)
+ → deterministic sample + touched set, then re-run   (Decision 5, AC-32)
+ → ci_mode deferred verdicts                         (AC-15)
+ → legacy-unenforced path                            (AC-19, AC-20)
```

### File-tree diff

```
commands/core/
~ spec.md                          192 → ~234   (ceiling 300)
~ create_plan.md                   549 → ~489   (ceiling 500; net −60 via extraction)
~ implement_plan.md                148 → ~182   (ceiling 300)
~ validate_plan.md                 235 → ~287   (ceiling 300)
conventions/
+ criterion-binding.md             new, ~230    single normative source (AC-28)
+ program-design.md                new, ~55     extracted from create_plan.md
~ subagent-fallback.md             46 → ~80     receives Sub-task Spawning body
scripts/
~ validate.py                      + --check/--list-checks, + 3 named assertions
~ run_evals.py                     + --check/--list-checks, + 1 named assertion
evals/cases/
+ validate_plan.json               new          ≥1 positive, ≥1 negative
+ specs.config.yaml                new          root config; enables single-group invocation
~ specs.config.example.yaml        + test_group_command, test_suite_command
thoughts/shared/
+ evidence/2026-08-07-executable-acceptance-criteria.md
+ validations/                     (created by the first /validate_plan run)
```

### Key formats and signatures

```python
# scripts/validate.py — registry keyed by the group name used in bindings
CHECKS: dict[str, Callable[[], None]] = {
    "check_agent_or_command":     _run_agent_or_command,   # existing, wrapped
    "check_yaml_configs":         _run_yaml_configs,       # existing, wrapped
    "check_skills":               _run_skills,             # existing, wrapped
    "check_links":                _run_links,              # existing, wrapped
    "check_gate_sections":        check_gate_sections,     # new  → AC-27
    "check_gate_single_source":   check_gate_single_source,# new  → AC-28
    "check_command_size_budget":  check_command_size_budget,# new → AC-29
}
# CLI: --list-checks prints names one per line, exit 0.
#      --check <name> runs exactly one, exit 0/1.
#      no flag  → runs all in registry order (unchanged CI behavior, AC-22).

GATE_TOKEN = "pairing gate"          # AC-27's canonical marker
GATE_SECTIONS = ("Common Shortcuts to Avoid", "Red Flags", "Verification")
GATE_SOURCE = "conventions/criterion-binding.md"   # AC-28's single source
SIZE_BUDGET = {                       # AC-29, measured as `wc -l`
    "commands/core/spec.md": 300,
    "commands/core/create_plan.md": 500,
    "commands/core/implement_plan.md": 300,
    "commands/core/validate_plan.md": 300,
}
DUP_MIN_WORDS = 25                    # AC-28 verbatim-paragraph threshold

# scripts/run_evals.py
CHECKS = {
    "check_cases":                 run_cases,                    # existing, wrapped
    "check_collisions":            check_collisions,             # existing, wrapped
    "check_core_command_coverage": check_core_command_coverage,  # new → AC-24
}
CORE_ROUTED = {"spec", "create_plan", "implement_plan", "validate_plan"}
```

```python
def check_gate_sections() -> None:
    """AC-27. For each of the four core commands, GATE_TOKEN must appear at
    least once inside each of GATE_SECTIONS."""

def check_gate_single_source() -> None:
    """AC-28. GATE_SOURCE must exist; each core command must carry a resolvable
    relative link to it; no paragraph of >= DUP_MIN_WORDS words may appear
    byte-identically in more than one file of {commands/core/*.md} U {GATE_SOURCE}."""

def check_command_size_budget() -> None:
    """AC-29. For each path in SIZE_BUDGET, line count (wc -l) <= budget."""

def check_core_command_coverage() -> None:
    """AC-24. Each name in CORE_ROUTED must have evals/cases/<name>.json with
    at least one positive and at least one negative case."""
```

---

## Phase 1 — Named, individually runnable test groups (tracer bullet for the gate mechanism)

### Overview

Create the five test groups the bindings depend on, and prove the mechanism end to end by observing four of them go red on the untouched tree. Nothing about the gate's prose exists yet; this phase demonstrates that a criterion's check can fail on its own.

### Changes Required

**1. `scripts/validate.py`** — wrap the four existing check bodies as named entries, add the `CHECKS` registry, `--list-checks`, and `--check <name>`; add `check_gate_sections`, `check_gate_single_source`, `check_command_size_budget` with the constants above. `main()` with no flag runs everything in registry order, so the `structural` CI job's command is unchanged (AC-22).

**2. `scripts/run_evals.py`** — same registry/`--check`/`--list-checks` treatment; add `check_core_command_coverage` over `CORE_ROUTED`.

**3. `thoughts/shared/evidence/2026-08-07-executable-acceptance-criteria.md`** — create with frontmatter per `conventions/thoughts-directory.md:88-99`; record the **red** entries for AC-22, AC-24, AC-27, AC-28, AC-29 in the Decision 3 format. Take the `code_state` from `git stash create` or from the Phase 1 commit so every record is re-runnable (AC-31, AC-32).

### Success Criteria

#### Automated Verification
- [ ] `python3 scripts/validate.py --list-checks` prints exactly the seven registry names, exit 0
- [ ] `python3 scripts/run_evals.py --list-checks` prints exactly the three registry names, exit 0
- [ ] `python3 scripts/validate.py --check check_gate_sections` exits **1** — red for AC-27
- [ ] `python3 scripts/validate.py --check check_gate_single_source` exits **1** — red for AC-28
- [ ] `python3 scripts/validate.py --check check_command_size_budget` exits **1** (create_plan.md 549 > 500) — red for AC-29
- [ ] `python3 scripts/run_evals.py --check check_core_command_coverage` exits **1** (no `validate_plan.json`) — red for AC-24
- [ ] `python3 scripts/validate.py` exits **1** — red for AC-22
- [ ] `python3 scripts/validate.py --check check_agent_or_command`, `--check check_yaml_configs`, `--check check_skills`, `--check check_links` each exit **0** — the refactor changed no existing behavior
- [ ] `python3 scripts/run_evals.py --check check_cases` and `--check check_collisions` each exit 0
- [ ] `python3 scripts/build_skills.py && git diff --exit-code skills/.curated` — clean

#### Manual Verification
- [ ] Owner confirms the five red records each carry all three AC-31 elements and a `code_state` that `git checkout` can reach (AC-31, D-5)
- [ ] Owner confirms the intentional red CI state on this branch is expected and the PR must not merge before Phase 9
- [ ] Owner reviews the split in "Dogfooding" above and rules on Review item 1 (AC-33, D-6)

**Implementation Note**: pause for the owner's confirmation of the split before Phase 2.

---

## Phase 2 — Single normative source and line-budget headroom

### Overview

Create the one file every command will link to, and free enough lines in `create_plan.md` to add the gate obligations without breaching AC-29. Turns AC-29 green and moves AC-28 from "source missing" to "links pending."

### Changes Required

**1. `conventions/criterion-binding.md`** (new, ~230 lines) — the single normative source. Contents: Decisions 1–7 verbatim as the framework's rule set; the stakes-domain keyword table for D-10; the sample-selection procedure with its `shasum` reproduction; the evidence-record schema. It **links** to `../references/definition-of-done.md` for the failing-first bar rather than restating it (DoD restructuring is out of scope; `definition-of-done.md:21` must not be duplicated).

**2. `conventions/program-design.md`** (new, ~55 lines) — receives the body of `create_plan.md:176-225` unchanged.

**3. `conventions/subagent-fallback.md`** — append the body of `create_plan.md:481-513` under a new `## Sub-task Spawning Best Practices` heading.

**4. `commands/core/create_plan.md`** — replace the body of Step 4 (`:176-225`) with a 5-line pointer, keeping the `### Step 4: Program Design` heading so no step is renumbered; replace the body of `## Sub-task Spawning Best Practices` (`:481-513`) with a 4-line pointer; delete `## Example Interaction Flow` (`:515-529`). Net ≈ −89 lines → ≈ 460.

### Success Criteria

#### Automated Verification
- [ ] `python3 scripts/validate.py --check check_command_size_budget` exits **0** — green for AC-29
- [ ] `python3 scripts/validate.py --check check_links` exits 0 — the two new relative links resolve
- [ ] `wc -l < commands/core/create_plan.md` ≤ 460
- [ ] `python3 scripts/validate.py --check check_agent_or_command` exits 0 — Common Shortcuts / Red Flags / Verification still present in all four core commands (`scripts/validate.py:43-48`)
- [ ] `python3 scripts/validate.py --check check_gate_single_source` still exits 1 — links pending, expected
- [ ] `python3 scripts/build_skills.py && git diff --exit-code skills/.curated` — clean

#### Manual Verification
- [ ] Owner confirms the extracted Program Design and Sub-task Spawning text reads correctly in its new home and that `create_plan.md`'s pointers are unambiguous
- [ ] Owner confirms `conventions/criterion-binding.md` states each rule exactly once and links to the DoD rather than restating it (AC-28, scope fence)
- [ ] Owner records the **green** evidence entry for AC-29 (AC-8)

---

## Phase 3 — Identity, mode, binding, and the block (minimum working gate)

**Covers:** AC-1, AC-2, AC-3, AC-3b, AC-6, AC-12, AC-13, AC-16, AC-18.

### Overview

The tracer bullet through the whole chain. After this phase, a criterion that gets skipped goes red on its own: the spec labels it, the plan must bind it, and validation blocks when it is unbound. Evidence, degradation, sampling, manual handling, and legacy behavior are added on top in later phases.

### Changes Required

**1. `commands/core/spec.md`** (+~18) — in "Output Artifact §3 Acceptance Criteria", require the Decision 1 identifier and mode-line shape and the AC-3b negative; add one "Common Shortcuts to Avoid" row containing the token `pairing gate`; add one Red Flag and two Verification items using the same token; link to `../../conventions/criterion-binding.md`.

**2. `commands/core/create_plan.md`** (+~18) — require the `## Criterion Bindings` section (Decision 2) with injectivity and the stakes column; state the AC-6 refusal (report unbound identifiers and stop, parallel to `spec.md:79`); add the section to the plan template; one Common Shortcuts row, one Red Flag, two Verification items, all carrying `pairing gate`; link to the convention.

**3. `commands/core/implement_plan.md`** (+~8) — an item bound to an unbound criterion cannot be checked off; one Common Shortcuts row, one Red Flag, one Verification item with the token; link.

**4. `commands/core/validate_plan.md`** (+~16) — the per-criterion accounting table of Decision 6, sourced from the **spec's** criterion list, not the plan's restatement (AC-18); `gate-blocked` on unbound (AC-13); the overall-result rule that makes a green pipeline unable to report success while a criterion is unbound (AC-16); one Common Shortcuts row, one Red Flag, two Verification items with the token; link.

### Success Criteria

#### Automated Verification
- [ ] `python3 scripts/validate.py --check check_gate_sections` exits **0** — green for AC-27
- [ ] `python3 scripts/validate.py --check check_gate_single_source` exits **0** — green for AC-28 (source exists, all four commands link to it, no ≥25-word paragraph repeated)
- [ ] `python3 scripts/validate.py --check check_command_size_budget` exits 0 — all four within budget
- [ ] `python3 scripts/validate.py` exits **0** — green for AC-22
- [ ] `python3 scripts/run_evals.py --check check_collisions` exits 0 — no description drifted (no description was edited)
- [ ] `python3 scripts/build_skills.py && git diff --exit-code skills/.curated` — clean

#### Manual Verification
- [ ] Owner runs `/spec` on a small throwaway requirement and confirms every criterion emerges with a unique `AC-<n>` and exactly one mode line, and that no test name, path, or framework appears anywhere in it (AC-1, AC-2, AC-3b)
- [ ] Owner runs `/create_plan` against that spec and confirms it produces `## Criterion Bindings` with one group per automated criterion, no group repeated, and a stakes value on every row (AC-3)
- [ ] Owner deletes one binding row and confirms `/create_plan` refuses to declare the plan complete and names the unbound identifier (AC-6)
- [ ] Owner runs `/validate_plan` against that state and confirms `gate-blocked`, not "pass with notes", and that the report contains exactly one record per spec criterion with no merges (AC-12, AC-13)
- [ ] Owner adds a criterion to the spec but not the plan and confirms it still appears in the accounting as unbound (AC-18)
- [ ] Owner confirms that with every plan-named automated check passing, one unbound criterion still prevents overall success (AC-16)
- [ ] Owner records green evidence for AC-27, AC-28, AC-22

**Implementation Note**: pause for manual confirmation before Phase 4.

---

## Phase 4 — Failing-first evidence

**Covers:** AC-7, AC-8, AC-9, AC-10, AC-11, AC-14, AC-31.

### Changes Required

**1. `commands/core/create_plan.md`** (+~6) — the plan declares the evidence file path (Decision 3) so `/implement_plan` and `/validate_plan` read from one place.

**2. `commands/core/implement_plan.md`** (+~18) — before making the change that satisfies an automated criterion, run its bound group and record the red entry; after, record green with a differing `code_state`; a record missing any of the three AC-31 elements is absent; a first-run pass is **not** red evidence and must be reported naming both AC-9 causes; do not check off a plan item whose criterion lacks a red record (AC-10); state that the pre-existing obligations at `references/definition-of-done.md:19-22` and `implement_plan.md:144-148` still apply unchanged, by link, not restatement (AC-11).

**3. `commands/core/validate_plan.md`** (+~8) — `gate-blocked` when a bound group has no red record or its red record shows a pass (AC-14).

### Success Criteria

#### Automated Verification
- [ ] `python3 scripts/validate.py` exits 0
- [ ] `python3 scripts/validate.py --check check_command_size_budget` exits 0 — `implement_plan.md` ≤ 300, `create_plan.md` ≤ 500
- [ ] `python3 scripts/validate.py --check check_gate_single_source` exits 0 — the AC-11 obligation was linked, not copied
- [ ] `python3 scripts/run_evals.py` exits 0
- [ ] `python3 scripts/build_skills.py && git diff --exit-code skills/.curated` — clean

#### Manual Verification
- [ ] Owner confirms a red and a green record for one criterion, with differing `code_state` values, and re-runs the red record's exact command against its `code_state` and observes the recorded failure (AC-7, AC-8, AC-31, D-5)
- [ ] Owner seeds a group that passes on first contact and confirms `/implement_plan` reports it unsatisfied naming both causes — the group does not discriminate, or the behavior already exists (AC-9)
- [ ] Owner confirms `/implement_plan` refuses to check off an item whose criterion has no red record and names the missing evidence (AC-10)
- [ ] Owner strips one of the three elements from a record and confirms `/validate_plan` treats it as absent and returns `gate-blocked` (AC-31, AC-14)
- [ ] Owner confirms the full-suite and no-regression obligations are unchanged and referenced by link (AC-11)

**Implementation Note**: pause for manual confirmation before Phase 5.

---

## Phase 5 — Evidence strength: single-group config, degradation, stakes blocking

**Covers:** AC-30, AC-34, AC-35, D-4, D-10.

### Changes Required

**1. `specs.config.example.yaml`** — add the `test_group_command` / `test_suite_command` block of Decision 4, commented with defaults of `""`.

**2. `specs.config.yaml`** (new, repo root) — minimum keys so this repo's own dogfood evidence is `single-group` rather than degraded:

```yaml
provider: "claude"
project_name: "project-specs"
project_description: "Spec-driven development framework for coding agents"
thoughts_directory: true
thoughts_path: "thoughts/shared"
ci_mode: false
test_group_command: "python3 {file} --check {name}"
test_suite_command: "python3 {file}"
```

Safe for CI: `scripts/validate.py:177-183` checks `specs.config.example.yaml` for parseability only and requires `provider` + `project_name` on `examples/**/specs.config.yaml`; a root config is unchecked (ASM-22). **Fallback, pre-authorized:** if the owner declines this file (Review item 3), skip it — every binding's `strength` becomes `degraded` with `degraded_reason: "test_group_command unset"`, all five are labeled per AC-34, and none blocks because every stakes value is `none`.

**3. `commands/core/create_plan.md`** (+~5) — the stakes-domain column semantics and its closed vocabulary, by link to the convention's keyword table.

**4. `commands/core/implement_plan.md`** (+~8) — set `strength` on every record; a degraded record requires `degraded_reason` and a `result` in which the bound group's individual outcome is identifiable, else the record does not satisfy AC-7/AC-8 (AC-30).

**5. `commands/core/validate_plan.md`** (+~8) — label degraded records with their reason and never present them as equivalent to single-group evidence (AC-34); apply `gate-blocked` when degraded evidence backs a criterion whose stakes value is not `none`, naming the domain match and the missing `test_group_command` as the remediation (AC-35). The stakes value is **read from the plan's column**, never re-derived, which keeps AC-35 inside AC-17.

### Success Criteria

#### Automated Verification
- [ ] `python3 -c "import yaml,sys; yaml.safe_load(open('specs.config.yaml'))"` exits 0
- [ ] `python3 scripts/validate.py` exits 0 — the new root config does not disturb structural validation
- [ ] `python3 scripts/validate.py --check check_yaml_configs` exits 0
- [ ] `python3 scripts/validate.py --check check_command_size_budget` exits 0
- [ ] `python3 scripts/run_evals.py` exits 0
- [ ] `bash setup.sh /tmp/ps-smoke-claude --provider=claude --copy --yes` succeeds and `/tmp/ps-smoke-claude/specs.config.yaml` exists — installer unaffected by the new root config
- [ ] `python3 scripts/build_skills.py && git diff --exit-code skills/.curated` — clean

#### Manual Verification
- [ ] Owner confirms substitution: `{file}`/`{name}` split on the last `::`, `{group}` is the whole name, and a group with no `::` uses `test_suite_command` (D-4)
- [ ] Owner seeds a criterion with stakes `auth` backed by degraded evidence and confirms `gate-blocked` naming the domain and the remediation; the same criterion with single-group evidence passes; a `none`-stakes criterion with degraded evidence is labeled but not blocked (AC-35's three seeded cases)
- [ ] Owner confirms a degraded record whose captured output does not individually identify the bound group is rejected outright, not merely labeled (AC-30)
- [ ] Owner confirms the report never presents a degraded record as equivalent to single-group evidence (AC-34)

**Implementation Note**: pause for manual confirmation before Phase 6.

---

## Phase 6 — Sampled re-run and reproducibility

**Covers:** AC-17, AC-32, OQ-11, OQ-12, DEP-10.

### Changes Required

**1. `commands/core/validate_plan.md`** (+~8) — add the re-run step: derive the re-run set per Decision 5 (deterministic sample ∪ touched set), execute each record's stored `command` against its stored `code_state`, and compare with the stored `result`. A command that cannot be re-run, or whose result contradicts the record, makes that criterion's evidence **absent** and AC-14's `gate-blocked` applies. State that the pairing and red→green portion of the report must be identical across two runs or two validators; judgment-based findings elsewhere may differ (AC-17). The rule itself lives in `conventions/criterion-binding.md`; the command links to it.

**2. `thoughts/shared/validations/`** — created on first use; each report carries `validated_at_code_state:` so Decision 5's touched set is computable.

### Success Criteria

#### Automated Verification
- [ ] `python3 scripts/validate.py` exits 0
- [ ] `python3 scripts/validate.py --check check_command_size_budget` exits 0 — `validate_plan.md` ≤ 300 (contingency below if breached)
- [ ] `python3 scripts/validate.py --check check_gate_single_source` exits 0 — the sample rule appears in the convention only
- [ ] `python3 scripts/run_evals.py` exits 0
- [ ] `python3 scripts/build_skills.py && git diff --exit-code skills/.curated` — clean

#### Manual Verification
- [ ] Owner computes the sample by hand with `printf '%s\n' <green code_states in LC_ALL=C group order> | shasum -a 256` and confirms `/validate_plan` selected the same group (AC-17, OQ-11)
- [ ] Owner runs `/validate_plan` twice on an unchanged tree and confirms the pairing and red→green verdicts are byte-identical (AC-17)
- [ ] Owner exercises AC-32's three seeded cases — re-run agrees → pass; re-run impossible → `gate-blocked`; re-run contradicts → `gate-blocked`
- [ ] Owner confirms the touched-set floor: with no prior validation the re-run set is every bound criterion; with a prior validation it is the sample plus every criterion whose text or group changed (OQ-12)

**Contingency (pre-authorized):** if `validate_plan.md` exceeds 300 lines, extract its "Validation Report" markdown template (`validate_plan.md:117-163`, 47 lines) to `references/validation-report-template.md` and link to it. Do not shorten the normative text to fit.

---

## Phase 7 — Manual-only lifecycle and `ci_mode` deferred verdicts

**Covers:** AC-4, AC-5, AC-15, D-8, DEP-9.

### Changes Required

**1. `commands/core/spec.md`** (+~16) — a `manual-only` criterion must record all four AC-4 elements in the fixed labels of Decision 1; any missing element makes the spec incomplete. Before saving as complete, present the manual-only set with per-criterion reasons to a human and record approval in a `## Manual-Only Approval` section (`approved_by:`, `approved_at:`, the identifier list). Under `ci_mode: true`, stop and report rather than self-approving (AC-5). Add one Red Flag and one Verification item.

**2. `commands/core/validate_plan.md`** (+~6) — a manual-only criterion with no recorded human verdict reads `awaiting-human-verdict` and the overall result is not success, distinguishable from an AC-13/AC-14 defect block. Under `ci_mode: true` the same criterion yields `deferred` — non-success, distinguishable, **non-halting** — that a human must close (AC-15, D-8). This is `/validate_plan`'s first `ci_mode` behavior (ASM-15).

### Success Criteria

#### Automated Verification
- [ ] `python3 scripts/validate.py` exits 0
- [ ] `python3 scripts/validate.py --check check_command_size_budget` exits 0 — `spec.md` ≤ 300
- [ ] `python3 scripts/validate.py --check check_gate_sections` exits 0
- [ ] `python3 scripts/run_evals.py` exits 0
- [ ] `grep -c 'ci_mode' commands/core/validate_plan.md` ≥ 1
- [ ] `python3 scripts/build_skills.py && git diff --exit-code skills/.curated` — clean

#### Manual Verification
- [ ] Owner confirms `/spec` refuses to save a spec with a manual-only criterion missing any of the four elements (AC-4)
- [ ] Owner confirms `/spec` presents the manual-only set for approval and records it, and that under `ci_mode: true` it stops rather than self-approving (AC-5)
- [ ] Owner confirms an unresolved manual-only criterion produces `awaiting-human-verdict`, a non-success overall result, and a reason visibly different from `gate-blocked` (AC-15)
- [ ] Owner confirms that under `ci_mode: true` the same criterion produces `deferred` and the run does **not** halt (D-8)

**Implementation Note**: pause for manual confirmation before Phase 8.

---

## Phase 8 — Legacy specs

**Covers:** AC-19, AC-20, AC-21, ASM-16.

### Changes Required

**1. `commands/core/spec.md`** (+~8) — the AC-21 upgrade path: re-invoking `/spec` on a legacy spec preserves each original criterion's text without silent rewording (the diff may only insert the identifier heading and the mode line), adds identifiers and modes, and lists the assignments for human review. Bindings are added later by `/create_plan` (D-1).

**2. `commands/core/create_plan.md` and `commands/core/implement_plan.md`** — no new lines; the legacy classification is defined once in the convention and both already link to it.

**3. `commands/core/validate_plan.md`** (+~6) — classification keys on the spec's **own format**, never the run date: a spec containing zero lines matching the mode-line regex is `legacy-unlabeled` (AC-19). All three commands proceed without error. The report states the pairing gate was not enforced and why, and must never state or imply that it passed (AC-20). Verdict: `legacy-unenforced`.

### Success Criteria

#### Automated Verification
- [ ] `python3 scripts/validate.py` exits 0
- [ ] `python3 scripts/validate.py --check check_command_size_budget` exits 0 — all four within budget
- [ ] `python3 scripts/validate.py --check check_gate_single_source` exits 0 — the legacy rule is defined once
- [ ] `python3 scripts/run_evals.py` exits 0
- [ ] `python3 scripts/build_skills.py && git diff --exit-code skills/.curated` — clean

#### Manual Verification
- [ ] Owner runs all three commands against a pre-change spec and confirms none errors and all classify it `legacy-unlabeled` (AC-19)
- [ ] Owner confirms classification is driven by the spec's format, not by a date (AC-19)
- [ ] Owner confirms the report says the gate was not enforced and why, and nowhere implies it passed (AC-20)
- [ ] Owner runs the upgrade and diffs the result, confirming no criterion sentence changed — only the identifier heading and mode line were inserted — and that the assignments were listed for review (AC-21)

**Implementation Note**: pause for manual confirmation before Phase 9.

---

## Phase 9 — Close-out: framework CI green and dogfood evidence complete

**Covers:** AC-22, AC-23, AC-24, AC-25, AC-26, AC-27, AC-28, AC-29, AC-33, and the AC-6 completeness assertion for this plan.

### Changes Required

**1. `evals/cases/validate_plan.json`** (new) — ≥1 positive and ≥1 negative case, following the shape of `evals/cases/spec.json`. Turns AC-24 green. Descriptions remain unedited, so `check_collisions` is unaffected.

**2. `thoughts/shared/evidence/2026-08-07-executable-acceptance-criteria.md`** — complete the green entries for all five automated criteria; verify every record carries the three AC-31 elements and a re-runnable `code_state`.

**3. `thoughts/shared/plans/2026-08-07-executable-acceptance-criteria-plan.md`** — mark all checkboxes to actual state.

### Success Criteria

#### Automated Verification
- [ ] `python3 scripts/validate.py` exits **0** — green for AC-22
- [ ] `python3 scripts/validate.py --check check_gate_sections` exits 0 — AC-27
- [ ] `python3 scripts/validate.py --check check_gate_single_source` exits 0 — AC-28
- [ ] `python3 scripts/validate.py --check check_command_size_budget` exits 0 — AC-29
- [ ] `python3 scripts/run_evals.py --check check_core_command_coverage` exits **0** — AC-24
- [ ] `python3 scripts/run_evals.py` exits 0 — routing evals and collision check
- [ ] `python3 scripts/build_skills.py && git diff --exit-code skills/.curated` — clean, AC-26 supporting check
- [ ] `bash setup.sh /tmp/ps-smoke-claude --provider=claude --copy --yes`, `--provider=codex`, `--provider=cursor` all succeed with the expected layout — AC-25 supporting check
- [ ] `wc -l < commands/core/spec.md` ≤ 300; `create_plan.md` ≤ 500; `implement_plan.md` ≤ 300; `validate_plan.md` ≤ 300
- [ ] `grep -rniE '\b(claude-[a-z0-9.-]+|gpt-[0-9][a-z0-9.-]*|gemini-[a-z0-9.-]+|opus|sonnet|haiku)\b' commands/ conventions/criterion-binding.md conventions/program-design.md` returns nothing — AC-23 supporting check
- [ ] All four CI jobs green on the branch (`.github/workflows/validate.yml:9-89`) — AC-22, AC-24, AC-25, AC-26

#### Manual Verification
- [ ] Owner confirms every one of the five automated criteria has a red and a green record with differing `code_state` values, and spot-re-runs at least the deterministically sampled one (AC-7, AC-8, AC-32)
- [ ] Owner confirms **no automated criterion is unbound** — the AC-6 completeness assertion for this plan
- [ ] Owner confirms all 31 manual-only criteria carry the four AC-4 elements and that AC-5 approval is recorded (AC-4, AC-5, D-6)
- [ ] Owner confirms the 5 / 31 split was reported before the plan was declared complete (AC-33)
- [ ] Owner confirms AC-23, AC-25, AC-26 are labeled manual-only with their supporting checks named, and signs off on Decision 8 (Review item 1)
- [ ] Owner confirms no frontmatter `description` changed anywhere in the diff (DEP-7 stays closed)

---

## Testing Strategy

### Named assertion groups (the automated layer)

- `check_gate_sections` — token presence in three sections × four commands. Edge cases: a token inside a fenced code block should still count (the sections are prose tables, so no special handling); a command that loses a required section is already caught by `scripts/validate.py:43-48`.
- `check_gate_single_source` — existence of the source, a resolvable link from each of the four commands, and no ≥25-word paragraph repeated across `{commands/core/*.md} ∪ {GATE_SOURCE}`. Edge cases: shared boilerplate such as the `## Setup (read before proceeding)` blocks is already near-identical across commands — verify the 25-word threshold does not trip on it during Phase 1, and raise `DUP_MIN_WORDS` or scope the comparison to paragraphs containing `pairing gate` if it does.
- `check_command_size_budget` — measured as `wc -l < file`. The spec's stated baselines are +1 for three files; the ceilings above are absolute and supersede them.
- `check_core_command_coverage` — presence and shape of a case file per `CORE_ROUTED` entry.

### Integration scenarios (the manual layer)

Run the full `/spec` → `/create_plan` → `/implement_plan` → `/validate_plan` chain against a small throwaway requirement, exercising: unbound criterion → `gate-blocked`; group that never failed → `gate-blocked`; degraded evidence on `none` stakes → labeled; degraded evidence on `auth` stakes → `gate-blocked`; manual-only unresolved → `awaiting-human-verdict`; same under `ci_mode: true` → `deferred`, non-halting; legacy spec → `legacy-unenforced`; two consecutive validations → identical pairing verdicts.

### Seeded cases named by the spec

- AC-32: re-run agrees → pass; re-run impossible → block; re-run contradicts → block.
- AC-35: high-stakes + degraded → block; high-stakes + single-group → pass; non-deny-list + degraded → labeled, not blocked.
- AC-9: bound group passing on first contact → unsatisfied, both causes named.

### Regression surface

`scripts/validate.py` and `scripts/run_evals.py` are refactored into registries. Phase 1's success criteria require each pre-existing check to exit 0 individually and the flagless run to behave as before, so the refactor is proven behavior-preserving before any new assertion is trusted.

---

## Performance Considerations

Negligible. The three new `validate.py` assertions read at most a few dozen markdown files already in memory from the existing walk; the duplicate-paragraph comparison is O(paragraphs²) over five files, on the order of a few thousand comparisons. `check_core_command_coverage` reads four JSON files.

The one real cost is the re-run in `/validate_plan`. Decision 5's floor deliberately bounds it: one group plus the touched set, rather than every group every time. On a first validation with no prior report the touched set is everything — acceptable here at five groups, and the reason the floor is defined as a set rather than a fixed count.

The four commands grow by 34–52 lines each and stay inside `conventions/three-layer-architecture.md:182-185`'s 300-line guidance; `create_plan.md` moves from 549 to ~489, a net improvement in the progressive-disclosure budget.

---

## Migration Notes

- **Existing specs.** Nothing is migrated automatically. A spec with zero mode lines is `legacy-unlabeled` and the gate is reported unenforced (AC-19, AC-20). Classification keys on format, never on date, so a legacy spec touched after this lands still classifies as legacy.
- **Upgrading a spec.** Operator-invoked via `/spec` (AC-21). The upgrade may only insert identifier headings and mode lines; any diff that changes criterion prose is a failed upgrade.
- **Downstream projects.** `test_group_command` / `test_suite_command` are optional and default to `""`. A project that never sets them keeps working; its evidence is degraded-but-labeled, and blocks only on deny-list criteria (AC-30, AC-34, AC-35). No config change is required to install this version.
- **`ticket_oneshot` remains outside the gate.** ASM-20 verified it never invokes `/validate_plan` (`commands/integrations/ticket_oneshot.md:31,40,49,54`). D-7 keeps it out of scope and OQ-9 is accepted; the Definition-of-Done wiring is being fixed as a separate task. Anyone relying on `/ticket_oneshot` gets no pairing gate.
- **New root `specs.config.yaml`.** Changes how commands resolve document storage in this repo — they will stop asking and use `thoughts/shared`. Reversible by deleting the file; see the Phase 5 fallback.

---

## Owner Review Items

1. **Decision 8 and the resulting 5 / 31 split (blocking for Phase 2).** AC-33 says "checkable → automated"; AC-9/AC-14 say a group that cannot fail is not evidence and blocks. Applied literally together, AC-23 and AC-26 would be bound to checks that can never redden, guaranteeing a permanent `gate-blocked`. This plan rules that such criteria go `manual-only` with a named supporting check. The alternative is to keep them `automated` and manufacture red with seeded fixtures — the technique the spec itself uses in AC-32's and AC-35's *Check* lines — which would raise the split to 7 / 29 but strains AC-7's phrase "against the pre-change code." Confirm the ruling or direct the alternative.
2. **AC-29 baselines are off by one.** The spec states 193 / 549 / 149 / 236; `wc -l` measures 192 / 549 / 148 / 235. The plan enforces absolute ceilings (300 / 500 / 300 / 300) with `wc -l < file` as the canonical measurement. Confirm the ceilings, especially `create_plan.md` at 500 — that is stricter than "must not grow further" and forces the extraction.
3. **New root `specs.config.yaml` (Phase 5).** Not named in the spec's IN scope. Without it, all five bindings record `strength: degraded` (nothing blocks, since every stakes value is `none`), which makes this plan a weaker demonstration of its own feature. The Phase 5 fallback is pre-authorized if you decline.
4. **`--check` selector in `validate.py` / `run_evals.py` (Phase 1).** Also beyond "four command files." Without it, no group in this repo is individually runnable, so AC-3's binding requirement cannot be satisfied at all — file-level groups would give only three distinct groups for five criteria and break injectivity. Flagged because it widens the changed-file set.
5. **`AC-25` classified manual-only.** The `install-smoke-test` CI job is fully mechanical, but it is not one of D-6's three enumerated sources. Amending D-6 to admit CI jobs as test groups would move it to automated. One-line decision.
6. **Intentional red CI from Phase 1 to Phase 9.** The `structural` job fails on this branch for most of the implementation, by design — that failure is the red evidence. Confirm this is acceptable for your PR workflow.

---

## References

- Spec: `thoughts/shared/specs/2026-08-07-executable-acceptance-criteria-spec.md` (AC-1 … AC-35, D-1 … D-10, ASM-1 … ASM-24, DEP-1 … DEP-12, OQ-11, OQ-12)
- Commands changed: `commands/core/spec.md`, `commands/core/create_plan.md`, `commands/core/implement_plan.md`, `commands/core/validate_plan.md`
- Conventions: `conventions/three-layer-architecture.md:161-186` (progressive disclosure, size guidance), `conventions/provider-portability.md:8-21,42-50` (neutral source, capability flags), `conventions/subagent-fallback.md`, `conventions/naming-conventions.md:251-282` (the only prior identifier convention), `conventions/thoughts-directory.md:88-110` (frontmatter shape)
- Standing bar: `references/definition-of-done.md:14,19-22` — linked, never restated
- Scripts: `scripts/validate.py:43-48,101-103,166-210`, `scripts/run_evals.py:191-246,249-265,275-300`, `scripts/build_skills.py:88-127`
- CI: `.github/workflows/validate.yml:9-89` (four jobs)
- Prior art in-repo: `agents/plan-skeptic.md:76-107` (severity vocabulary this plan deliberately does not collide with), `thoughts/shared/plans/2026-06-05-model-provider-agnostic.md` (plan format precedent)
