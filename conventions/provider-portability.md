# Provider Portability

project-specs runs across multiple coding-agent providers from a single neutral
source. **Claude Code is the reference implementation**; OpenAI Codex CLI and
Cursor are also supported. This document describes how portability works and how
to add a new provider.

## Principle: neutral source, provider manifests, installer adapts

- `agents/`, `commands/`, `skills/` are the **single source of truth**, authored
  in provider-neutral markdown. They are never edited per-provider.
- `providers/<provider>/manifest.yaml` captures everything provider-specific as
  **data**: where files install, what format transform is needed, model-tier
  defaults, and capability flags.
- `setup.sh --provider=<name>` reads the manifest and installs accordingly —
  copying for providers that read markdown, or generating provider-native files
  for those that don't.

This keeps provider-specific knowledge out of the command/agent bodies and in
one declarative place per provider.

## The manifest schema

```yaml
provider: <id>
display_name: "<human name>"
install:
  base_dir: ".claude"            # install root relative to project
  config_format: markdown|toml  # native format of the provider
  agents_subdir: "agents"       # where agent defs go
  commands_subdir: "commands"   # where command defs go (copy providers)
  skills_subdir: "skills"       # where skills go
  commands_dest: "skills"       # (transform providers) commands install AS skills
  root_instructions: "AGENTS.md"|null   # root instruction file, if any
  settings_template: "settings.local.json"|null  # permissions artifact, if any
  transform: copy|skill+toml    # installer behavior
command_invocation: slash|skill|mention
models:                         # semantic tier → concrete model id (or "")
  planning: ""
  analysis: ""
  quick: ""
capabilities:
  subagents: true|false         # drives conventions/subagent-fallback.md
  mcp: true|false               # drives conventions/ticket-integration.md (mcp mode)
  tool_frontmatter: true|false  # honors `tools:` allowlist (Claude only)
  model_pinnable: true|false    # can a file pin the model?
```

All manifests must share the same top-level keys (schema consistency is checked
at install time).

## Capability-gated behavior

Two coupling points vary by provider and are handled by convention, not by
forking the command bodies:

- **Subagents** — see [subagent-fallback](./subagent-fallback.md). Commands spawn
  research agents in parallel when `capabilities.subagents: true`, else perform
  the same research inline/sequentially. All three current providers support
  subagents; the fallback is defensive.
- **Ticket integration** — see [ticket-integration](./ticket-integration.md).
  Commands write ticket ops in `{ticket_mcp_prefix}__<op>` form; the project's
  `ticket_integration` (mcp|cli|none) decides how each op is performed.

## Model selection across providers

Commands/agents declare a **semantic tier** (`planning`/`analysis`/`quick`) in
frontmatter, never a literal model. Resolution order:

1. `specs.config.yaml` `models:` block (project override), then
2. `providers/<provider>/manifest.yaml` `models:` defaults.

Notes per provider:
- **Claude** — tiers map to `opus`/`sonnet`/`haiku`.
- **Codex** — leave tiers empty to let Codex auto-select its recommended model;
  pin a `gpt-5.x` id only if you need determinism (`model_pinnable: true`).
- **Cursor** — main-agent model is chosen in the Cursor UI and is **not**
  file-pinnable (`model_pinnable: false`); tiers are advisory only.

## Format transforms

| transform   | Used by | What the installer does |
|-------------|---------|-------------------------|
| `copy`      | claude, cursor | Copy/symlink neutral markdown into the install dir. |
| `skill+toml`| codex   | Generate a `SKILL.md` folder per command (custom prompts are deprecated in Codex) and a TOML subagent def per agent. |

## Adding a new provider

1. Create `providers/<name>/manifest.yaml` with all schema keys.
2. If the provider reads markdown, set `transform: copy`. If it needs native
   formats, either add a transform branch to `setup.sh` or pre-build artifacts.
3. Set `capabilities` honestly — `subagents`/`mcp` drive the fallbacks above.
4. Add an example at `examples/<name>/specs.config.yaml`.
5. Register provider-dependent assumptions in
   [model-assumptions.md](./model-assumptions.md) (Provider-Dependent Patterns).

See [Appendix: Verified Provider Facts] in the implementation plan
(`thoughts/shared/plans/2026-06-05-model-provider-agnostic.md`) for the
researched paths/capabilities behind the current manifests, and re-verify
fast-moving items (model ids, MCP tool naming) before relying on them.
