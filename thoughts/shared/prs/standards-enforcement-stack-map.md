---
date: 2026-08-19
feature: codex-standards-enforcement
base: main
status: open
---

# Stack Map — Codex-Style Standards Enforcement

Decomposition of the standards-enforcement work (see
`thoughts/decisions/codex-standards-enforcement-handoff.md`). Trigger: full
diff was ~1,260 lines across 24 files, past the 1,000-line MUST-stack
threshold in `conventions/pr-decomposition.md`.

| # | Branch | Base | Contents | ~Size |
|---|--------|------|----------|-------|
| 1 | `feat/standards-1-conventions` | `main` | Front matter + RFC 2119 keywords in six conventions | 78+/31- |
| 2 | `feat/standards-2-engine` | layer 1 | Extractor, statements registry, `/check_standards`, governance convention, registry validation | 823+ |
| 3 | `feat/standards-3-wiring` | layer 2 | Wiring into 4 core commands, config blocks, installer, CI drift job | 83+/2- |
| 4 | `feat/standards-4-docs` | layer 3 | README, AGENTS.md, usage guide, changelog, handoff status, this map | docs only |

Note: layer 2 exceeds the 500-line SHOULD threshold at 823 lines. 380 of those
are the generated `statements.json` and the layer is one cohesive unit
(registry + producer + consumer + rules would not review sensibly apart), so
it ships as one PR. The middle-ground rule in `pr-decomposition.md` permits
this judgment; recorded here so the reviewer sees it was a decision, not an
oversight.

## Review Focus

### Layer 1 — conventions
1. Does each bold MUST/SHOULD sentence stand alone out of context (no "the table above")?
2. Are the enforced/approved batch assignments right — is anything in the enforced batch not actually agreed practice?
3. Is the new 1,000-line MUST-stack threshold the number we want?

### Layer 2 — engine
1. Is slug derivation stable enough (level + subject + predicate words) — will routine doc edits leave slugs alone?
2. Does the extractor correctly skip code blocks and keyword *mentions* vs. keyword *usage*?
3. Is the `extracted_at` preservation logic sound (deterministic output for unchanged conventions, so CI drift-diff works)?

### Layer 3 — wiring
1. Are the enforcement semantics consistent across the four commands (block only in validate_plan, warn in describe_pr, recommend elsewhere)?
2. Does each wired command stay inside its validate.py line budget?
3. Is installing `standards/` at the target project root (individual file copies, no rm -rf) the right install behavior?

### Layer 4 — docs
1. Does the README section explain the model to someone who has never seen Cloudflare's Codex?
2. Do the AGENTS.md obligations (regenerate registry, standalone sentences) match what CI actually enforces?
