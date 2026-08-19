# Handoff: Add Codex-Style Standards Enforcement to project-specs

**Created:** 2026-08-16
**Status:** Implemented 2026-08-16 (steps 1–9; step 10 — promoting the second batch to `enforced` — is time-gated on 2–4 weeks of `approved` findings)
**Source:** Cloudflare Codex (Source 88 in playbook), Timo Reimann "How Cloudflare enforces engineering standards using AI"
**Why this matters:** project-specs already has 12 convention docs that define how the framework should be used. But nothing enforces them — agents don't check whether a plan follows `program-design.md`, whether a PR follows `pr-decomposition.md`, or whether a commit follows `naming-conventions.md`. The Codex model turns these conventions into machine-readable statements that agents can enforce at every step of the workflow.

## What you have today vs. what this adds

**Today:** Conventions are prose documents in `conventions/`. An engineer reads them (or doesn't). Commands don't reference them. A `/create_plan` that violates `program-design.md` passes silently.

**After:** Conventions are formalized with SHOULD/MUST semantics, extracted to a `statements.json` that agents query. `/create_plan` checks the plan against relevant standards. `/validate_plan` checks the implementation. `/describe_pr` checks the PR structure. Standards written once in conventions, enforced at every command that touches the thing they govern.

## What to change

### 1. Add SHOULD/MUST semantics to existing conventions

Each convention doc already contains implicit requirements. Formalize them with RFC 2119 keywords and add front matter:

```yaml
---
domain: workflow
status: enforced     # or: approved (non-blocking findings only)
sdlc_stage: planning # planning | implementation | review | all
---
```

Example — `conventions/pr-decomposition.md` already says:
> "Stack when: diff touches >3 files across >1 layer, or diff is >500 lines"

Rewrite as:
> Engineers **SHOULD** stack PRs when the diff touches more than 3 files across more than one architectural layer (data/API/UI), or when the diff exceeds 500 lines. Engineers **MUST** stack PRs when the diff exceeds 1,000 lines.

The convention doc stays human-readable. The SHOULD/MUST keywords are what the extractor picks up.

**Do this for each convention doc.** Not all at once — start with the 3-4 conventions that cause the most review friction, then add more as `approved` and promote to `enforced` after the team absorbs them.

**Suggested first batch (start enforced — these are already agreed practice):**
- `naming-conventions.md` — mechanical, easy to check
- `pr-decomposition.md` — high-value, directly addresses the review bottleneck
- `workflow-patterns.md` — the Research→Plan→Implement→Review sequence

**Suggested second batch (start as approved — surface findings, don't block):**
- `program-design.md` — more subjective, needs team calibration
- `three-layer-architecture.md` — violations are usually structural mistakes, not style
- `criterion-binding.md` — already has strict rules, but new to the team

### 2. New directory: `standards/`

```
standards/
  statements.json          # extracted SHOULD/MUST statements (build artifact)
  extractor.py             # script that parses conventions → statements.json
```

The `statements.json` schema, adapted from Cloudflare's format:

```json
{
  "version": "1.0",
  "extracted_at": "2026-08-16T00:00:00Z",
  "statements": [
    {
      "slug": "must-stack-prs-over-1000-lines",
      "source": "conventions/pr-decomposition.md",
      "domain": "review",
      "sdlc_stage": "review",
      "level": "MUST",
      "text": "Engineers MUST stack PRs when the diff exceeds 1,000 lines",
      "status": "enforced"
    },
    {
      "slug": "should-stack-prs-over-3-files-across-layers",
      "source": "conventions/pr-decomposition.md",
      "domain": "review",
      "sdlc_stage": "review",
      "level": "SHOULD",
      "text": "Engineers SHOULD stack PRs when the diff touches more than 3 files across more than one architectural layer, or when the diff exceeds 500 lines",
      "status": "enforced"
    }
  ]
}
```

The **slug** is stable — it survives convention doc edits. It's derived from the MUST/SHOULD statement text (kebab-cased key phrase), not from line numbers or section headings.

The **extractor** is a simple script that:
1. Reads each `conventions/*.md` file
2. Parses front matter for domain, status, sdlc_stage
3. Finds lines containing SHOULD or MUST (RFC 2119 bold keywords)
4. Generates a slug for each
5. Writes `statements.json`

Run the extractor on convention changes (git hook or CI step). The output is committed alongside the conventions so agents always have a current copy without running the extractor at runtime.

### 3. New command: `/check_standards`

**Location:** `commands/core/check_standards.md`

**When it runs:**
- Explicitly by the user: `/check_standards`
- Automatically as a step in `/validate_plan` and `/describe_pr`

**Behavior:**
1. Read `standards/statements.json`
2. Filter to statements matching the current SDLC stage (e.g., if called from `/validate_plan`, filter to `implementation` and `all`)
3. Read the artifact being checked (plan, implementation diff, PR description)
4. For each relevant statement, assess compliance
5. Output findings grouped by severity:

```
## Standards Check

### Blocking (MUST violations on enforced standards)
- [must-stack-prs-over-1000-lines] PR is 1,247 lines across 4 layers — MUST be stacked
  Source: conventions/pr-decomposition.md

### Recommendations (SHOULD violations or approved-only standards)
- [should-use-research-before-plan] No research document found in thoughts/ before plan creation
  Source: conventions/workflow-patterns.md

### Passed (3 of 5 checked)
- [must-have-acceptance-criteria] ✓
- [must-have-scope-boundaries] ✓
- [must-use-specs-config] ✓
```

**MUST on enforced standards** = blocking finding. `/validate_plan` reports the check as failed. `/describe_pr` warns before creating the PR.
**SHOULD or approved-only** = non-blocking recommendation. Surfaced but doesn't block.

### 4. Wire into existing commands

**`/validate_plan`** — add a standards check phase after the existing plan-vs-implementation verification:

```
### Phase N: Standards Compliance
1. Load standards/statements.json, filter to sdlc_stage: implementation
2. Check implementation against each relevant statement
3. Add findings to the Validation Report under a "Standards Compliance" section
4. If any MUST violation on an enforced standard → validation fails
```

**`/describe_pr`** — add a pre-flight standards check:

```
Before creating the PR:
1. Load standards/statements.json, filter to sdlc_stage: review
2. Check the diff against review-stage standards (PR size, stacking, commit conventions)
3. If blocking findings exist → warn the user and ask whether to proceed
```

**`/create_plan`** — add a standards check on the plan output:

```
After generating the plan:
1. Load standards/statements.json, filter to sdlc_stage: planning
2. Check the plan against planning-stage standards (program design phases, research-before-plan)
3. Surface findings as recommendations in the plan document itself
```

**`/spec`** — lightest touch. After the spec is finalized:

```
1. Load standards/statements.json, filter to sdlc_stage: planning
2. Check whether the spec's acceptance criteria conflict with any existing standards
3. Surface as a note, never block spec creation
```

### 5. Add `standards` section to `specs.config.yaml`

```yaml
standards:
  enabled: true
  statements_path: "standards/statements.json"
  enforcement:
    must_on_enforced: block       # block | warn | ignore
    should_on_enforced: warn      # block | warn | ignore
    must_on_approved: warn        # block | warn | ignore
    should_on_approved: ignore    # block | warn | ignore
```

This lets teams tune enforcement granularity. A team just adopting the framework might start with everything as `warn`. A mature team promotes to `block` on enforced MUSTs.

### 6. Convention: `conventions/standards-governance.md`

New convention documenting:
- How to propose a new standard (add SHOULD/MUST to an existing convention, or write a new one)
- The approved→enforced promotion lifecycle
- Who owns each domain (initially: repo owner for all domains; as the org grows, delegate)
- How to request an exception (waiver) for a specific standard on a specific project
- The extractor workflow: edit convention → run extractor → commit `statements.json`

## Implementation order

1. Add front matter (domain, status, sdlc_stage) to the first 3 convention docs
2. Add SHOULD/MUST keywords to those conventions' existing requirements
3. Write `standards/extractor.py` and generate the first `statements.json`
4. Write `commands/core/check_standards.md`
5. Wire `/check_standards` into `/validate_plan` as a new phase
6. Wire into `/describe_pr` as a pre-flight check
7. Write `conventions/standards-governance.md`
8. Add `standards` section to `specs.config.example.yaml`
9. Add remaining conventions to the Codex (second batch, as `approved`)
10. After 2-4 weeks of `approved` findings, promote stable standards to `enforced`

## What this does NOT cover

- **Linter fast-path.** Cloudflare ships oxlint packages for mechanically-verifiable rules. For project-specs, the equivalent would be a script that checks naming conventions or file structure without an LLM. Worth adding later, but the LLM-based `/check_standards` command is the starting point.
- **Incident report review.** Not applicable — project-specs doesn't manage incident reports. If you add postmortem conventions, the same Codex model extends naturally.
- **Cross-repo standards.** This handoff covers one repo's conventions. If you want org-wide standards (shared across project-specs, agent-personas, and other repos), that's a separate corpus that lives outside any single repo and gets vendored in. The `statements_path` in config supports pointing to a vendored file.
- **Spec reviewer as a standalone service.** Cloudflare runs theirs on Workers + D1 + Cron, scanning all specs continuously. For project-specs, the check runs inline within commands — simpler, no infrastructure, same enforcement.

## Expected outcomes

- **Standards violations caught before code review.** The biggest time sink in review is catching things the author should have known. If `/validate_plan` catches "you didn't stack this 800-line PR" before the PR is created, the reviewer doesn't have to.
- **Conventions become living documents.** Today, conventions are write-once-read-never. When agents enforce them, engineers actually encounter them — and propose improvements when a standard doesn't make sense for their case.
- **New engineer onboarding improves.** A new engineer who runs `/create_plan` and gets back "SHOULD: use the Research→Plan→Implement→Review sequence" learns the convention at the point of work, not from a wiki they may never read.
- **Measurable adoption signal.** Track violation trends per slug over time. Declining trend = convention is being absorbed. Flat trend = convention needs better communication or the convention itself is wrong.

## Cross-references

- **Source 88 (Cloudflare Codex):** The reference implementation. 230K violations, 16K blocks, 600 specs reviewed.
- **Source 40 (antirez DESIGN.md):** Per-component design docs. The Codex is DESIGN.md scaled to org-wide governance.
- **Source 75 (Braintrust BEHAVIOR.md):** Per-behavior standards for eval targeting. Complementary — behaviors define what to test, Codex standards define what to comply with.
- **agent-personas C1 (Review Panel):** The review panel's four lens reviewers could each consume `statements.json` filtered to their domain (security lens reads security-domain statements, correctness lens reads architecture-domain statements).
- **agent-access-model-handoff.md:** The Trust Ratchet could trigger on MUST violations — a MUST violation during implementation could ratchet permissions (remove write access, switch to analysis-only mode).
