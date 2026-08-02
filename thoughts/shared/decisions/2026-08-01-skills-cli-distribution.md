# Decision: skills-CLI distribution (`npx skills add dj-haile/project-specs`)

**Date:** 2026-08-01
**Status:** Recommendation — awaiting owner go/no-go
**Scope:** Handoff item 3 (marked optional). Goal was to make project-specs
installable via the [vercel-labs/skills](https://github.com/vercel-labs/skills)
CLI, which reaches 70+ agent tools.

## TL;DR

**Recommendation: conditional GO, gated on owner sign-off — do not merge blind.**
The transform is feasible and mostly low-risk, but it introduces three real
costs (committed generated artifacts, broken `conventions/` cross-links for CLI
consumers, and dropped model-tier frontmatter) that are product decisions, not
mechanical ones. This doc specifies a ready-to-implement design so the work is a
single focused PR once approved. If the owner would rather not carry the extra
distribution surface, the honest answer is **NO-GO** and this doc is the record
of why — the framework already installs everywhere it needs to via `setup.sh`.

## How the CLI works (verified against its README, 2026-08-01)

- `skills add <source>` accepts `owner/repo` shorthand, full URLs, subpaths, git
  URLs, local paths, and direct `SKILL.md`/archive downloads.
- It **discovers** skills by scanning the repo 1–2 levels deep in standard
  locations: repo root (if it has a `SKILL.md`), `skills/`, `skills/.curated/`,
  `skills/.experimental/`, and agent paths like `.claude/skills/`,
  `.agents/skills/`.
- A skill is **a directory containing a `SKILL.md`** with YAML frontmatter.
  **Required fields: `name`, `description` only.** Optional `metadata.internal:
  true` hides a skill from discovery.
- It installs into agent-specific dirs (`./<agent>/skills/` project scope,
  `~/<agent>/skills/` global) by symlink (default) or `--copy`.

## Fit assessment

project-specs's primary units are **commands** (`commands/**/*.md`) and
**agents** (`agents/*.md`). The `skills/` directory holds only `_template/`.
So today `skills add dj-haile/project-specs` would:

1. Discover `skills/_template/SKILL.md` and try to install it as a skill named
   `my-skill-name` (its placeholder frontmatter) — i.e. install the **template**
   as if it were a real skill. This is actively wrong.
2. Surface **none** of the framework's real value (the commands and agents).

To distribute the real value, the repo must contain committed `SKILL.md`
directories, one per command/agent, in a discovery location. That is a
**transform** — the same shape `setup.sh` already performs for Codex
(`commands/**/<name>.md → .agents/skills/<name>/SKILL.md`,
`setup.sh:239-277`) — but the output must be committed to the repo rather than
produced at install time, because the CLI reads the repo over git and never runs
our build.

### What is genuinely fine

- **`--provider=claude` stays byte-identical.** `setup.sh`'s claude/cursor path
  installs only `agents/` and `commands/` (`setup.sh:329-330`); it never copies
  the source `skills/` tree into a project. Adding generated skills under
  `skills/` therefore cannot change any `setup.sh` install. Verified.
- **`validate.py` is unaffected.** It scans `commands/**` and `agents/*.md`
  only; it does not walk `skills/`. Generated skills won't break structural
  validation.
- **Three-layer architecture is preserved.** The transform is a *packaging view*
  of existing commands/agents for one more distribution channel, not a
  restructure. Source layers are untouched.

### The three real costs (why this needs sign-off)

1. **Committed generated artifacts + drift.** ~26 `SKILL.md` files (19 commands
   + 7 agents) would be committed and must stay in sync with their sources. This
   needs a CI "regenerate and `git diff --exit-code`" guard, or the skills
   silently rot. New maintenance obligation on every command/agent edit.

2. **Broken `conventions/` cross-links for CLI consumers.** Command/agent bodies
   link to `../../conventions/*.md`, `../../references/definition-of-done.md`,
   etc. `setup.sh` solves this by copying `conventions/` next to the install
   (`setup.sh:346-349`). The vercel CLI installs a skill **directory only** — it
   won't bring `conventions/` along, so every such link 404s in a consuming
   project. The workflow bodies still work; the cross-references degrade. Fixing
   it properly means inlining referenced conventions into each SKILL.md at
   transform time (larger transform, larger files) or accepting the degradation.

3. **Model tiers are dropped.** The community SKILL.md shape is `name` +
   `description`. Our `model: planning|analysis|quick` tier carries no meaning to
   the 70+ target tools and would be dropped or ignored. Acceptable, but it means
   the distributed skills lose the model-selection signal the framework relies on.

Secondary: distributing to 70+ tools invites issues/expectations from
environments we don't test. That's a support-surface decision for the owner.

## Recommended design (if GO)

A single PR, no changes to existing `setup.sh` flows:

1. **`scripts/build_skills.py`** — transform each `commands/**/<name>.md` and
   `agents/<name>.md` into `skills/.curated/<name>/SKILL.md`:
   - Frontmatter: keep `name` + `description` verbatim; **drop** `model`/`tools`
     (or move to `metadata:` for provenance). Add `metadata.source:
     commands/core/<name>.md` so drift is traceable.
   - Body: the source body. **Decision knob:** either (a) leave `../../`
     convention links as-is (accept 404s in consumers) or (b) rewrite them to
     absolute `https://github.com/dj-haile/project-specs/blob/main/...` URLs so
     they resolve anywhere. Recommend (b) — cheap, and it keeps the cross-refs
     working for CLI consumers.
   - Put output under `skills/.curated/` (a documented discovery dir) so it is
     visibly generated and separate from hand-authored `skills/`.
2. **Hide the template.** Add `metadata:\n  internal: true` to
   `skills/_template/SKILL.md` so the CLI never offers the template as a skill.
3. **CI drift guard.** New job in `.github/workflows/validate.yml`: run
   `build_skills.py`, then `git diff --exit-code skills/.curated` — fails if a
   command/agent changed without regenerating. Mirrors the existing validate/eval
   jobs (Python + PyYAML only).
4. **`validate.py` extension (optional).** Add a light check that every
   `skills/.curated/*/SKILL.md` has `name` + `description`, so generated output
   is covered too.
5. **README.** Add an "Install via skills CLI" note:
   `npx skills add dj-haile/project-specs` — and state that it installs the
   commands/agents as skills, with model-tier selection not carried.
6. **CHANGELOG** Unreleased entry.

Estimated size: ~1 script (~80 lines), 1 CI job, ~26 generated files, small
docs. No edits to the claude/cursor/codex install paths.

## Alternatives considered

- **Restructure the repo around `skills/`** — rejected. Breaks the three-layer
  architecture the framework is built on; the handoff explicitly prefers the
  transform.
- **Do nothing / NO-GO** — legitimate. `setup.sh --provider=<claude|codex|
  cursor>` already covers the reference targets. The skills CLI is reach, not a
  gap. If the maintenance surface isn't wanted, this is the right call.

## Open question for the owner

Ship the transform (conditional GO, ~1 PR as designed above), or decline the
extra distribution surface (NO-GO)? If GO, confirm the convention-link knob:
rewrite to absolute GitHub URLs (recommended) vs. accept degraded links.
