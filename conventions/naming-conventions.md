# Naming Conventions

Consistent naming conventions across agents, commands, skills, and configuration files make the framework predictable and maintainable.

## Agents

### File Naming
Use **kebab-case** for agent filenames:
```
agents/
├── codebase-analyzer.md
├── pattern-finder.md
├── dependency-mapper.md
├── log-analyzer.md
├── git-historian.md
└── test-suite-analyzer.md
```

### Agent Identifier
The agent identifier comes from the filename (without `.md`):
- File: `codebase-analyzer.md`
- Identifier: `codebase-analyzer`

### YAML Frontmatter
Agents must include YAML frontmatter with these fields:

```yaml
---
name: codebase-analyzer
description: Analyzes project structure and identifies architectural patterns
tools:
  - glob
  - grep
  - read
model: sonnet
---
```

### Naming Guidelines
- Descriptive but concise (2-3 words)
- Include the primary action or specialty
- Examples of good names:
  - `codebase-analyzer` (what it does + domain)
  - `pattern-finder` (action + target)
  - `git-historian` (domain + specialty)
  - `test-suite-analyzer` (domain + object)
- Avoid:
  - Single-word names (`analyzer` is too generic)
  - Names longer than 4 words
  - Acronyms without explanation
  - Project-specific names (keep agents reusable)

## Commands

### File Naming
Use **snake_case** for command filenames:
```
commands/
├── research_codebase.md
├── create_plan.md
├── implement_plan.md
├── commit.md
├── describe_pr.md
└── debug.md
```

### Slash Command Trigger
The command trigger comes from the filename (without `.md`):
- File: `create_plan.md`
- User invokes with: `/create_plan`

### YAML Frontmatter
Commands must include YAML frontmatter with these fields:

```yaml
---
description: Creates a detailed implementation plan based on research findings
model: opus
---
```

### Naming Guidelines
- Verb + object structure
- Use snake_case (lowercase with underscores)
- Start with action verb when possible
- Examples of good names:
  - `research_codebase` (verb + domain)
  - `create_plan` (verb + output)
  - `implement_plan` (verb + reference)
  - `commit` (single action)
  - `debug` (single action)
- Avoid:
  - Camel case or kebab-case for commands
  - Overly generic names (`process`, `run`)
  - Names that don't convey the action
  - Acronyms without context

### Command Groups
Related commands use common prefixes for discoverability:

```
Ticket workflow:
  /ticket_research
  /ticket_plan
  /ticket_impl
  /ticket_oneshot

Planning workflow:
  /research_codebase
  /create_plan
  /iterate_plan
  /implement_plan
  /validate_plan

Handoff workflow:
  /create_handoff
  /resume_handoff
```

## Skills

### Directory Naming
Use **kebab-case** for skill directories:
```
skills/
├── deployment-checklist/
├── testing-strategy/
├── commit-style-guide/
└── api-design-patterns/
```

### File Structure
Each skill is a directory containing a required `SKILL.md` file and optional supporting files:

```
skills/deployment-checklist/
├── SKILL.md          # Required: main skill content
├── checklist.md      # Optional: supplementary material
└── examples/         # Optional: example files
    ├── prod-deploy.md
    └── staging-deploy.md
```

### Naming Guidelines
- Describe the domain or methodology
- Use kebab-case
- Specific enough to be useful (not generic)
- Examples of good names:
  - `deployment-checklist` (clear domain)
  - `testing-strategy` (methodology)
  - `commit-style-guide` (convention)
  - `api-design-patterns` (patterns in domain)
- Avoid:
  - Single-word names
  - Project-specific names (skills should be reusable)
  - Names that are too generic (`guidelines`, `rules`)

### SKILL.md Content
The main skill file should include:
```markdown
# Deployment Checklist

[Description of the skill]

## Key Principles
[Main points]

## Process
[Step-by-step or checklist]

## Examples
[Concrete examples]
```

## Configuration Files

### Main Configuration
The framework configuration file is always named:
```
specs.config.yaml
```

Located at the project root.

### Structure
```yaml
# specs.config.yaml at project root

project:
  name: my-project
  description: Project description

agents:
  enabled: true
  directory: agents/

commands:
  enabled: true
  directory: commands/

skills:
  enabled: true
  directory: skills/

thoughts:
  enabled: true
  directory: thoughts/

models:
  default: sonnet
  commands:
    create_plan: opus
    research_codebase: opus

tickets:
  enabled: true
  pattern: "ENG-\\d+"
```

## Thoughts Directory

### File Naming Patterns

#### With Timestamp (for session-specific files)
```
YYYY-MM-DD_HH-MM-SS_description.md
2026-03-24_14-30-45_debug-session.md
2026-03-24_09-15-00_research-findings.md
```

#### Without Timestamp (for longer-lived documents)
```
YYYY-MM-DD-description.md
2026-03-24-implement-auth-refactor.md
2026-03-23-ticket-ENG-1234-plan.md
```

### Subdirectory Naming
```
thoughts/
├── shared/           # Team knowledge
├── plans/            # Implementation plans
├── tickets/          # Ticket-specific context
├── handoffs/         # Session handoffs
├── prs/              # PR documentation
├── research/         # Investigation notes
└── local/            # Session-specific (gitignored)
```

### YAML Frontmatter
```yaml
---
date: 2026-03-24
git_commit: abc1234
branch: feature/something
status: in_progress
tags:
  - feature
  - blocking
---
```

## Ticket References

### Pattern Configuration
Tickets are referenced using configurable patterns in `specs.config.yaml`:

```yaml
tickets:
  enabled: true
  pattern: "ENG-\\d+"  # Matches ENG-1234
```

### Common Patterns
```
Jira style: "ENG-\\d+"         # ENG-1234
GitHub style: "GH-\\d+"        # GH-567
Linear style: "LIN-\\d+"       # LIN-1234
Simple numeric: "#\\d+"        # #123
Prefix with multiple: "[A-Z]+-\\d+"  # Any-123
```

### File References to Tickets
When documenting tickets in the thoughts directory, use consistent naming:

```
thoughts/tickets/
├── ENG-1234-research.md
├── ENG-1234-plan.md
├── ENG-1234-findings.md
└── ENG-1235-implementation.md
```

Format: `{TICKET_ID}-{type}.md`

## History: The _nt Suffix

Earlier versions of the framework included variant commands with an `_nt` suffix, where `_nt` stood for "**no thoughts**" — these were versions of commands that skipped thought document creation.

Examples of deprecated naming:
- `create_plan.md` and `create_plan_nt.md` (two separate files)
- `implement_plan.md` and `implement_plan_nt.md`

### Why It Changed
The framework has consolidated to a single implementation per command. Control the behavior through configuration:

```yaml
# specs.config.yaml
thoughts:
  enabled: true  # or false to disable
```

When `thoughts.enabled: false`, all commands skip thought creation automatically. This eliminated the need for duplicate files with different suffixes.

### Migration from _nt Naming
If you're upgrading from a version that used `_nt`:
1. Keep only the base command file (remove `_nt` variant)
2. Set `thoughts.enabled: true/false` in config
3. Both behaviors now come from the same file

## Summary Table

| Item | Case | Location | Example |
|------|------|----------|---------|
| Agent file | kebab-case | agents/ | codebase-analyzer.md |
| Agent identifier | kebab-case | frontmatter | codebase-analyzer |
| Command file | snake_case | commands/ | create_plan.md |
| Command trigger | snake_case | user input | /create_plan |
| Skill directory | kebab-case | skills/ | deployment-checklist/ |
| Config file | snake_case | project root | specs.config.yaml |
| Thoughts (with time) | YYYY-MM-DD_HH-MM-SS | thoughts/ | 2026-03-24_14-30-45_debug.md |
| Thoughts (without time) | YYYY-MM-DD-kebab | thoughts/ | 2026-03-24-auth-refactor.md |
| Ticket reference | Pattern-based | config | ENG-1234 |

## Consistency Checklist

Before creating a new agent, command, or skill, verify:

- [ ] Naming follows correct case convention
- [ ] YAML frontmatter includes required fields
- [ ] File is in correct directory (agents/, commands/, or skills/)
- [ ] Agent/command name is descriptive but concise
- [ ] Name is reusable (not project-specific)
- [ ] No _nt suffix (use config instead)
- [ ] Skill includes supporting documentation
- [ ] Frontmatter is valid YAML
