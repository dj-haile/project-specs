# Thoughts Directory Convention

The `thoughts/` directory is an optional feature that provides cross-session continuity, persistent knowledge, and structured context for handoffs between developers and sessions.

## Purpose

The thoughts directory serves as a **persistent knowledge base for your project**, enabling:

- **Cross-session continuity**: Preserve context when handing off between developers or resuming work
- **Knowledge persistence**: Record decisions, architectural notes, and research findings
- **Structured handoffs**: Pass project state and open questions to team members or future sessions
- **Reference material**: Quick access to ticket status, PR context, and research history

## Directory Structure

```
thoughts/
├── shared/              # Committed to git, team-visible
│   ├── architecture/
│   ├── patterns/
│   └── decisions/
├── plans/               # Feature and implementation plans
├── tickets/             # Ticket context and research
├── handoffs/            # Session handoff documents
├── prs/                 # Pull request context and reviews
├── research/            # Investigation notes and findings
└── local/               # Local-only, gitignored
    └── session-notes/
```

### Subdirectory Purposes

**shared/** - Team-wide, committed to git
- Architectural decisions and patterns
- Reusable knowledge and conventions
- Historical context and rationale

**plans/** - Feature implementation plans
- Research findings and analysis
- Proposed implementation approach
- Timeline and dependencies

**tickets/** - Issue/ticket-specific context
- Ticket research and initial analysis
- Links to related code
- Status and blockers

**handoffs/** - Session continuity
- What you completed this session
- What's next
- Open questions and context for the next person

**prs/** - Pull request documentation
- PR context and motivation
- Testing approach
- Review notes

**research/** - Investigation notes
- Deep dives into systems
- Pattern analysis
- Learning and exploration

**local/** - Session-specific, gitignored
- Scratch notes
- Temporary findings
- Personal session context

## File Naming Conventions

### With Timestamp
For time-sensitive or session-specific files:
```
YYYY-MM-DD_HH-MM-SS_description.md
2026-03-24_14-30-45_debug-session.md
```

### Without Timestamp
For longer-lived documents:
```
YYYY-MM-DD-description.md
2026-03-24-implement-auth-refactor.md
```

## YAML Frontmatter Requirements

All thoughts files should include metadata:

```yaml
---
date: 2026-03-24
git_commit: abc1234
branch: feature/auth-refactor
status: in_progress
tags:
  - authentication
  - refactor
  - blocking
---
```

### Frontmatter Fields

| Field | Required | Format | Purpose |
|-------|----------|--------|---------|
| `date` | Yes | YYYY-MM-DD | Document creation date |
| `git_commit` | No | commit hash | Associated code state |
| `branch` | No | branch name | Related branch |
| `status` | No | in_progress, blocked, completed, abandoned | Document status |
| `tags` | No | array | Searchable metadata |

## Optional: Config-Driven Control

The `thoughts/` directory is entirely optional. Control it in `specs.config.yaml`:

```yaml
# Enable thoughts directory for this project
thoughts:
  enabled: true
  directory: thoughts/

  # Auto-create suggested subdirectories
  auto_create: true

  # Include shared/ in git commits
  include_in_git: true
```

If `thoughts.enabled: false`, commands and agents do not reference or create thought files.

## Best Practices

### Commit shared/ to Git
Keep architectural decisions and team knowledge in version control:

```bash
git add thoughts/shared/
git commit -m "docs: add deployment checklist to thoughts/shared"
```

### Gitignore local/
Add to `.gitignore`:

```
thoughts/local/
thoughts/**/*.tmp
```

### Use Handoffs for Transitions
End each session with a handoff document:

```
thoughts/handoffs/2026-03-24-session-end.md
- Completed: Auth refactor phase 1
- Next: Migrate tests to new authentication system
- Blockers: Waiting on decision from @alice about API design
- Open questions: How to handle legacy token support?
```

### Date-Sort for Discovery
Naming with dates makes it easy to find recent work:

```
thoughts/plans/
├── 2026-03-20-initial-analysis.md
├── 2026-03-22-revised-approach.md
└── 2026-03-24-final-plan.md
```

### Tag for Quick Search
Use tags in frontmatter for filtering:

```yaml
tags:
  - performance
  - database
  - urgent
```

## Integration with Commands

Commands can automatically create and reference thoughts:

- `/research_codebase` → creates `thoughts/research/YYYY-MM-DD_findings.md`
- `/create_plan` → creates `thoughts/plans/YYYY-MM-DD_plan.md`
- `/create_handoff` → creates `thoughts/handoffs/YYYY-MM-DD_handoff.md`
- `/resume_handoff` → reads previous `thoughts/handoffs/` to restore context

## History: The _nt Suffix

Earlier versions of the framework included separate `_nt` variant commands (e.g., `create_plan` and `create_plan_nt`) where the `_nt` suffix meant "no thoughts" — commands that worked without the thoughts/ directory.

This has been consolidated: **all commands now use a single implementation**, with the `thoughts.enabled` config flag controlling behavior. Commands automatically skip thought creation if disabled.

## When to Use (and When Not To)

### Use thoughts/ When
- You have team handoffs or multi-session projects
- You need to document architectural decisions
- You want persistent context for future maintenance
- You're collaborating and need shared context

### Skip thoughts/ When
- You're working on a small, one-off project
- All context is in code comments and commit messages
- You prefer minimal overhead
- Your project doesn't value persistent documentation

The framework supports both approaches. Set `thoughts.enabled: false` and ignore the directory entirely if it doesn't fit your workflow.
