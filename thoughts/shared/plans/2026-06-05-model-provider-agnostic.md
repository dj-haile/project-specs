# Model-Provider-Agnostic project-specs Implementation Plan

## Overview

Make the project-specs framework work across multiple coding-agent providers — **Claude Code** (reference implementation), **OpenAI Codex CLI**, and **Cursor** — while preserving its effectiveness. The framework's *architecture* is already provider-neutral (config-driven, three-layer, markdown-based); what couples it to Claude Code is a contained set of conventions: install directory, slash-command syntax, tool names, subagent spawning, MCP ticket prefixes, model names, and the permissions file. This plan introduces a `providers/` manifest layer and a capability-gated fallback pattern so a single neutral source installs and runs correctly on each provider.

## Current State Analysis

The repo cleanly separates **source** (`agents/`, `commands/`, `skills/`) from **install target** (`.claude/`), which is the single most important precondition for going multi-provider — it already exists.

**The 7 coupling points, with verified spread across files:**

| # | Coupling point | Where it lives | Count |
|---|----------------|----------------|-------|
| 1 | Install/discovery dir (`.claude/agents/`, `.claude/commands/`) | `setup.sh` (hardcodes `CLAUDE_DIR`) | 1 file |
| 2 | Slash-command syntax (`/create_plan`, `/spec`) | command bodies, cross-references, README | many (prose) |
| 3 | Tool names (`Read`, `Grep`, `Glob`, `Bash`, `TodoWrite`, `LS`, `WebFetch`, `WebSearch`) | command + agent bodies, `tools:` frontmatter | most files |
| 4 | Subagent spawning ("spawn Task agents in parallel") | `commands/core/`: create_plan, implement_plan, validate_plan, spec, research_codebase | 5 files |
| 5 | MCP ticket prefix (`ticket_mcp_prefix: mcp__linear`) | `commands/integrations/`: all 7 | 7 files |
| 6 | Model names (`model: opus`/`sonnet`/`haiku`) | frontmatter in 6 agents + 13 commands | ~19 files |
| 7 | Permissions (`.claude/settings.local.json`) | install artifact | 1 file |

**Agent-name references** (codebase-locator, etc.) appear in 3 core commands: create_plan, spec, research_codebase ([commands/core/create_plan.md:60-62](../../../commands/core/create_plan.md#L60-L62)).

### Key Discoveries:
- **Source/target separation already exists** — [setup.sh:142-174](../../../setup.sh#L142-L174) copies/symlinks `agents/` and `commands/` into `.claude/`. Only the *target path* and a couple of artifacts are Claude-specific; the loop logic is reusable.
- **Config already abstracts two of the seven points.** `ticket_mcp_prefix` ([specs.config.example.yaml:22](../../../specs.config.example.yaml#L22)) is templated, and `models:` ([specs.config.example.yaml:40-43](../../../specs.config.example.yaml#L40-L43)) already expresses **semantic tiers** (`planning`/`analysis`/`quick`) — the exact indirection we need for model-name portability. The frontmatter `model: opus` is the only place that bypasses these tiers.
- **The framework already thinks in model-independent vs model-dependent terms.** [conventions/model-assumptions.md](../../../conventions/model-assumptions.md) is a registry of which assumptions survive model upgrades. Provider-portability is the same axis one level up (provider-independent vs provider-dependent), and the new work should be registered there.
- **Subagent spawning is the capability most likely to vary by provider — but all three current targets actually support it.** Verified (Jun 2026): Claude Code (Task), Codex CLI (`.codex/agents/` TOML, explicit spawn), and Cursor (`.cursor/agents/` md, incl. background/parallel) all have subagents. The inline fallback is therefore **defensive** — it's keyed off `capabilities.subagents` so a future provider (or a downgraded environment) without subagents still works, but on today's three targets the parallel path is available everywhere. (This corrects an earlier assumption that Cursor lacked subagents.)
- **`thoughts/` did not exist in this repo** (project-specs is the framework, not a consumer). Created `thoughts/shared/plans/` to hold this plan.

## Desired End State

A maintainer can run `./setup.sh /path/to/project --provider=codex` (or `claude`/`cursor`) and the framework installs into that provider's expected location, with model tiers mapped to that provider's models and subagent steps that gracefully fall back to inline research where subagents aren't available. The neutral source files in `agents/`, `commands/`, `skills/` remain the single source of truth and are never provider-specific.

**Verification:** Each provider's install produces a working, discoverable command set; running a research-heavy command (e.g. create_plan) produces equivalent-quality output on all three providers, differing only in whether research ran in parallel or sequentially.

## What We're NOT Doing

- **Not targeting Gemini CLI** (deferred — manifest pattern makes it a later add).
- **Not implementing the changes this session** — this is a *plan-only* deliverable: the only artifact produced now is this document. No `setup.sh`, manifest, command, or agent file is edited yet. Implementation is a separate, reviewable step. ("Plan-only" is a scope choice for this session — it does **not** drop any command or feature. All 12 core + 7 integration commands, including `research_codebase`, remain fully supported on every provider.)
- **Not changing the Claude Code experience without explicit opt-in** — `provider: "claude"` is the default and a no-flag `setup.sh` run is byte-identical to today's behavior (proven by the Phase 2 baseline diff). A user's existing workflow only changes when they choose to run `setup.sh` with `--provider=<other>` or `--update`.
- **Not building a runtime transpiler** — we use static manifests + neutral prose, not setup-time file rewriting (that was the rejected "per-provider built files" option).
- **Not removing Claude Code features** — Claude Code stays the reference; its parallel-subagent path is the fast path, not the only path.
- **Not abstracting away `tools:` frontmatter per agent** — non-Claude providers ignore unknown frontmatter, so it stays as a Claude-only hint (documented as such).
- **Not changing the three-layer architecture, anti-rationalization tables, workflow patterns, or thoughts/ convention** — these are already provider-neutral and are where most of the framework's value lives.

## Implementation Approach

Introduce a thin **provider manifest layer** that captures everything provider-specific as data, keep all command/agent *bodies* provider-neutral, and make the one un-portable capability (subagents) a config-driven fallback. Order the work so the foundation (manifests + config) lands first, then `setup.sh` consumes it, then command bodies are de-coupled, then docs and the assumptions registry are updated. Each phase is independently verifiable.

---

## Phase 1: Provider Manifest Layer + Config Extension

### Overview
Establish the data model for provider differences. Nothing consumes it yet; this phase just defines the contract.

### Changes Required:

#### 1. New `providers/` directory with one manifest per provider
**File**: `providers/claude/manifest.yaml` (and `providers/codex/manifest.yaml`, `providers/cursor/manifest.yaml`)
**Changes**: New files. Each manifest declares install target, model-tier→model mapping, and capability flags.

```yaml
# providers/claude/manifest.yaml
provider: claude
display_name: "Claude Code"
install:
  base_dir: ".claude"                 # relative to project root
  agents_subdir: "agents"             # → .claude/agents/
  commands_subdir: "commands"         # → .claude/commands/
  skills_subdir: "skills"
  settings_template: "settings.local.json"   # provider-specific perms artifact
command_invocation: "slash"           # how users invoke: slash | mention | file
models:                               # maps semantic tier → concrete model id
  planning: "opus"
  analysis: "sonnet"
  quick: "haiku"
capabilities:
  subagents: true                     # parallel autonomous subagents available
  mcp: true                           # MCP tool integration available
  tool_frontmatter: true              # honors `tools:` allowlist in frontmatter
```

```yaml
# providers/codex/manifest.yaml
# Verified against developers.openai.com/codex + github.com/openai/codex (Jun 2026).
provider: codex
display_name: "OpenAI Codex CLI"
install:
  base_dir: ".codex"                  # project config dir (config.toml, trusted projects only)
  config_format: "toml"              # Codex uses TOML, NOT yaml — config.toml
  agents_subdir: "agents"            # .codex/agents/ — subagent defs, as TOML files
  skills_subdir: ".agents/skills"    # NOTE: .agents/skills/<name>/SKILL.md, NOT .codex/skills
  commands_dest: "skills"            # custom prompts are DEPRECATED → our commands install as skills
  root_instructions: "AGENTS.md"     # global ~/.codex + project tree; 32 KiB cap
  settings_template: null            # no permissions-file equivalent; documented instead
command_invocation: "skill"          # invoked via /skills or $skill-name (not slash-prompt)
models:
  # Codex defaults to the current "recommended" model when unset — do NOT hardcode.
  # Empty = let Codex pick; users may pin a gpt-5.x id for determinism.
  planning: ""                       # e.g. "gpt-5.5" to pin
  analysis: ""
  quick: ""                          # e.g. "gpt-5.4-mini" for cheap subagent work
capabilities:
  subagents: true                    # ~/.codex/agents/ or .codex/agents/ (TOML); explicit spawn
  mcp: true                          # [mcp_servers.<name>] in config.toml
  tool_frontmatter: false
  model_pinnable: true               # model = "..." in config.toml / per-subagent
```

```yaml
# providers/cursor/manifest.yaml
# Verified against cursor.com/docs (Jun 2026).
provider: cursor
display_name: "Cursor"
install:
  base_dir: ".cursor"
  agents_subdir: "agents"            # .cursor/agents/*.md — subagent defs (md + YAML frontmatter)
  commands_subdir: "commands"        # .cursor/commands/*.md — reusable prompts, invoked with /
  skills_subdir: "skills"            # .cursor/skills/<name>/SKILL.md
  rules_subdir: "rules"              # .cursor/rules/*.mdc — MUST be .mdc, plain .md is IGNORED
  root_instructions: "AGENTS.md"     # plain-markdown alternative, also supported
  settings_template: null
  mcp_config: ".cursor/mcp.json"     # MCP config is JSON here
command_invocation: "slash"          # /command in the Agent input
models:
  # Cursor model selection is UI-only (Settings → Models). NOT pinnable via a
  # project config file for the main agent. Per-subagent `model:` frontmatter is
  # the ONLY file-configurable pin. Tiers below are advisory only.
  planning: ""
  analysis: ""
  quick: ""
capabilities:
  subagents: true                    # CORRECTED: Cursor DOES support subagents (incl. background/parallel)
  mcp: true                          # .cursor/mcp.json
  tool_frontmatter: false
  model_pinnable: false              # main-agent model is UI-only; tiers are advisory at most
```

#### 2. Extend `specs.config.example.yaml`
**File**: `specs.config.example.yaml`
**Changes**: Add a `provider` selector and a non-MCP ticket fallback. Keep existing `models:` block as the per-project override of manifest defaults.

```yaml
# --- Provider ---
# Which coding-agent provider this project targets. setup.sh reads the
# matching providers/<provider>/manifest.yaml for install + model details.
provider: "claude"                  # Options: claude, codex, cursor

# --- Ticket System Integration ---
ticket_system: "linear"
ticket_integration: "mcp"           # Options: mcp, cli, none
ticket_mcp_prefix: "mcp__linear"    # Used when ticket_integration: mcp
ticket_cli: ""                      # e.g. "linear-cli" — used when ticket_integration: cli
# ... existing ticket_* keys unchanged ...
```

### Success Criteria:

#### Automated Verification:
- [ ] All three `providers/*/manifest.yaml` files parse as valid YAML (`yq . providers/*/manifest.yaml` or equivalent)
- [ ] `specs.config.example.yaml` parses as valid YAML
- [ ] Every manifest contains the same set of top-level keys (schema consistency check)

#### Manual Verification:
- [x] Codex and Cursor install paths + capabilities verified against current provider docs (Jun 2026) — manifests above now carry verified values. See [Verified Provider Facts](#appendix-verified-provider-facts-jun-2026).
- [ ] Model fields intentionally left empty (Codex auto-selects "recommended"; Cursor model is UI-only) — confirm this matches the provider behavior at implementation time, since the `gpt-5.x` line churns fast.
- [ ] Re-confirm the two items the research could NOT pin down: (a) Codex's exact MCP tool-name namespacing surface, and (b) whether any pinned `gpt-5.x` id is still current.

**Implementation Note**: Provider facts are verified as of Jun 2026 (see appendix). The fast-moving items are model ids and MCP tool naming — re-check those against a live install before relying on them.

---

## Phase 2: `setup.sh` Reads the Manifest

### Overview
Make the installer provider-aware. It selects a manifest, installs into that provider's directories, and emits the right settings artifact.

### Changes Required:

#### 1. Add `--provider` flag and manifest loading
**File**: `setup.sh`
**Changes**: Parse `--provider=<name>` (default `claude` for backward compatibility). Read `providers/<name>/manifest.yaml` to resolve `base_dir` and subdirs instead of the hardcoded `CLAUDE_DIR`.

```bash
# Replace hardcoded CLAUDE_DIR (setup.sh:122) with manifest-driven values:
PROVIDER="${PROVIDER:-claude}"
MANIFEST="$SCRIPT_DIR/providers/$PROVIDER/manifest.yaml"
[[ -f "$MANIFEST" ]] || { print_error "Unknown provider: $PROVIDER"; exit 1; }

BASE_DIR=$(yq -r '.install.base_dir' "$MANIFEST")
AGENTS_SUBDIR=$(yq -r '.install.agents_subdir' "$MANIFEST")
COMMANDS_SUBDIR=$(yq -r '.install.commands_subdir' "$MANIFEST")
INSTALL_DIR="$TARGET_PATH/$BASE_DIR"
```

#### 2. Generalize the copy/symlink blocks
**File**: `setup.sh`
**Changes**: The two near-identical blocks at [setup.sh:142-174](../../../setup.sh#L142-L174) become a helper called with `(source_subdir, target_subdir)` from the manifest. Emit `root_instructions` (e.g. Codex `AGENTS.md`) and `settings_template` only when the manifest defines them.

#### 3. Preserve backward compatibility
**File**: `setup.sh`
**Changes**: With no `--provider`, behavior is identical to today (`claude`, installs to `.claude/`). Update `show_help` to document `--provider`.

#### 4. ⚠️ Format translation for Codex (NEW — surfaced by Phase 1 research)
**File**: `setup.sh` + a small per-provider transform step
**Changes**: Plain file-copy works for **Claude** (md→md) and largely for **Cursor** (md commands/agents→md). It does **NOT** work for **Codex**, where the research found:
- Custom prompts are **deprecated** → our `commands/*.md` must install as **Skills**: `.agents/skills/<command-name>/SKILL.md` with `name` + `description` frontmatter.
- Subagents are defined as **TOML** in `.codex/agents/`, not markdown — our `agents/*.md` need a frontmatter→TOML transform (name, description, developer_instructions) or to also be shipped as skills.

This means the installer needs a **per-provider transform**, not just a path remap. Decision for implementation: either (a) a thin transform in `setup.sh` (wrap each command body in a generated `SKILL.md`, emit a TOML stub per agent), or (b) commit pre-built Codex artifacts under `providers/codex/`. **Recommendation: (a)** — keeps the neutral `commands/`/`agents/` as the single source of truth and matches the "manifests describe, installer adapts" architecture. This is the one place the installer does light generation. Flag for the reviewer: this enlarges Phase 2 beyond a pure path-remap. Cursor needs no transform for commands/agents/skills; only `.cursor/rules/` (if used) requires `.mdc` + frontmatter, which the framework does not currently emit, so rules are out of scope unless added later.

### Success Criteria:

#### Automated Verification:
- [ ] `./setup.sh --help` shows the new `--provider` flag
- [ ] `./setup.sh /tmp/test-claude --provider=claude` produces a `.claude/` tree identical to the current installer's output (diff against a baseline)
- [ ] `./setup.sh /tmp/test-codex --provider=codex` produces `.codex/agents/` (TOML), `.agents/skills/` for commands-as-skills, and a project-root `AGENTS.md`
- [ ] `./setup.sh /tmp/test-cursor --provider=cursor` produces `.cursor/agents/`, `.cursor/commands/`, `.cursor/skills/` (and `.cursor/rules/*.mdc` if rules are emitted — must be `.mdc`, not `.md`)
- [ ] Unknown `--provider=foo` exits non-zero with a clear error
- [ ] `yq` presence is checked via the existing `check_required_command` pattern

#### Manual Verification:
- [ ] Installed Codex layout is actually discovered by Codex CLI in a scratch project
- [ ] Installed Cursor rules are actually discovered by Cursor in a scratch project
- [ ] No `--provider` flag still works for existing Claude Code users (no regression)

**Implementation Note**: Pause after this phase for manual confirmation that each provider discovers its installed files before touching command bodies.

---

## Phase 3: De-couple Command & Agent Bodies

### Overview
Remove hard Claude-isms from the prose: capability-gate subagent spawning, neutralize tool-name and slash-command references, and route models through semantic tiers.

### Changes Required:

#### 1. Capability-gated subagent fallback (5 core commands)
**File**: `commands/core/create_plan.md`, `implement_plan.md`, `validate_plan.md`, `spec.md`, `research_codebase.md`
**Changes**: Wrap every "spawn the X agent" instruction with a capability gate. The agent `.md` files already contain full instructions, so the inline path just follows them sequentially.

```markdown
**Research the codebase.** If your environment supports parallel subagents
(`capabilities.subagents: true`), spawn the **codebase-locator** and
**codebase-analyzer** agents concurrently as described below.

If subagents are **not** available, perform the same research yourself, inline
and sequentially, following the procedures in `agents/codebase-locator.md` and
`agents/codebase-analyzer.md`: first locate the relevant files, then analyze how
the current implementation works. The output must be equivalent — only the
execution (parallel vs. sequential) differs.
```

Apply the same gate to [commands/core/create_plan.md:110-130](../../../commands/core/create_plan.md#L110-L130) and the "Sub-task Spawning Best Practices" section ([create_plan.md:410-440](../../../commands/core/create_plan.md#L410-L440)), reframing it as "when subagents are available."

#### 2. Neutralize tool-name references in prose
**File**: all command/agent bodies that name tools imperatively
**Changes**: Prefer capability language with the tool as a parenthetical hint, e.g. "read the file fully (Read tool, no limit/offset)" → keep the instruction meaningful where the named tool is absent. Leave `tools:` frontmatter intact (Claude honors it; others ignore it — documented in Phase 4).

#### 3. Route models through semantic tiers
**File**: command + agent frontmatter (~19 files) — see [the model: inventory in Current State](#current-state-analysis)
**Changes**: Replace literal `model: opus` with the semantic tier the manifest/config resolves: `model: planning` (or `analysis`/`quick`). Document the tier vocabulary once. Claude Code consumers map tiers via `models:` in config; the manifest provides per-provider defaults.

```yaml
# before
model: opus
# after
model: planning        # resolved via providers/<p>/manifest.yaml + specs.config.yaml models:
```

**Tier mapping per component** (so resolution is unambiguous at implementation time):
- `planning` ← currently `model: opus` (create_plan, spec, debug, etc.)
- `analysis` ← currently `model: sonnet` (all 6 agents, implement_plan, research_codebase, etc.)
- `quick` ← currently `model: haiku` (if any)

**How a user changes which model a workflow uses** (the "I want research on opus" case): research agents are `analysis`-tier, so the user sets `analysis: "opus"` in their `specs.config.yaml` `models:` block — one line, applied to every analysis-tier command and agent. No file edits needed. On Claude Code, leaving the config at its defaults resolves every tier back to the same model the literal frontmatter used today, so behavior is unchanged until the user deliberately retunes a tier.

#### 4. Slash-command cross-references → invocation-neutral
**File**: command bodies and README that say "Run `/create_plan`"
**Changes**: Introduce a single phrasing convention, e.g. "run the **create_plan** workflow", so it reads correctly whether invoked by slash (Claude/Cursor), file (Codex), or mention.

#### 5. MCP ticket calls honor `ticket_integration` (7 integration commands)
**File**: `commands/integrations/*.md` (all 7)
**Changes**: Replace direct `{ticket_mcp_prefix}` usage with "use the configured ticket integration": if `ticket_integration: mcp`, use `{ticket_mcp_prefix}__*`; if `cli`, shell out via `{ticket_cli}`; if `none`, skip/ask.

### Success Criteria:

#### Automated Verification:
- [ ] No command body contains an un-gated "spawn … agent" instruction (grep for spawn/Task without a neighboring capability gate)
- [ ] No frontmatter contains a literal `model: opus|sonnet|haiku` (grep returns only semantic tiers)
- [ ] All `{ticket_mcp_prefix}` usages are inside a `ticket_integration` conditional (grep audit across the 7 files)
- [ ] All command/agent markdown still parses (frontmatter valid)

#### Manual Verification:
- [ ] create_plan produces an equivalent-quality plan on Cursor (inline path) vs Claude Code (parallel path)
- [ ] A ticket command works against the `cli` and `none` integration modes, not just `mcp`
- [ ] Tier-based model selection resolves to sensible models on each provider
- [ ] Prose still reads naturally for a Claude Code user (no regression in the reference experience)

**Implementation Note**: This is the largest phase by file count (~25 files touched). Pause after for confirmation that the reference (Claude Code) experience is unchanged before updating docs.

---

## Phase 4: Documentation & Model-Assumptions Registry

### Overview
Make the new capability discoverable and record the provider-portability decisions where the framework already records model-portability decisions.

### Changes Required:

#### 1. README provider section
**File**: `README.md`
**Changes**: Retitle away from "Claude Code Spec Framework" to a provider-neutral title with Claude Code as reference. Add a "Supported Providers" section and `--provider` usage. Document that `tools:` frontmatter and slash syntax are Claude-Code-specific niceties that degrade gracefully.

#### 2. New provider-portability convention doc
**File**: `conventions/provider-portability.md` (new)
**Changes**: Document the manifest schema, capability flags, the subagent fallback contract, the semantic-tier model vocabulary, and how to add a 4th provider (the Gemini path).

#### 3. Extend the model-assumptions registry
**File**: `conventions/model-assumptions.md`
**Changes**: Add a parallel "Provider-Dependent Patterns" table (subagent spawning, MCP availability, `tools:` gating, install path, invocation syntax) alongside the existing model-dependent table, so the same upgrade-time review covers provider drift. Add manifests to the "Model-Independent Patterns" list as a structural separation.

#### 4. Per-provider example config
**File**: `examples/<provider>/specs.config.yaml`
**Changes**: Add a `provider:`-set example for codex and cursor mirroring the existing example structure.

### Success Criteria:

#### Automated Verification:
- [ ] All internal doc links resolve (link-check across `conventions/`, `README.md`)
- [ ] New example configs parse as valid YAML and set `provider:`

#### Manual Verification:
- [ ] A new user can read the README + provider-portability doc and successfully install on a non-Claude provider
- [ ] The model-assumptions registry now answers "what do I re-check when adding/upgrading a provider?"

---

## Testing Strategy

### Unit / Static checks:
- YAML validity for all manifests, example configs, and frontmatter.
- Grep-based audits: no literal model names, no un-gated subagent spawns, no un-conditional MCP prefixes.
- Manifest schema consistency (same keys across providers).

### Integration scenarios:
- Install into three scratch projects (`--provider=claude|codex|cursor`); confirm each provider discovers its files.
- Run create_plan end-to-end on Claude Code (parallel path) and Cursor (inline path); compare output quality.
- Run a ticket command under `mcp`, `cli`, and `none` integration modes.

### Manual testing steps:
1. `./setup.sh /tmp/specs-claude --provider=claude` → diff `.claude/` against current-installer baseline (expect identical).
2. `./setup.sh /tmp/specs-cursor --provider=cursor` → open in Cursor, invoke a `/command`, confirm it's discovered (subagents available, so parallel path runs).
3. `./setup.sh /tmp/specs-codex --provider=codex` → confirm `AGENTS.md` + `.codex/agents/` + `.agents/skills/` discovered by Codex.
4. Edge: `./setup.sh /tmp/x --provider=bogus` → clear error, non-zero exit.

## Performance Considerations

All three current targets (Claude, Codex, Cursor) support subagents, so the **parallel** research path is available everywhere — there is no expected per-provider performance penalty on the current target set. The **inline sequential fallback** only engages on a hypothetical future provider (or a downgraded environment) where `capabilities.subagents: false`. When it does engage, it's slower and uses more single-context tokens but produces equivalent quality if the inline procedure follows the agent `.md` instructions. Accepted, documented trade-off — not a defect.

## Migration Notes

- **Backward compatible by default.** Existing Claude Code users who pull this update and re-run `setup.sh` with no flag get identical behavior; `provider: "claude"` is the default.
- **Existing installs:** the `model: opus → model: planning` frontmatter change requires that consumers have a `models:` block (already present in the example config since v1.0.0). Document as a minor-version note; if any project lacks it, manifest defaults cover it.
- **Versioning:** this is a backward-compatible feature addition to the config schema and command interface → **minor** version bump (e.g. 1.1.0), per the README's SemVer policy. The `model:` frontmatter vocabulary change is the one item to call out in CHANGELOG as potentially breaking for projects that pinned literal models.

## References

- Audited coupling points: [Current State Analysis](#current-state-analysis) (this doc)
- Installer to modify: [setup.sh:122](../../../setup.sh#L122), [setup.sh:142-174](../../../setup.sh#L142-L174)
- Config to extend: [specs.config.example.yaml:22](../../../specs.config.example.yaml#L22), [specs.config.example.yaml:40-43](../../../specs.config.example.yaml#L40-L43)
- Subagent-coupled commands: [commands/core/create_plan.md:57-62](../../../commands/core/create_plan.md#L57-L62), [create_plan.md:110-130](../../../commands/core/create_plan.md#L110-L130)
- Registry to extend: [conventions/model-assumptions.md](../../../conventions/model-assumptions.md)
- Related convention: [conventions/three-layer-architecture.md](../../../conventions/three-layer-architecture.md)

---

## Appendix: Verified Provider Facts (Jun 2026)

Researched against official docs. The manifests above encode these. Re-verify the items marked ⚠️ (they churn) before implementation.

### OpenAI Codex CLI
| Concern | Value | Source |
|---|---|---|
| Instructions file | `AGENTS.md` (global `~/.codex/` + project tree; `AGENTS.override.md` wins; 32 KiB cap) | developers.openai.com/codex/guides/agents-md |
| User config | `~/.codex/config.toml` (**TOML**, overridable via `CODEX_HOME`) | developers.openai.com/codex/config-reference |
| Project config | `.codex/config.toml` (**trusted projects only**) | same |
| Reusable prompts | **DEPRECATED** → use **Skills**: `.agents/skills/<name>/SKILL.md` (note `.agents/`, not `.codex/`); also `~/.agents/skills`, `/etc/codex/skills` | developers.openai.com/codex/skills |
| Subagents | **Yes** — TOML defs in `~/.codex/agents/` or `.codex/agents/` (`name`, `description`, `developer_instructions`); explicit spawn | developers.openai.com/codex/subagents |
| MCP | `[mcp_servers.<name>]` in `config.toml`; `codex mcp add …` | developers.openai.com/codex/mcp |
| Models ⚠️ | Versioned `gpt-5.x` line (`gpt-5.5` newest recommended, `gpt-5.4`, `gpt-5.4-mini`); **default is "recommended" auto-tracking — do NOT hardcode** | developers.openai.com/codex/models |
| Tool-frontmatter allowlist | No `tools:` gating like Claude's | — |
| ⚠️ Not confirmable | exact MCP tool-name namespacing; literal default model string | research flagged |

### Cursor
| Concern | Value | Source |
|---|---|---|
| Project rules | `.cursor/rules/*.mdc` (**`.mdc` required — plain `.md` is ignored**; frontmatter: `description`, `globs`, `alwaysApply`) | cursor.com/docs/context/rules |
| Simple instructions | `AGENTS.md` (root/nested, plain markdown) | same |
| Legacy `.cursorrules` | **Deprecated / ignored in Agent mode — do NOT write it** | forum.cursor.com bug reports |
| Commands | `.cursor/commands/*.md` (plain md, no frontmatter; invoke with `/`) — since Cursor 1.6 | cursor.com/changelog/1-6 |
| Skills | `.cursor/skills/<name>/SKILL.md` (`name`, `description`, `paths`) | cursor.com/docs/skills |
| Subagents | **Yes** — `.cursor/agents/*.md` (YAML frontmatter: `name`, `description`, `model`, `readonly`, `is_background`); foreground blocks, background runs parallel | cursor.com/docs/context/subagents |
| MCP | `.cursor/mcp.json` (project) / `~/.cursor/mcp.json` (global); `mcpServers` object | cursor.com/docs/context/mcp |
| Models | **UI-only** (Settings → Models); **not file-pinnable** for main agent — only per-subagent `model:` frontmatter | cursor.com/help/models-and-usage/available-models |

### What changed vs. the pre-research plan
1. **Cursor has subagents** (was assumed false) → the inline fallback is defensive, not load-bearing for current targets.
2. **Codex deprecated prompts → Skills**, and uses **TOML** for config/agents → installer needs a per-provider *transform* for Codex, not just a path remap (new Phase 2 item #4).
3. **Model fields left empty** for Codex (auto-recommended) and Cursor (UI-only) rather than placeholder ids.
4. Cursor rules require **`.mdc`**, a format the framework doesn't currently emit → rules deferred.
