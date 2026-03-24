# AGENTS.md — Agent Design and Conventions

This document captures the reasoning and conventions for agents in project-specs. It is not a tutorial; refer to [README.md](./README.md) for getting started.

## Three-Layer Architecture: Why

project-specs enforces a three-layer separation:

```
Agents (orchestrators)
  ↓
Commands (reusable workflows)
  ↓
Skills (atomic operations)
```

**Why this structure?**

1. **Composability** — Commands combine skills without reimplementing logic. A new integration command can reuse core skills (search, validate, commit) without duplication.

2. **Consistency** — Agents all follow the same initialization pattern: read specs.config.yaml, instantiate commands, dispatch work. This makes agent behavior predictable and testable.

3. **Scalability** — Skills are versioned and namespaced. You can maintain multiple versions of a skill, or swap implementations (e.g., use a faster linter for quick checks) without touching agent or command code.

4. **Auditability** — Each layer has a clear interface. Agents log which commands they invoke; commands log which skills they use. This creates a traceable execution path.

## Initialization: specs.config.yaml First

Every agent and command **must** read specs.config.yaml as its first action. Do not infer project parameters from the environment or heuristics.

```python
# agents/my-agent/agent.py (pseudo-code)
import yaml

with open('specs.config.yaml') as f:
    config = yaml.safe_load(f)

project_name = config['project_name']
models = config['models']
commit_style = config['commit_style']
```

This ensures:
- **Single source of truth** — All project metadata lives in one file.
- **No guessing** — An agent deployed to a new project reads the correct config immediately.
- **Environment independence** — Agents work in CI/CD, local development, and cloud runners without special setup.

## Thoughts Directory Convention

If **thoughts_directory: true** in specs.config.yaml, agents and commands use the **thoughts/** directory to persist analysis and decisions across sessions.

Structure:
```
thoughts/
  research/
    codebase-analysis-<timestamp>.md
    module-dependencies-<timestamp>.md
  decisions/
    architecture-<timestamp>.md
    migration-plan-<timestamp>.md
  handoffs/
    session-<uuid>.md
```

**When to write to thoughts/**:
- After completing research (codebase-analyzer writes findings)
- Before making architectural decisions (document trade-offs)
- When handing off work to another session (create_handoff writes context)

**When NOT to write**:
- If thoughts_directory: false in config (respect the setting)
- For transient debugging output (use stdout instead)
- For sensitive data (credentials, keys, API secrets)

## Model Selection Rationale

project-specs assigns models to tiers of work:

| Tier | Model | Use Case |
|------|-------|----------|
| **Planning** | claude-opus | Create and iterate plans; architectural decisions; long-context analysis |
| **Analysis** | claude-sonnet | Code review, pattern discovery, testing; general-purpose work |
| **Quick** | claude-haiku | Lint checks, file searches, small edits; fast turnaround |

This tiering balances cost, latency, and quality:

- Opus for decisions ensures high-quality planning and fewer bad decisions upstream.
- Sonnet for analysis provides good accuracy without the latency/cost of Opus.
- Haiku for quick checks minimizes latency and cost for simple operations.

Commands select models based on the config:
```python
model = config['models']['planning']  # Use Opus for create_plan
model = config['models']['analysis']  # Use Sonnet for validate_plan
model = config['models']['quick']      # Use Haiku for file search
```

## What NOT to Do

### Don't Modify agents/ Directory

The agents/ directory is shared infrastructure. Custom orchestration lives in integration commands (ticket_plan, founder_mode, etc.), not in new agents.

**Anti-pattern:**
```python
# agents/custom-orchestrator/agent.py
# DON'T: Create custom agents for specific projects
```

**Pattern:**
```python
# commands/integrations/custom-workflow/command.py
# DO: Create a custom command that composes existing agents
```

### Don't Create Skills Without SKILL.md Frontmatter

Every skill must have a SKILL.md file declaring:
- **name** — Human-readable name
- **description** — What it does
- **inputs** — Required and optional parameters
- **outputs** — Return type and format
- **version** — Semantic version

This metadata enables:
- Command-line discovery (list available skills)
- Type checking and validation
- Versioning and compatibility checks
- Documentation generation

**Anti-pattern:**
```
skills/my-skill/
  script.py
```

**Pattern:**
```
skills/my-skill/
  SKILL.md
  script.py
```

### Don't Hardcode Project-Specific Values

All project parameters (branch prefix, commit style, ticket system, models) belong in specs.config.yaml. Don't hardcode them in agent or command code.

**Anti-pattern:**
```python
# agents/codebase-analyzer/agent.py
branch_prefix = "feat/"  # DON'T: hardcoded
commit_style = "conventional"  # DON'T: hardcoded
```

**Pattern:**
```python
# Read from specs.config.yaml
branch_prefix = config['branch_prefix']
commit_style = config['commit_style']
```

This allows:
- Different teams to use the same agent with different conventions
- Switching projects without modifying code
- Configuration as code (version control specs.config.yaml, not agent source)

### Don't Use thoughts-locator/thoughts-analyzer if thoughts_directory: false

If a project disables thought persistence, don't invoke thoughts-locator or thoughts-analyzer. Respect the config setting.

**Anti-pattern:**
```python
# commands/implement_plan/command.py
if True:  # DON'T: ignore config
    thoughts = thoughts_analyzer.search(query)
```

**Pattern:**
```python
if config['thoughts_directory']:
    thoughts = thoughts_analyzer.search(query)
else:
    thoughts = []  # No persistent thoughts; start fresh
```

### Don't Suggest Improvements in Research Commands

Research commands (research_codebase, codebase-pattern-finder, web-search-researcher) document systems as-is. They do not recommend refactoring, architecture changes, or optimizations.

**Anti-pattern:**
```
# research_codebase output
Found 12 uses of deprecated API_v1.fetch().
Recommendation: Migrate to API_v2.stream() for better performance.
```

**Pattern:**
```
# research_codebase output
Found 12 uses of deprecated API_v1.fetch() at:
  - src/services/users.py:42
  - src/services/products.py:88
  - src/api/routes.py:156
```

This separation ensures:
- Research is objective and reproducible
- Recommendations come from create_plan and iterate_plan (where tradeoffs are weighed)
- Clients can decide whether to act on findings

## Configuration and Agents

All six agents read specs.config.yaml and adapt their output format and behavior:

| Agent | Config Keys Used |
|-------|------------------|
| codebase-analyzer | project_name, models.analysis |
| codebase-locator | models.quick |
| codebase-pattern-finder | models.analysis |
| thoughts-analyzer | thoughts_directory, models.analysis |
| thoughts-locator | thoughts_directory, models.quick |
| web-search-researcher | models.analysis |

For example, if a project sets `models.quick: haiku`, thoughts-locator will use Haiku for fast thought searches. If a project sets `thoughts_directory: false`, both thought agents become no-ops.

## Versioning Agents

Agent implementations are versioned in their SKILL.md files (if they are exposed as skills) or in their agent.py metadata. Use Semantic Versioning:

- **Major** — Breaking changes to inputs, outputs, or command dispatch
- **Minor** — New features, new output fields
- **Patch** — Bug fixes, internal refactors

When updating an agent, bump the version and document the change in CHANGELOG.md.

## Calling Agents from Commands

Commands invoke agents to delegate work:

```python
# commands/create_plan/command.py
from agents.codebase_analyzer import CodebaseAnalyzer
from agents.web_search_researcher import WebSearchResearcher

analyzer = CodebaseAnalyzer(config)
web_researcher = WebSearchResearcher(config)

# Dispatch work
structure = analyzer.analyze()
research = web_researcher.search("best practices for " + query)

# Compose results into plan
plan = build_plan(structure, research)
```

This pattern ensures:
- Agents are instantiated with config (they can adapt behavior)
- Commands own orchestration logic (which agents to call, in what order)
- Results are composable (agents return structured data, not side effects)

## Summary of Conventions

| Convention | Rationale |
|-----------|----------|
| **Read specs.config.yaml first** | Single source of truth for project metadata |
| **Use three-layer architecture** | Composability, consistency, scalability, auditability |
| **Respect thoughts_directory setting** | Some teams want persistence; others don't |
| **Model tiering (Opus → Sonnet → Haiku)** | Balance cost, latency, and quality |
| **Don't modify agents/**  | Agents are shared infrastructure |
| **SKILL.md frontmatter required** | Enables discovery, versioning, type checking |
| **No hardcoded project values** | Configuration as code; teams can customize |
| **Research as-is, not recommendations** | Separation of concerns; planning is downstream |

Follow these conventions and project-specs agents will be reusable, testable, and maintainable across projects.
