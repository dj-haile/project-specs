# project-specs — Provider-Agnostic Spec Framework

**project-specs** is a three-layer architecture for AI coding-agent projects that standardizes how agents orchestrate commands, which in turn invoke reusable skills. It provides a structured, parameterized approach to code analysis, planning, implementation, and validation workflows across any codebase, with first-class support for ticket systems, branch workflows, and cross-session persistence.

**Claude Code is the reference implementation.** The same neutral source also installs to **OpenAI Codex CLI** and **Cursor** via `setup.sh --provider=<name>` — see [Supported Providers](#supported-providers) and [conventions/provider-portability.md](./conventions/provider-portability.md).

## Quick Start

### Prerequisites

`setup.sh` reads provider manifests (`providers/<name>/manifest.yaml`) using a
small embedded Python helper, so the installer needs:

- **bash** (the install script)
- **python3** with **PyYAML** — present on most systems; install PyYAML if missing:
  ```bash
  python3 -m pip install pyyaml
  ```
  (The installer exits with this exact hint if PyYAML is not found.)

No `yq` or other tools are required. These are install-time only — the framework
itself (commands, agents) has no runtime dependency on them.

### Install

1. **Get a copy of `setup.sh`.** Either clone the repo:

   ```bash
   git clone https://github.com/dj-haile/project-specs ~/.project-specs
   ```

   or skip the clone entirely and let the installer fetch its own source with
   `--from` (step 2). You only need `setup.sh` and `scripts/` on disk.

2. **Run setup.sh to install into your project:**
   ```bash
   ~/.project-specs/setup.sh /path/to/your-project                 # Claude Code (default)
   ~/.project-specs/setup.sh /path/to/your-project --provider=codex   # OpenAI Codex CLI
   ~/.project-specs/setup.sh /path/to/your-project --provider=cursor  # Cursor

   # No clone on this machine? Point at the repo instead:
   ./setup.sh /path/to/your-project --from=https://github.com/dj-haile/project-specs
   ```

   The installer copies `agents/`, `commands/`, and the `conventions/` they
   reference into the provider's location, writes a `specs.config.yaml` at your
   project root (with `provider` pre-set), and optionally creates a `thoughts/`
   directory. For Codex it transforms commands into Skills and agents into TOML;
   see [Supported Providers](#supported-providers). It also writes
   `.project-specs.json`, which records what it installed so later runs can
   update it and leave your edits alone — see
   [Updating an install](#updating-an-install).

3. **Customize specs.config.yaml** (created at your project root by setup.sh):
   ```bash
   $EDITOR /path/to/your-project/specs.config.yaml
   ```
   Set `provider`, map model tiers under `models:`, and choose
   `ticket_integration` (`mcp`/`cli`/`none`). See
   [conventions/provider-portability.md](./conventions/provider-portability.md).

### Updating an install

Every install records where it came from, at `.project-specs.json` in your
project root. That lets the installer fetch its own source, so you never need to
remember where your clone of project-specs lives — or have one at all.

**Am I behind?**

```bash
/path/to/setup.sh /path/to/your-project --check
```

It fetches the source recorded at install time and reports the revision your
project is on, how far behind it is, and the change-log entries added since.
Exit status is 1 when a newer revision exists and 0 when you are current, so CI
can gate on it.

**Bring it up to date:**

```bash
/path/to/setup.sh /path/to/your-project --update
```

The update fetches before it copies. If the source cannot be reached, nothing in
your project changes.

**Files you edited are kept.** The record holds a fingerprint of every file the
installer wrote. A file whose content no longer matches is left alone, and the
installer lists it under "Kept your local changes" when it finishes. Your
`specs.config.yaml` is never overwritten.

**Pin a project to one version:**

```bash
/path/to/setup.sh /path/to/your-project --from=https://github.com/dj-haile/project-specs --ref=v1.0.0
```

A `--ref` naming a branch follows that branch. A tag or a revision pins the
install: later updates hold it there, and `--check` tells you a newer revision
exists without moving you. Move it by naming a different reference:
`--update --ref=main`.

**Install on a machine with no clone:**

```bash
/path/to/setup.sh /path/to/your-project --from=https://github.com/dj-haile/project-specs
```

The source is cached under `$XDG_CACHE_HOME/project-specs` (override with
`SPECS_CACHE`), and one revision is exported for the install.

From inside an agent session, `/specs_update` runs the check, reports what
changed in plain language, and applies the update when you ask for it.

### What to put in .gitignore

The framework is local tooling for your project, not part of what your project
ships, so keep it out of your project's git history. Add these:

```gitignore
# project-specs framework (local tooling)
.claude/
.project-specs.json
specs.config.yaml
standards/
thoughts/
pr_description.md
```

Adjust the first line for your provider (`.cursor/`, or `.codex/` plus
`.agents/` and `AGENTS.md`). Keep `thoughts/` tracked instead if you want plans
and handoffs shared with your team — see [Thoughts Directory](#thoughts-directory).

### Install the read-only agents as skills (any agent tool)

The **read-only agents** — the six research agents (`codebase-locator`,
`codebase-pattern-finder`, `codebase-analyzer`, `thoughts-locator`,
`thoughts-analyzer`, `web-search-researcher`) plus `plan-skeptic` — are also
published as standalone Skills under `skills/.curated/`, installable into 70+
agent tools via the [vercel-labs/skills](https://github.com/vercel-labs/skills)
CLI:

```bash
npx skills add dj-haile/project-specs
```

This is a lightweight alternative to `setup.sh` for the agents only — it does
**not** install the commands (which are framework-coupled and expect
`specs.config.yaml` + `conventions/`) and does not carry model-tier selection.
For the full framework, use `setup.sh` above. The skills are generated from the
agent sources by `scripts/build_skills.py` (CI enforces they stay in sync).

## Architecture Overview

project-specs is built on three tightly coupled layers:

- **Agents** (agents/) — Orchestrators that read specs.config.yaml and dispatch work to commands. Seven standard agents handle codebase analysis, pattern discovery, thought management, web research, and adversarial plan review.
- **Commands** (commands/) — Reusable workflows that compose skills and enforce consistent patterns. 14 core commands (create_plan, implement_plan, validate_plan, etc.) plus 7 integration commands for ticket systems and team workflows.
- **Skills** (skills/) — Atomic, reusable operations (file search, code review, test execution) invoked by commands. Skills are versioned and namespaced.

## Supported Providers

A single neutral source (`agents/`, `commands/`, `skills/`) installs to each provider. Per-provider details live in `providers/<name>/manifest.yaml`; `setup.sh --provider=<name>` reads it.

| Provider | Install location | Format | Subagents | Model selection |
|----------|------------------|--------|-----------|-----------------|
| **Claude Code** (reference) | `.claude/` | markdown (copy) | yes | tiers → opus/sonnet/haiku |
| **OpenAI Codex CLI** | `.codex/agents/` + `.agents/skills/` + `AGENTS.md` | transformed (Skills + TOML) | yes | auto-recommended (`gpt-5.x`) |
| **Cursor** | `.cursor/` | markdown (copy) | yes | UI-only (not file-pinnable) |

Two coupling points degrade gracefully by convention: subagent spawning ([subagent-fallback](./conventions/subagent-fallback.md)) and ticket integration ([ticket-integration](./conventions/ticket-integration.md)). `--provider=claude` (the default) is byte-identical to the framework's original behavior, so existing Claude Code installs are unaffected unless you opt in. Full details: [conventions/provider-portability.md](./conventions/provider-portability.md).

## Available Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `spec` | Define requirements and acceptance criteria before planning |
| `create_plan` | Analyze codebase and create structured implementation plan |
| `iterate_plan` | Refine an existing plan based on new constraints or findings |
| `research_codebase` | Deep-dive analysis of specific patterns, modules, or architecture decisions |
| `implement_plan` | Execute implementation steps with validation checkpoints |
| `validate_plan` | Run tests, linting, type checks against plan deliverables |
| `commit` | Commit changes with conventional commit messages and co-author attribution |
| `stack_pr` | Decompose a large change into a stack of dependency-ordered, reviewable branches |
| `describe_pr` | Generate pull request title and body from commit history |
| `check_standards` | Check a plan, diff, or PR against the extracted standards registry |
| `debug` | Reproduce and analyze runtime errors or test failures |
| `create_handoff` | Package current context for another Claude session |
| `resume_handoff` | Load prior handoff context and continue work |
| `local_review` | Review changes against style guide and best practices |
| `specs_update` | Report whether the installed framework is out of date, and upgrade it |

### Integration Commands

| Command | Description |
|---------|-------------|
| `ticket_plan` | Create implementation plan from ticket/issue |
| `ticket_research` | Research ticket context and add analysis to ticket |
| `ticket_impl` | Implement ticket and auto-update status |
| `ticket_oneshot` | Plan, implement, validate, and commit in one pass |
| `ticket_manage` | Bulk manage ticket lifecycle (move, assign, close) |
| `founder_mode` | Rapid workflow: research, plan, implement, validate, commit in one session |
| `create_worktree` | Create isolated git worktree for parallel work |

## Available Agents

| Agent | Description |
|-------|-------------|
| `codebase-analyzer` | Analyzes project structure, dependencies, and architecture patterns |
| `codebase-locator` | Searches codebase for files, functions, classes by name or pattern |
| `codebase-pattern-finder` | Discovers recurring patterns, conventions, and code anti-patterns |
| `thoughts-analyzer` | Analyzes thought files for insights and cross-session learning |
| `thoughts-locator` | Searches thought directory for relevant prior decisions and context |
| `web-search-researcher` | Researches third-party libraries, frameworks, and best practices |
| `plan-skeptic` | Adversarial fresh-context reviewer of an implementation plan before coding; returns objections by severity (used by `validate_plan`) |

## Configuration

All parameterization lives in **specs.config.yaml** at your project root. Key parameters:

- **provider** — Target coding agent (claude, codex, cursor); default claude
- **project_name** — Human-readable project identifier
- **thoughts_directory** — Enable cross-session persistence (true/false)
- **ticket_system** — Integration target (linear, jira, github-issues)
- **ticket_integration** — How to reach the ticket system (mcp, cli, none)
- **ticket_mcp_prefix** — MCP prefix when ticket_integration=mcp (e.g., mcp__linear)
- **ticket_id_pattern** — Regex for ticket IDs (e.g., API-\\d+)
- **branch_prefix** — Prefix for feature branches (e.g., feat/)
- **commit_style** — Commit convention (conventional, freeform)
- **models** — Semantic tier → model map (planning/analysis/quick); see [provider-portability](./conventions/provider-portability.md)

See [specs.config.example.yaml](./specs.config.example.yaml) for all available options.

Example configs for common project types are in the [examples/](./examples/) directory.

## Thoughts Directory

If **thoughts_directory: true** in your config, project-specs creates and manages a **thoughts/** directory for cross-session persistence. Commands and agents log decisions, analysis results, and context to this directory so future Claude sessions can access prior findings without re-analyzing.

See [conventions/thoughts-directory.md](./conventions/thoughts-directory.md) for structure and best practices.


## Anti-Rationalization Tables

Core commands (`create_plan`, `implement_plan`, `validate_plan`) include **"Common Shortcuts to Avoid"** tables — pre-written rebuttals to common excuses agents produce to skip workflow steps. LLMs are skilled at rationalization; these tables counter that by placing the rebuttal directly in the command file where the shortcut would occur.

Each table lists 3–4 excuse/rebuttal pairs specific to that command's workflow. For example, `implement_plan` includes rebuttals for combining phases, skipping verification on small changes, and touching files outside the plan's scope.

These tables are based on patterns identified in [Addy Osmani's Agent Skills research](https://addyosmani.com/blog/agent-skills/) and connect to the broader principle that behavioral contracts outperform prose directives for agent compliance.

## Validation & CI

The framework validates itself. `scripts/validate.py` checks every agent and command for valid frontmatter, semantic model tiers (never literal model names), required behavioral sections, parseable configs and manifests, and unbroken cross-references:

```bash
python3 scripts/validate.py
```

The framework also evals its own routing. `scripts/run_evals.py` builds a stemmed TF‑IDF index over every command/agent `name` + `description` and asserts that natural user phrasings route to the right command (positive cases in top‑_k_), don't steal a neighbor's prompt (negative cases), and that no two descriptions collide. It's deterministic (Python + PyYAML only — no Node, no network) so it runs in CI unchanged:

```bash
python3 scripts/run_evals.py
# Debug a phrasing:
python3 scripts/run_evals.py --explain "create a plan for the top ticket"
```

A failing eval means a description needs sharpening, not that the test is wrong — see [evals/README.md](./evals/README.md).

CI (`.github/workflows/validate.yml`) runs `validate.py` and `run_evals.py` on every pull request, plus an installer smoke test that runs `setup.sh --yes` against a fresh project for all three providers and asserts the expected install layout. This protects the core promise — one neutral source installs everywhere — automatically.

CI also keeps two generated files honest: `skills/.curated/` (regenerate with `python3 scripts/build_skills.py`) and `standards/statements.json` (regenerate with `python3 standards/extractor.py`). If a PR edits the sources without regenerating the file, the matching drift job fails it.

For scripted or CI installs, `setup.sh` accepts `--yes` to run non-interactively (overwrites an existing install, skips optional prompts).

## Standards Enforcement

Agents check plans, implementations, and PRs against the rules written in `conventions/`. You write a rule once, as a sentence a person can read, and the commands apply it at each step of the workflow where it matters. This is the model Cloudflare uses (they call theirs the Codex) to enforce engineering standards with AI.

It works in three parts:

1. **Conventions carry the rules.** To make a convention enforceable, add three metadata lines at the top of its file (`domain`, `status`, `sdlc_stage`) and write each rule as a sentence with a bold **MUST** or **SHOULD** — the RFC 2119 convention for requirement keywords. For example: "Engineers **MUST** stack PRs when the diff exceeds 1,000 lines." The doc stays readable prose. The bold keywords tell the extractor which sentences are rules.
2. **The extractor makes the rules machine-readable.** `standards/extractor.py` reads the enforceable conventions and writes `standards/statements.json`: one entry per MUST/SHOULD sentence. Each entry carries the rule's text, its source file, its workflow stage, and a short ID built from the rule's own words, so the ID doesn't change when the rest of the doc does. The file is committed to git, so agents read it directly instead of running the extractor.
3. **Commands check the rules at the point of work.** `/check_standards` filters the registry to the stage you're at and reports violations by severity. You can run it directly, but mostly it runs for you. `/create_plan` surfaces planning findings as recommendations. `/validate_plan` fails validation when the implementation breaks an enforced MUST rule. `/describe_pr` warns before creating a PR that breaks a review rule.

A new standard starts as `approved`: its findings show up, but nothing blocks. Once the team has absorbed it, promote it to `enforced`, where breaking a MUST rule actually stops work. Each project chooses how hard each rule bites through the `standards:` block in `specs.config.yaml`, and any change can opt out of a specific rule by recording a waiver with a reason. The full lifecycle — proposing, promoting, waiving, ownership — lives in [conventions/standards-governance.md](./conventions/standards-governance.md).

## Definition of Done

[references/definition-of-done.md](./references/definition-of-done.md) is a standing, project-wide checklist that every change must clear — distinct from per-task acceptance criteria. `validate_plan` and `local_review` apply it as their final gate. Projects can extend it via a `definition_of_done` key in specs.config.yaml.

## Creating Custom Skills

Skills are reusable operations that commands invoke. To create a new skill:

1. Create a directory under **skills/yourname/**
2. Add a **SKILL.md** frontmatter file with metadata (name, description, inputs, outputs)
3. Implement logic in your skill's command or Python script
4. Call from commands via the standard skill interface

See [skills/_template/SKILL.md](./skills/_template/SKILL.md) for a complete annotated example.

## Workflow Examples

Common workflows are documented in [conventions/workflow-patterns.md](./conventions/workflow-patterns.md):

- **Spec-First** — Requirements → plan → implement → validate
- **Iterative Planning** — Multi-round refinement before implementation
- **Debugging in Production** — Rapid error reproduction and fix
- **Codebase Onboarding** — New team member analysis and context-building
- **Cross-Session Handoff** — Pausing and resuming long-running tasks

## Versioning

project-specs follows [Semantic Versioning](https://semver.org/). Breaking changes to the specs.config.yaml schema or agent/command interfaces will increment the major version.

Current version: **1.0.0**

## License

MIT

## Usage Guide

For detailed examples showing how to use all features — including the spec-first workflow, anti-rationalization tables, scope discipline, and verification gates — see [examples/usage-guide.md](./examples/usage-guide.md).
