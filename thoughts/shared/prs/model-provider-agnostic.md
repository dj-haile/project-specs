## What does this PR do?

Makes project-specs **provider-agnostic** — the same neutral source installs to Claude Code (reference), OpenAI Codex CLI, and Cursor — so the framework isn't locked to a single coding agent. Existing Claude Code users are unaffected unless they opt in.

## Problem

Every coupling point in the framework assumed Claude Code: the `.claude/` install path, slash-command syntax, Claude tool names, subagent spawning, `mcp__` ticket prefixes, literal model names (`opus`/`sonnet`/`haiku`), and the permissions file. None of the architecture required this — only conventions and names did — but nothing let you target another provider.

## Solution

Introduce a thin **provider manifest layer** that captures everything provider-specific as data, keep all command/agent bodies provider-neutral, and make the two un-portable behaviors (subagents, ticket integration) config-driven with graceful fallbacks.

- `providers/<name>/manifest.yaml` declares install location, format transform, model-tier defaults, and capability flags.
- `setup.sh --provider=<name>` reads the manifest (via an embedded python3/PyYAML helper — no `yq` dependency). For Codex it transforms commands→Skills and agents→TOML; for Claude/Cursor it copies markdown.
- Commands declare **semantic model tiers** (`planning`/`analysis`/`quick`) resolved per provider, and gate subagent/ticket behavior on capability flags documented in new convention files.

## Changes

**New (Phase 1–2): manifests + installer**
- `providers/{claude,codex,cursor}/manifest.yaml`
- `setup.sh`: `--provider` flag, manifest-driven install, Codex transform (SKILL.md + TOML + AGENTS.md), installs the `conventions/` commands reference
- `specs.config.example.yaml`: `provider`, `ticket_integration`, `ticket_cli`

**Changed (Phase 3): de-coupled bodies**
- Model frontmatter literal → semantic tiers across 19 commands/agents
- Subagent invocations capability-gated → `conventions/subagent-fallback.md`
- Ticket commands honor `ticket_integration: mcp|cli|none` → `conventions/ticket-integration.md`

**Docs (Phase 4 + this round)**
- `conventions/provider-portability.md`, Provider-Dependent Patterns in `model-assumptions.md`
- README: provider-neutral retitle, Supported Providers table, **Prerequisites** (bash + python3/PyYAML)
- `examples/{codex,cursor}/specs.config.yaml`, CHANGELOG entry, AGENTS.md tier note

## Breaking changes

**None for default usage.** `--provider=claude` (the default) installs byte-identically to prior behavior (verified by diff against source). The one item to note: command/agent frontmatter now uses semantic tiers instead of literal model names — projects that pinned literal models should confirm their `models:` block maps the tiers (the example config has done so since v1.0.0).

## How to verify it

- [x] Manifests parse and share a schema; example configs valid; `setup.sh` syntax clean
- [x] `--provider=claude` install is byte-identical to source (no regression)
- [x] Codex/Cursor installs produce the right layout; bogus provider exits 1
- [x] Codex transform generates valid SKILL.md (single frontmatter) + TOML subagents
- [x] All 28 internal doc links resolve; 13/13 convention links resolve from installed command locations (all 3 providers)
- [x] **Live end-to-end**: installed into a real project (`agent-readiness-cli`), executed the installed `create_plan` — config read, semantic tier, capability-gated subagents, convention links, and thoughts/ output all worked; produced a grounded plan
- [ ] (Manual, pre-prod) Verify Codex/Cursor discover installed files against a live CLI; re-confirm the ⚠️ items (Codex `gpt-5.x` model ids, MCP tool-name namespacing)

## Changelog entry

Added multi-provider support (Claude Code, OpenAI Codex CLI, Cursor) via provider manifests, a manifest-driven installer, semantic model tiers, and capability-gated subagent/ticket fallbacks — backward compatible for existing Claude Code installs.

## Notes for reviewers

- Two deviations from the original plan, both improvements: dropped the `yq` dependency in favor of embedded python3/PyYAML; used shared convention files for the subagent/ticket fallbacks instead of inlining the contract into every command.
- The Codex transform produces structurally valid files; whether the live Codex CLI accepts them end-to-end is the one gap left for a real-CLI check.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
