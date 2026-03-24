# project-specs — Build Instructions

## What This Repo Will Be

A standalone, reusable Claude Code spec framework that can be installed into any project. It extracts the three-layer architecture (agents → commands → skills) from `dj-haile/skills-app` into a generic, configurable system.

**Distribution model:** Template repo with a setup script. Users can fork/clone to scaffold new projects, or run the setup script to install into an existing project. This is the current best practice — submodules add too much friction, and pure templates don't allow updates to propagate.

---

## Proposed Repo Structure

```
project-specs/
├── README.md                          # Methodology guide + getting started
├── AGENTS.md                          # For AI agents working with this repo
├── CHANGELOG.md                       # Semantic versioning log
├── LICENSE                            # MIT
├── setup.sh                           # Bootstrap script (installs .claude/ into any project)
├── specs.config.example.yaml          # Template config — user copies to specs.config.yaml
│
├── templates/                         # Default files installed into projects
│   └── pr_description.md             # Default PR description template
│
├── agents/                            # 6 reusable agents
│   ├── web-search-researcher.md
│   ├── codebase-analyzer.md
│   ├── codebase-locator.md
│   ├── codebase-pattern-finder.md
│   ├── thoughts-analyzer.md
│   └── thoughts-locator.md
│
├── commands/                          # Reusable commands (consolidated, no _nt/_generic duplication)
│   ├── core/                          # Universal workflow commands
│   │   ├── create_plan.md             # Consolidated from create_plan + create_plan_generic + create_plan_nt
│   │   ├── implement_plan.md
│   │   ├── iterate_plan.md            # Consolidated from iterate_plan + iterate_plan_nt
│   │   ├── validate_plan.md
│   │   ├── research_codebase.md       # Consolidated from 3 variants
│   │   ├── debug.md
│   │   ├── commit.md                  # Consolidated from commit + ci_commit
│   │   ├── describe_pr.md             # Consolidated from describe_pr + ci_describe_pr
│   │   ├── create_handoff.md
│   │   ├── resume_handoff.md
│   │   └── local_review.md
│   │
│   └── integrations/                  # Commands that require external tools
│       ├── ticket_plan.md             # Generic version of ralph_plan (parameterized ticket system)
│       ├── ticket_research.md         # Generic version of ralph_research
│       ├── ticket_impl.md             # Generic version of ralph_impl
│       ├── ticket_oneshot.md          # Generic version of oneshot + oneshot_plan
│       ├── ticket_manage.md           # Generic version of linear.md (works with Linear/Jira/Asana)
│       ├── founder_mode.md            # Parameterized for any ticket system
│       └── create_worktree.md         # Parameterized (no hack/ dependency)
│
├── skills/                            # Starter skill templates (NOT the skills-app domain skills)
│   └── _template/
│       └── SKILL.md                   # Annotated template showing frontmatter + structure
│
├── conventions/                       # Opinionated methodology documentation
│   ├── three-layer-architecture.md    # When to use agents vs commands vs skills
│   ├── thoughts-directory.md          # The thoughts/ convention (optional but recommended)
│   ├── workflow-patterns.md           # research → plan → implement → review → handoff → debug
│   ├── model-selection.md             # When to use opus vs sonnet vs haiku
│   └── naming-conventions.md          # File naming, frontmatter patterns, _nt suffix history
│
└── examples/                          # Example configurations for different project types
    ├── api-service/
    │   └── specs.config.yaml          # Config for a typical API backend
    ├── frontend-app/
    │   └── specs.config.yaml          # Config for a React/Next.js app
    └── data-pipeline/
        └── specs.config.yaml          # Config for an ETL/ML pipeline
```

---

## Key Design Decisions

### 1. Consolidate the _nt/_generic variants

Your skills-app currently has 3 variants of several commands (e.g., `create_plan.md`, `create_plan_generic.md`, `create_plan_nt.md`). In the generic repo, these should be **one file each** that reads from `specs.config.yaml` to determine behavior:

```yaml
# specs.config.yaml
thoughts_directory: true          # false = _nt behavior
thoughts_path: "thoughts/shared"  # customizable path
```

The command files should use conditional logic:
```markdown
## Storage
{{#if thoughts_directory}}
Save plans to `{{thoughts_path}}/plans/` ...
{{else}}
Save plans to the project root or user-specified location ...
{{/if}}
```

**Implementation approach:** Rather than actual template syntax (which Claude Code doesn't natively support), use a preamble in each command that reads the config:

```markdown
## Setup (read before proceeding)
1. Check if `specs.config.yaml` exists at project root
2. If `thoughts_directory: true`, use `{{thoughts_path}}` for document storage
3. If `thoughts_directory: false` or config missing, ask the user where to save documents
```

### 2. Parameterize the ticket system

The `ralph_*` commands and `linear.md` are tightly coupled to Linear. In the generic repo, these become `ticket_*` commands with a config parameter:

```yaml
# specs.config.yaml
ticket_system: "linear"           # or "jira", "asana", "github-issues"
ticket_mcp_prefix: "mcp__linear"  # MCP tool prefix for the ticket system
ticket_id_pattern: "ENG-\\d+"     # Regex for ticket IDs in branch names
```

### 3. The thoughts/ directory is an optional convention, not a requirement

Document it in `conventions/thoughts-directory.md` as a recommended pattern with clear benefits (cross-session continuity, handoff context, plan storage), but make every command work without it. This is what your `_nt` variants already do — we're just making it the default flexibility rather than separate files.

### 4. Skills are excluded but templated

The 5 skills-app skills (vp-orchestrator, project-tracker, data-query, visualize, predict) stay in skills-app. The generic repo includes only a `_template/SKILL.md` showing the proper structure, frontmatter, and conventions so users can create their own project-specific skills.

### 5. The setup script handles installation

`setup.sh` should:
1. Check if `.claude/` already exists (don't clobber)
2. Copy `specs.config.example.yaml` → `specs.config.yaml` if not present
3. Symlink or copy agents/ and commands/ into `.claude/`
4. Create `.claude/skills/` directory for project-specific skills
5. Optionally create `thoughts/` directory structure
6. Print a summary of what was installed

```bash
# Usage examples:
./setup.sh /path/to/my-project              # Install into existing project
./setup.sh /path/to/my-project --link       # Symlink (updates propagate)
./setup.sh /path/to/my-project --copy       # Copy (independent snapshot)
./setup.sh /path/to/my-project --update     # Update existing installation
```

### 6. AGENTS.md follows ETH Zurich guidance

Per our research finding: limit to non-inferable details only. The AGENTS.md should cover:
- The three-layer architecture concept (not obvious from files alone)
- The `specs.config.yaml` mechanism (agent needs to know to read it)
- The thoughts/ directory convention (if enabled)
- Model selection rationale (why opus for planning, sonnet for analysis)
- What NOT to do (don't modify agents/, don't create skills without SKILL.md frontmatter)

### 7. Semantic versioning

```
Major (2.0.0) = Breaking changes to command interfaces or config schema
Minor (1.1.0) = New agents, commands, or conventions added
Patch (1.0.1) = Prompt improvements, bug fixes, documentation
```

---

## Build Order

Phase 1 — **Extraction & Consolidation** (do first):
1. Copy all 6 agents as-is (they're already generic)
2. Consolidate the 3-variant commands into single files with config-awareness
3. Parameterize the Linear-specific commands into generic ticket_* commands
4. Create `specs.config.example.yaml` with all parameters documented

Phase 2 — **Documentation** (do second):
5. Write `conventions/` docs from your accumulated knowledge
6. Write README.md with getting started guide
7. Write AGENTS.md (non-inferable details only)
8. Create example configurations for 3 project types

Phase 3 — **Tooling** (do third):
9. Write `setup.sh` with install/link/copy/update modes
10. Create skill template with annotated SKILL.md
11. Add LICENSE (MIT) and CHANGELOG.md

Phase 4 — **Validation** (do last):
12. Test setup.sh against a fresh empty project
13. Test setup.sh against an existing project with a .claude/ directory
14. Verify all commands work without thoughts/ directory
15. Verify ticket_* commands work with config pointing to Linear

---

## What Changes From skills-app

| In skills-app | In project-specs | Why |
|---|---|---|
| `create_plan.md` + `create_plan_generic.md` + `create_plan_nt.md` | Single `commands/core/create_plan.md` | Config-driven instead of file duplication |
| `iterate_plan.md` + `iterate_plan_nt.md` | Single `commands/core/iterate_plan.md` | Same |
| `research_codebase.md` + `_generic` + `_nt` | Single `commands/core/research_codebase.md` | Same |
| `commit.md` + `ci_commit.md` | Single `commands/core/commit.md` | Differences were minimal |
| `describe_pr.md` + `ci_describe_pr.md` | Single `commands/core/describe_pr.md` | Identical content |
| `ralph_plan.md` | `commands/integrations/ticket_plan.md` | Parameterized ticket system |
| `ralph_research.md` | `commands/integrations/ticket_research.md` | Same |
| `ralph_impl.md` | `commands/integrations/ticket_impl.md` | Same |
| `oneshot.md` + `oneshot_plan.md` | `commands/integrations/ticket_oneshot.md` | Merged + parameterized |
| `linear.md` | `commands/integrations/ticket_manage.md` | Generic ticket management |
| 5 domain skills | `skills/_template/SKILL.md` only | Skills are project-specific |
| No config file | `specs.config.yaml` | Drives all parameterization |
| No setup script | `setup.sh` | Handles installation into any project |
| No methodology docs | `conventions/` directory | Documents the "why" behind the architecture |

---

## Decisions (resolved)

1. **HumanLayer dependency**: **Removed.** All references to HumanLayer (`npx humanlayer launch`, `humanlayer thoughts sync`) stripped from generic commands. The `oneshot` command pattern is replaced with a self-contained `ticket_oneshot.md` that uses Claude Code's native session launching. The `describe_pr` command saves files directly instead of syncing via HumanLayer.

2. **hack/ scripts**: **Inline the logic.** The `create_worktree.md` command will be self-contained — worktree creation logic written directly into the command rather than referencing an external `hack/create_worktree.sh`. No `scripts/` directory needed.

3. **thoughts/ subdirectory structure**: **Pre-create the full tree.** The setup script creates:
   ```
   thoughts/
   └── shared/
       ├── plans/
       ├── tickets/
       ├── handoffs/
       ├── prs/
       └── pr_description.md    ← default template included
   ```

4. **PR description template**: **Ship a default.** Included as `templates/pr_description.md` in the repo, copied into `thoughts/shared/pr_description.md` by setup script. Covers: What/Problem/Solution/Changes/Breaking changes/Verification checklist/Changelog/Screenshots.

---

*Decisions finalized. Ready to build Phase 1.*
