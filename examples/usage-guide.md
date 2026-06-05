# Usage Guide — project-specs v1.1.0

This guide walks through how to use project-specs features with concrete examples. It covers the recommended workflow, each command's role, and the behavioral guardrails that keep agent work on track.

---

## Getting Started

### Install into your project

```bash
# Clone project-specs
git clone https://github.com/dj-haile/project-specs ~/.project-specs

# Install into your project
~/.project-specs/setup.sh /path/to/your-project

# Or symlink for automatic updates
~/.project-specs/setup.sh /path/to/your-project --link
```

### Verify installation

After running setup.sh, confirm these exist:

```
your-project/
├── .claude/
│   ├── agents/          # 6 research agents
│   ├── commands/        # 12 core + 7 integration commands
│   └── skills/          # Empty, ready for project-specific skills
├── specs.config.yaml    # Your project configuration
└── pr_description.md    # PR template
```

### Configure for your project

Edit `specs.config.yaml`:

```yaml
project_name: "my-api"
thoughts_directory: true
thoughts_path: "thoughts/shared"
ticket_system: "github-issues"    # or linear, jira
ticket_id_pattern: "#\\d+"
branch_prefix: "feat/"
commit_style: "conventional"
models:
  planning: opus
  analysis: sonnet
  quick: haiku
```

---

## The Recommended Workflow

### Spec-first development (recommended)

The strongest workflow starts with requirements, then plans, then implements:

```
/spec → /create_plan → /implement_plan → /validate_plan → /commit → /describe_pr
```

**Example: Adding rate limiting to an API**

```
You: /spec We need to add rate limiting to our public API endpoints.
     Users are hitting us with too many requests and degrading service
     for everyone.

Claude: [researches codebase, finds all public endpoints, checks for
         existing rate limiting, identifies the request handling middleware]

         Here's my requirements spec:

         Problem: Public API has no rate limiting. During peak traffic,
         a single client can monopolize server resources.

         Acceptance Criteria:
         - Given a client exceeds 100 requests/minute,
           When they make another request,
           Then they receive a 429 status with Retry-After header
         - Given rate limits are hit,
           When the window expires,
           Then requests resume normally
         [... more criteria ...]

         Out of scope: Per-endpoint custom limits, paid tier exemptions,
         WebSocket connections.

         Spec saved to thoughts/specs/2026-05-29-rate-limiting.md
         Next step: Run /create_plan to design the implementation.
```

```
You: /create_plan based on thoughts/specs/2026-05-29-rate-limiting.md

Claude: [reads spec, uses acceptance criteria as success criteria,
         researches middleware patterns in your codebase]

         Phase 1: Add rate limiter middleware
         Phase 2: Configure per-route limits
         Phase 3: Add monitoring and alerting
         [each phase has automated + manual verification]
```

```
You: /implement_plan thoughts/plans/2026-05-29-rate-limiting-plan.md

Claude: [implements phase 1, runs tests, pauses for manual verification]

         Phase 1 Complete - Ready for Manual Verification
         Automated verification passed:
         - Build passes
         - 12 new unit tests pass
         - Type checking passes

         Please test: Send >100 requests in 1 minute and verify 429 response.
```

### When to skip /spec

For well-defined tickets with clear acceptance criteria, you can start at `/create_plan` or `/ticket_plan`. The `/spec` step is most valuable when:
- Requirements are vague or ambiguous
- Multiple people have different expectations
- Scope creep is a risk
- You're not sure what "done" looks like

---

## Behavioral Guardrails

### Anti-rationalization tables

Every core command includes a "Common Shortcuts to Avoid" table. These are pre-written rebuttals to excuses the agent will produce to skip steps.

**Why they exist:** LLMs are excellent at rationalization. They produce plausible-sounding reasons to skip workflows. Prose directives ("be thorough") get acknowledged and ignored under pressure. Pre-written rebuttals in table form are harder to rationalize past.

**How they work in practice:**

When implementing a plan, the agent might think: "This change is small enough to do without phase-by-phase verification." The table in `implement_plan.md` immediately counters: "Small changes cause large outages. Run verification after every phase regardless of size."

The tables are positioned right after the workflow steps they guard — so the agent encounters the rebuttal at exactly the moment it would be tempted to shortcut.

**Tables included in:**

| Command | # of Rebuttals | Guards Against |
|---------|---------------|----------------|
| `/spec` | 4 | Skipping requirements, deferring scope, assuming user clarity |
| `/create_plan` | 4 | Skipping research, oversimplifying phases, rushing, deferring questions |
| `/implement_plan` | 4 | Skipping verification, combining phases, silent adaptation, scope creep |
| `/validate_plan` | 3 | Trusting tests blindly, hiding deviations, skipping manual testing |

### Scope discipline

The `implement_plan` command enforces a hard rule: **if a change requires modifying a file not listed in the plan, the agent must STOP and ask.**

This prevents "drive-by improvements" — those tempting refactors of adjacent code that balloon a focused PR into an unreviewable mess. The agent must present the deviation (what file, why it's needed, what happens without it) and wait for approval.

### Verification gates

Verification between phases is non-negotiable. The agent cannot batch phases or skip the human verification pause. After every phase:
1. Run all automated checks from the plan's success criteria
2. Fix failures before proceeding
3. Present results to the human
4. Wait for confirmation

There is no "skip pause for consecutive phases" option. If you want to batch, you say so explicitly each time.

---

## Workflow Selection

Not sure which command to start with? Use this decision tree from AGENTS.md:

| Scenario | Start With |
|----------|------------|
| Requirements unclear | `/spec` |
| Have a ticket | `/ticket_plan` |
| Want full automation | `/ticket_oneshot` |
| Need to understand code first | `/research_codebase` |
| Have a plan, ready to build | `/implement_plan` |
| Debugging an error | `/debug` |
| Quick prototype, document later | `/founder_mode` |
| Picking up someone's work | `/resume_handoff` |
| Reviewing changes | `/local_review` |

**When in doubt, start with `/spec`.** It's always safe to define requirements first.

---

## Tips for Getting the Most Out of project-specs

### 1. Let the agent research before you answer

When you invoke `/create_plan`, resist the urge to front-load every detail. Give the agent a ticket or brief description and let it research the codebase. Its questions will be more informed, and it will catch things you'd miss.

### 2. Treat verification pauses as features, not friction

The phase-by-phase pause is where you catch problems cheaply. A bug caught between phases costs minutes to fix. The same bug caught after all phases are complete costs hours.

### 3. Use thoughts/ for cross-session memory

If `thoughts_directory: true` in your config, every spec, plan, research finding, and handoff is saved. Future sessions can reference these — the agent doesn't start from zero each time.

### 4. Customize with project-specific skills

The `skills/` directory is empty after setup. Add your project's conventions here:
- Code review standards
- Testing patterns
- Deployment checklists
- API design guidelines

Commands will reference these skills automatically.

### 5. Use /spec to push back on vague tickets

If a ticket says "improve the dashboard performance," running `/spec` will force concrete acceptance criteria: what response time, at what percentile, under what load? This prevents building something that technically "improves performance" but doesn't solve the actual problem.
