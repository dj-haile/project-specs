# Three-Layer Architecture

The project-specs framework organizes Claude Code automation into three distinct layers: agents, commands, and skills. Each layer has a specific role in the workflow.

## Layer Definitions

### Agents
**Reusable research and analysis specialists** that perform focused, read-only tasks.

- **Role**: Spawn as sub-tasks from commands to investigate, analyze, or gather information
- **Scope**: Single, well-defined responsibility (find files, analyze code, locate patterns, search web)
- **Output**: Findings, analysis, or data that commands consume
- **Capabilities**: Limited tool set specific to their role
- **Reusability**: Designed to be used across multiple commands and projects

**Agent Structure** (YAML frontmatter + instructions):
```yaml
---
name: codebase-analyzer
description: Analyzes codebase structure and identifies architectural patterns
tools:
  - glob
  - grep
  - read
model: sonnet
---
```

### Commands
**Workflow orchestrators** invoked by users through slash commands.

- **Role**: Primary user interface; orchestrate multi-step workflows
- **Trigger**: User calls via `/command_name` (e.g., `/create_plan`, `/commit`)
- **Responsibilities**:
  - Read project configuration
  - Spawn agents for sub-tasks
  - Interact with users (ask questions, present options)
  - Coordinate workflow state
  - Produce artifacts (plans, commits, PRs)
- **Modes**: Interactive (user-guided) or CI-mode (automated, non-interactive)
- **Configuration**: Defined in `commands/` directory with YAML frontmatter

**Command Structure** (YAML frontmatter + instructions):
```yaml
---
description: Creates an implementation plan for a feature or bug fix
model: opus
---
```

### Skills
**Domain-specific capabilities** with rich prompts and optional supporting code.

- **Role**: Encapsulate specialized knowledge (linting rules, testing patterns, deployment processes)
- **Scope**: Project-specific methodologies and conventions
- **Storage**: Live in their own directories with a `SKILL.md` file
- **Framework vs Project**:
  - Framework provides templates only
  - Actual skills are project-specific
- **Reusability**: Used by commands via skill references in prompts

**Skill Structure** (Directory-based):
```
skills/
├── deployment-checklist/
│   ├── SKILL.md
│   └── supporting-files
└── testing-strategy/
    └── SKILL.md
```

## Decision Flowchart

Use this flowchart to determine which layer to use:

```
┌─ Do you need to find or read information? ─┐
│                                              │
├─ YES → Is it a focused, reusable task?      ├─ YES → AGENT
│         (codebase analysis, search, grep)   │
│                                              ├─ NO → Use multiple agents in a command
│
├─ NO → Do you need to orchestrate a workflow?
│        (combine steps, ask user questions)  ├─ YES → COMMAND
│                                              │
├─ NO → Do you need domain-specific knowledge?
│        (project conventions, best practices) ├─ YES → SKILL
│                                              │
└─ UNCLEAR → Ask: "Will this be used across
             multiple commands/projects?"      ├─ YES → AGENT
             "Is this user-facing?"            ├─ NO  → SKILL
```

## Interaction Patterns

### Command → Agent
Commands spawn agents as sub-tasks:

```
User calls /create_plan
  ↓
Command reads config, asks clarifying questions
  ↓
Command spawns agents:
  - codebase-analyzer: understand structure
  - pattern-finder: identify related code
  ↓
Agents return findings
  ↓
Command synthesizes findings into a plan
```

### Command → Skill
Commands reference project skills in their prompts:

```
User calls /commit
  ↓
Command checks project skills (e.g., commit-style-guide)
  ↓
Command passes skill content in prompt to ensure
  commits follow project conventions
  ↓
Command generates commit message
```

### Agent → Skill
Agents can reference skills but do not modify them:

```
Agent researching codebase
  ↓
Finds reference to skill (e.g., testing-strategy)
  ↓
Reads skill to understand conventions
  ↓
Includes context in findings
```

## When to Add a New Layer

### Add an Agent When
- Multiple commands need the same analysis
- The task is read-only and focused
- Results should be consumable by commands without user intervention
- The task can be defined with a specific tool set

### Add a Command When
- You need to provide a user-facing slash command
- The workflow involves multiple steps or decisions
- You need to spawn agents and synthesize their outputs
- User interaction or presentation is needed

### Add a Skill When
- Your project has domain-specific conventions or requirements
- Knowledge needs to be reusable across multiple commands
- The skill describes methodology, patterns, or best practices
- It's project-specific, not generic to all projects


## Progressive Disclosure

Do not load all commands and conventions into agent context at session start. Context is finite and attention degrades as context grows.

**How loading works in project-specs:**
- **Commands** are loaded on invocation — the slash command triggers loading
- **Conventions** should be referenced, not pre-loaded
- **Skills** are loaded when a command calls them, not at startup
- **Agents** load only when spawned by a command

**Guidelines for file size:**
- If a convention file exceeds 500 lines, split it into focused sub-files with a router index
- A 200-line focused document outperforms a 2,000-line comprehensive one because the agent actually follows the focused version
- Each file should cover one concept and be scannable in under 5 seconds

**When adding new conventions:**
- One concept per file
- Title should be scannable (agent decides in <1 second whether to read it)
- Include a 1-line summary at the top before any detail
- Prefer examples over prose — agents follow examples more reliably than instructions

**When adding new commands:**
- Keep commands under 300 lines where possible
- If a command grows beyond that, extract reusable sections into skills
- Anti-rationalization tables, scope rules, and verification gates add lines but earn their keep — don't count them toward the "too long" threshold

## Configuration

All three layers are configured in `specs.config.yaml`:

```yaml
agents:
  enabled: true
  directory: agents/

commands:
  enabled: true
  directory: commands/

skills:
  enabled: true
  directory: skills/
```

## Summary

| Layer | User-Facing | Reusable | Read-Only | Scope |
|-------|-------------|----------|-----------|-------|
| Agent | No | Yes | Yes | Single task |
| Command | Yes | Moderate | No | Multi-step workflow |
| Skill | No | Yes | No | Knowledge/conventions |
