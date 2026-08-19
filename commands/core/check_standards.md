---
name: check_standards
description: Check an artifact against the standards registry extracted from conventions and report MUST/SHOULD violations by severity
model: analysis
---

# Check Standards

You are tasked with checking an artifact — a plan, an implementation diff, or a PR — against the standards extracted from this project's conventions, and reporting compliance findings grouped by severity. The standards model and lifecycle are defined in [standards-governance](../../conventions/standards-governance.md); this command is the enforcement point.

## Setup (read before proceeding)

1. Check if `specs.config.yaml` exists at project root and read its `standards:` block:
   - `standards.enabled` — if `false`, report "standards checking disabled" and stop
   - `standards.statements_path` — where the registry lives (default `standards/statements.json`)
   - `standards.enforcement` — how each level × status combination is treated (`block` | `warn` | `ignore`)
2. Read the statements registry. If it is missing, report that and suggest `python3 standards/extractor.py` — do not fail the calling workflow over a missing registry.
3. Determine the SDLC stage to filter to (see below).

## When This Runs

- **Explicitly**: the user invokes `/check_standards [artifact path]`
- **Automatically**: as a step inside `/create_plan` (stage `planning`), `/validate_plan` (stage `implementation`), `/describe_pr` (stage `review`), and `/spec` (stage `planning`, note-only)

When invoked explicitly with no artifact, infer the most useful target: an uncommitted diff → check the diff at stage `review`; a plan path given → check the plan at stage `planning`. Say which artifact and stage you chose.

## Process

1. **Load and filter statements.** From the registry, keep statements whose `sdlc_stage` matches the current stage, plus every statement with `sdlc_stage: all`.
2. **Read the artifact being checked** — the plan document, the implementation diff (`git diff` against the base branch), or the PR description and its diff.
3. **Assess each statement against the artifact.** A statement is only a finding if the artifact actually exhibits the violation — quote the evidence (the diff numbers, the missing section, the misnamed file). Statements the artifact gives no occasion to violate are not "passed"; count only statements that were genuinely checkable.
4. **Check for recorded waivers** ([standards-governance](../../conventions/standards-governance.md)): a violation whose slug is waived in the plan's `## What We're NOT Doing` or the PR's `## Standards Waivers` section, with a reason, is reported as waived — not as a finding.
5. **Classify each violation** using `standards.enforcement` from config. Defaults:

   | Level | Status | Default treatment |
   |---|---|---|
   | MUST | enforced | **block** |
   | SHOULD | enforced | warn |
   | MUST | approved | warn |
   | SHOULD | approved | ignore (still listed, lowest priority) |

## Output Format

```
## Standards Check (stage: review)

### Blocking (MUST violations on enforced standards)
- [must-stack-prs-diff-exceeds-1000-lines] PR is 1,247 lines across 4 layers — MUST be stacked
  Source: conventions/pr-decomposition.md

### Recommendations (SHOULD violations or approved-only standards)
- [should-run-research_codebase-before-create_plan-new-features] No research document found before plan creation
  Source: conventions/workflow-patterns.md

### Waived
- [should-stack-prs-diff-exceeds-500-lines] Waived in PR description: "single-module mechanical rename"

### Passed (3 of 5 checked)
- [must-leave-codebase-green] ✓
- [must-not-auto-stack] ✓
- [must-use-kebab-case] ✓
```

Every finding carries its slug and its source file, so the reader can open the convention that owns the rule. Omit empty sections except **Passed**, which always appears with its count.

## How Callers Consume the Result

- **`/validate_plan`** — any blocking finding fails the standards phase of the validation report.
- **`/describe_pr`** — blocking findings trigger a warning and a confirmation before the PR is created; in CI-mode, note them in the description and continue.
- **`/create_plan`** and **`/spec`** — findings are surfaced as recommendations/notes only; never block authoring.
- **Standalone** — report the findings; change nothing.

This command **reports**; it never edits the artifact, auto-stacks a PR, or blocks on its own authority. Blocking is always the calling command's decision, applied per the enforcement config.

## Red Flags

Observable signs that you are drifting off this workflow:

- You reported a violation without quoting the artifact evidence that shows it
- You marked a statement "passed" that the artifact never gave you occasion to check
- You softened a MUST-on-enforced finding to a recommendation because the fix felt expensive — that decision belongs to the enforcement config, not to you
- You treated an unwaived violation as waived because the author's intent seemed reasonable — a waiver needs a recorded slug and reason
- You edited the artifact to make a finding go away instead of reporting it

## Error Handling

- Registry missing or unparseable → report it, suggest `python3 standards/extractor.py`, and return no findings rather than failing the caller
- `standards.enabled: false` → report "standards checking disabled" and return
- No artifact found (empty diff, no plan) → say so and suggest the likely cause
