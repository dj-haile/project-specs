# project-specs — Claude Code Spec Framework

**project-specs** is a three-layer architecture for Claude Code projects that standardizes how agents orchestrate commands, which in turn invoke reusable skills. It provides a structured, parameterized approach to code analysis, planning, implementation, and validation workflows across any codebase, with first-class support for ticket systems, branch workflows, and cross-session persistence.

## Quick Start

1. **Clone or link this directory into your project:**
   ```bash
   git clone https://github.com/anthropics/project-specs <your-project>/.claude-specs
   ```

2. **Run setup.sh to initialize:**
   ```bash
   ./.claude-specs/setup.sh
   ```

3. **Configure specs.config.yaml:**
   ```bash
   cp .claude-specs/specs.config.example.yaml ./specs.config.yaml
   # Edit with your project details
   ```

## Architecture Overview

project-specs is built on three tightly coupled layers:

- **Agents** (agents/) — Orchestrators that read specs.config.yaml and dispatch work to commands. Six standard agents handle codebase analysis, pattern discovery, thought management, and web research.
- **Commands** (commands/) — Reusable workflows that compose skills and enforce consistent patterns. 11 core commands (create_plan, implement_plan, validate_plan, etc.) plus 7 integration commands for ticket systems and team workflows.
- **Skills** (skills/) — Atomic, reusable operations (file search, code review, test execution) invoked by commands. Skills are versioned and namespaced.

## Available Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `create_plan` | Analyze codebase and create structured implementation plan |
| `iterate_plan` | Refine an existing plan based on new constraints or findings |
| `research_codebase` | Deep-dive analysis of specific patterns, modules, or architecture decisions |
| `implement_plan` | Execute implementation steps with validation checkpoints |
| `validate_plan` | Run tests, linting, type checks against plan deliverables |
| `commit` | Commit changes with conventional commit messages and co-author attribution |
| `describe_pr` | Generate pull request title and body from commit history |
| `debug` | Reproduce and analyze runtime errors or test failures |
| `create_handoff` | Package current context for another Claude session |
| `resume_handoff` | Load prior handoff context and continue work |
| `local_review` | Review changes against style guide and best practices |

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

## Configuration

All parameterization lives in **specs.config.yaml** at your project root. Key parameters:

- **project_name** — Human-readable project identifier
- **thoughts_directory** — Enable cross-session persistence (true/false)
- **ticket_system** — Integration target (linear, jira, github-issues)
- **ticket_mcp_prefix** — MCP prefix for ticket system (e.g., mcp__linear)
- **ticket_id_pattern** — Regex for ticket IDs (e.g., API-\\d+)
- **branch_prefix** — Prefix for feature branches (e.g., feat/)
- **commit_style** — Commit convention (conventional, freeform)
- **models** — Model assignment (planning=opus, analysis=sonnet, quick=haiku)

See [specs.config.example.yaml](./specs.config.example.yaml) for all available options.

Example configs for common project types are in the [examples/](./examples/) directory.

## Thoughts Directory

If **thoughts_directory: true** in your config, project-specs creates and manages a **thoughts/** directory for cross-session persistence. Commands and agents log decisions, analysis results, and context to this directory so future Claude sessions can access prior findings without re-analyzing.

See [conventions/thoughts-directory.md](./conventions/thoughts-directory.md) for structure and best practices.

## Creating Custom Skills

Skills are reusable operations that commands invoke. To create a new skill:

1. Create a directory under **skills/yourname/**
2. Add a **SKILL.md** frontmatter file with metadata (name, description, inputs, outputs)
3. Implement logic in your skill's command or Python script
4. Call from commands via the standard skill interface

See [skills/_template/](./skills/_template/) for a complete example and [SKILL.md spec](./SKILL.md.spec).

## Workflow Examples

Common workflows are documented in [conventions/workflow-patterns.md](./conventions/workflow-patterns.md):

- **Ticket-to-Code** — From ticket creation to merged PR
- **Iterative Planning** — Multi-round refinement before implementation
- **Debugging in Production** — Rapid error reproduction and fix
- **Codebase Onboarding** — New team member analysis and context-building
- **Cross-Session Handoff** — Pausing and resuming long-running tasks

## Versioning

project-specs follows [Semantic Versioning](https://semver.org/). Breaking changes to the specs.config.yaml schema or agent/command interfaces will increment the major version.

Current version: **1.0.0**

## License

MIT
