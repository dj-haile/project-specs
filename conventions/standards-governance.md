---
domain: governance
status: approved
sdlc_stage: all
---

# Standards Governance

One-line summary: how SHOULD/MUST standards are proposed, extracted into `standards/statements.json`, promoted from `approved` to `enforced`, and waived when a project has a good reason not to comply.

The framework's conventions double as its standards. A convention doc stays human-readable prose, but any requirement written with a bold RFC 2119 keyword (`MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`) is also a machine-readable statement that `/check_standards` — and the commands wired to it — enforce at the point of work. This file governs that lifecycle.

## How a convention becomes a standard

To make a convention enforceable, start its file with three metadata keys (the YAML front matter):

```yaml
---
domain: review        # grouping used to filter statements (review, workflow, planning, …)
status: enforced      # enforced | approved
sdlc_stage: review    # planning | implementation | review | all
---
```

A convention without front matter contributes no statements — it is documentation only. This is deliberate: standards roll out incrementally, not by fiat over the whole `conventions/` directory at once.

## Proposing a new standard

1. **Prefer amending an existing convention.** Add the requirement as a sentence carrying a bold `SHOULD` or `MUST` keyword. Write it so the sentence stands alone — statements are read from `statements.json` without the surrounding doc, so "the thresholds above" reads as nothing out of context. New standalone conventions are for genuinely new domains.
2. A new standard **SHOULD** enter as `status: approved`, so its findings surface without blocking anyone. The exception is a standard that codifies practice the team already follows — that may start `enforced`.
3. Each normative sentence **SHOULD** carry exactly one RFC 2119 keyword, since one sentence becomes one statement with one level.
4. Open a PR. The reviewer of a standards change is reviewing two things: is the requirement right, and is the sentence extractable (standalone, one keyword, correct level).

## The extractor workflow

`standards/extractor.py` reads every enforceable convention and writes `standards/statements.json`. The output file is committed, so agents read it at runtime instead of running the extractor.

Engineers **MUST** regenerate `standards/statements.json` and commit it in the same PR as any convention edit that adds, removes, or rewords a bold SHOULD/MUST sentence:

```bash
python3 standards/extractor.py
```

CI regenerates the registry on every PR and fails if the committed file is stale, so a forgotten regeneration is caught before merge, not in the field.

A statement's **slug** is derived from its own text, so editing a statement's wording changes its slug. That is intended: a changed slug is the visible signal that the standard itself changed, and any waiver or trend data keyed to the old slug should be re-examined.

## Promotion: approved → enforced

- `approved` — violations surface as recommendations. Nothing blocks. This is the calibration period: the team sees the findings and either absorbs the standard or amends it.
- `enforced` — a `MUST` violation is a blocking finding (`/validate_plan` fails the check; `/describe_pr` warns before creating the PR). `SHOULD` violations remain recommendations even when enforced.

A standard **SHOULD** be promoted to `enforced` only after 2–4 weeks of `approved` findings show the violation trend is declining or flat-and-understood. A flat trend with recurring violations means the standard needs better communication — or the standard is wrong. Amend it rather than promoting it.

Promotion is a one-line front matter change (`status: approved` → `status: enforced`) plus the regenerated registry, reviewed like any other standards PR. Note that `status` is per-convention: promoting one doc promotes all of its statements together. Split a convention if half of it is ready and half is not.

## Ownership

Each `domain` has an owner who approves standards changes in that domain. Initially the repo owner owns all domains; as the org grows, delegate per domain (e.g., a security lead owns `security`, a platform lead owns `architecture`). The owner is the person who decides promotions and waivers.

## Waivers

A project may have a good reason not to comply with a specific standard for a specific piece of work. In that case:

1. A waiver **MUST** name the statement's slug, the scope it applies to (a PR, a plan, or a project), and the reason.
2. Record it where the check will see it — in the plan's `## What We're NOT Doing` section, or in the PR description under a `## Standards Waivers` heading.
3. `/check_standards` reports a waived violation as waived (with the recorded reason) rather than as a finding. A waiver with no reason is not a waiver.
4. Recurring waivers of the same slug are a signal the standard is miscalibrated — take it back to `approved` and fix it.

## Enforcement tuning

Teams tune how hard each combination of level × status bites via the `standards:` block in `specs.config.yaml` (see `specs.config.example.yaml`). The defaults — block on MUST-enforced, warn on SHOULD-enforced and MUST-approved, stay silent on SHOULD-approved — match the lifecycle above. A team just adopting the framework can set everything to `warn` while calibrating.

## Cross-references

- [check_standards](../commands/core/check_standards.md) — the command that runs the check
- `standards/statements.json` — the extracted registry (build artifact, committed)
- [Cloudflare's Codex](https://blog.cloudflare.com/how-cloudflare-enforces-engineering-standards-using-ai/) — the reference implementation this model adapts
