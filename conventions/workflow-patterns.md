# Workflow Patterns

The project-specs framework provides standardized workflow patterns for common development tasks. Each pattern combines commands and agents in a proven sequence.

## 1. Research → Plan → Implement → Review

The **full feature development cycle** from investigation through deployment.

### Flow

```
User: /research_codebase [feature/issue]
  ↓
Research Agent: Analyze codebase, find affected areas, identify patterns
  ↓
Output: thoughts/research/YYYY-MM-DD_findings.md
  ↓
---
User: /create_plan [based on research findings]
  ↓
Plan Command: Synthesize findings, ask clarifying questions, create detailed plan
  ↓
Output: thoughts/plans/YYYY-MM-DD_plan.md
  ↓
---
User: /implement_plan [with plan reference]
  ↓
Implementation Command: Break down plan steps, generate code/changes
  ↓
Output: Modified files, code changes
  ↓
---
User: /validate_plan [review changes against plan]
  ↓
Validation: Ensure implementation matches plan, identify gaps
  ↓
Output: Validation report
  ↓
---
User: /commit [with validation context]
  ↓
Commit Command: Generate semantic commit message, create commit
  ↓
Output: Committed changes
  ↓
---
User: /describe_pr [to create PR]
  ↓
PR Description Command: Generate PR title, description, test plan
  ↓
Output: Ready-to-merge PR with context
```

### When to Use
- New features from scratch
- Major refactors or architectural changes
- Complex bug fixes requiring analysis
- Work that spans multiple files or systems

### Key Commands
- `/research_codebase` - Understand the landscape
- `/create_plan` - Design the approach
- `/implement_plan` - Execute the plan
- `/validate_plan` - Verify correctness
- `/commit` - Persist changes
- `/describe_pr` - Document and create PR

---

## 2. Ticket-Driven Workflow

**Integration with external ticket systems** (Jira, GitHub Issues, Linear, etc.).

### Flow

```
Ticket assigned to you (ticket ID: ENG-1234)
  ↓
User: /ticket_research ENG-1234
  ↓
Research Agent: Fetch ticket details, analyze requirements, link to code
  ↓
Output: thoughts/tickets/ENG-1234-research.md
  ↓
---
User: /ticket_plan ENG-1234
  ↓
Plan Command: Create implementation plan from ticket spec
  ↓
Output: thoughts/tickets/ENG-1234-plan.md
  ↓
---
Option A: Full automation
User: /ticket_oneshot ENG-1234
  ↓
Command: Implement, test, commit, create PR in one run
  (Non-interactive, requires CI-mode enabled)
  ↓
Output: Ready-to-review PR
  ↓
---
Option B: Step-by-step
User: /ticket_impl ENG-1234
  ↓
Implementation: Follow plan, generate code
  ↓
Output: Changes ready to commit
```

### Configuration

```yaml
# specs.config.yaml
tickets:
  enabled: true
  system: jira  # or github, linear, etc.
  pattern: "ENG-\\d+"
  api_token_env: JIRA_API_TOKEN
```

### When to Use
- You're working from a backlog or issue tracker
- Ticket system is your source of truth
- You need automated link-back to ticket
- Team prefers end-to-end traceability

### Key Commands
- `/ticket_research` - Understand ticket requirements
- `/ticket_plan` - Design solution
- `/ticket_impl` - Implement the ticket
- `/ticket_oneshot` - Automated end-to-end (CI-mode)

---

## 3. Handoff Pattern

**Session continuity and team transitions** using documented context.

### Flow

```
Developer A (end of session):
  ↓
/create_handoff
  ↓
Handoff Command: Summarize progress, open questions, next steps
  ↓
Output: thoughts/handoffs/YYYY-MM-DD-session-end.md
  Includes:
    - What was completed
    - What's partially done
    - Blockers and decisions needed
    - Files touched, branches, commits
    - Recommended next steps
  ↓
---
Developer B (start of next session):
  ↓
/resume_handoff [or /resume_handoff --latest]
  ↓
Handoff Command: Read latest handoff, restore branch context, ask follow-ups
  ↓
Output: Session context restored, branch checkedout, ready to continue
```

### Handoff Document Structure

```yaml
---
date: 2026-03-24
branch: feature/auth-refactor
last_commit: 5f3a2b1
status: in_progress
---

## Session Summary
Completed auth refactor phase 1: moved credentials to env vars.

## Progress
- [x] Extract API keys to environment
- [x] Update config loader
- [x] Add secrets rotation script
- [ ] Migrate tests to new system
- [ ] Update documentation

## Blockers
- Waiting on security review for token rotation approach
- Need decision: legacy token support or hard cutover?

## Files Modified
- config/auth.py
- scripts/secrets-rotate.sh
- tests/test_auth.py

## Next Steps
1. Migrate all unit tests to new auth system
2. Update integration tests
3. Deploy to staging
4. Collect feedback before prod rollout

## Open Questions
- How long should we support legacy tokens?
- Should we auto-rotate or manual trigger?
- Need to test with load?
```

### When to Use
- Team with multiple developers
- Complex, multi-session projects
- When context needs to transfer between people
- Resuming work after interruptions

### Key Commands
- `/create_handoff` - Document for next person
- `/resume_handoff` - Pick up where you left off

---

## 4. Debug Pattern

**Parallel investigation** of complex issues using multiple agents.

### Flow

```
Issue reported: "Service crashes on high load"
  ↓
User: /debug issue-identifier
  ↓
Debug Command spawns agents in parallel:
  ├─ Log Analyzer Agent: search logs, find error patterns
  ├─ Git History Agent: find recent changes, commits
  ├─ Database Agent: check schema, query performance
  └─ Config Agent: verify settings, environment
  ↓
Agents report findings:
  - Logs: OOM error on 50k+ concurrent users
  - Git: Resource limits not updated 3 weeks ago
  - DB: Missing index on users.created_at
  - Config: Memory limit set to 256MB (too low)
  ↓
Output: thoughts/research/YYYY-MM-DD_debug-findings.md
  with hypothesis and remediation steps
  ↓
User: /implement_fix [based on debug findings]
```

### When to Use
- Investigating production issues
- Root cause analysis of failures
- Performance problems
- When you need to examine multiple signals at once

### Key Commands
- `/debug` - Spawn parallel investigation agents
- `/implement_fix` - Act on findings

---

## 5. Founder Mode

**Post-hoc documentation** for work that was already implemented.

### Flow

```
You've already implemented a feature (files modified, tested, ready)
  ↓
User: /founder_mode [brief description]
  ↓
Founder Mode Command:
  ├─ Analyze what you changed
  ├─ Create backfill ticket (or ticket reference)
  ├─ Generate retrospective plan doc
  ├─ Create semantic commit message
  └─ Generate PR description
  ↓
Output: Ticket link, commit message, PR ready to merge
  (All documentation created retroactively)
  ↓
You review and adjust as needed
```

### When to Use
- Quick prototypes that worked out
- Emergency fixes needing documentation
- Spike work that turned into production code
- When you implemented first, documented later

### Key Commands
- `/founder_mode` - Retroactively document implementation

---

## Pattern Selection Guide

| Pattern | Best For | Duration | Team Size |
|---------|----------|----------|-----------|
| Research → Plan → Implement → Review | Features, refactors, complex work | Hours to days | Any |
| Ticket-Driven | Backlog work, external requirements | Hours to days | Teams |
| Handoff | Multi-person projects | Ongoing | Teams |
| Debug | Production issues, investigations | Minutes to hours | Any |
| Founder Mode | Quick iterations, prototypes | Minutes | Solo |

## Combining Patterns

Patterns can combine:

```
Ticket-driven + Research → Plan:
  /ticket_research → /create_plan → /implement_plan → /commit

Handoff + Ticket-driven:
  /resume_handoff → /ticket_impl → /ticket_oneshot → /create_handoff

Debug + Founder Mode:
  /debug → analyze → implement → /founder_mode to document
```

## Configuration

Control pattern availability in `specs.config.yaml`:

```yaml
workflows:
  research_plan_implement: true
  ticket_driven: true
  handoff: true
  debug: true
  founder_mode: true
```

---

## 6. Spec-First Workflow

**Requirements definition before planning** to catch assumptions early.

### Flow

```
User: /spec [feature description or ticket reference]
  ↓
Spec Command: Research codebase, define requirements, acceptance criteria
  ↓
Output: thoughts/specs/YYYY-MM-DD_requirements.md
  ↓
---
User: /create_plan [referencing spec document]
  ↓
Plan Command: Uses spec's acceptance criteria as success criteria
  ↓
Output: thoughts/plans/YYYY-MM-DD_plan.md
  ↓
---
User: /implement_plan → /validate_plan → /commit → /describe_pr
```

### When to Use
- Features where requirements aren't fully understood
- Work where scope creep is a risk
- Tasks involving multiple stakeholders with different expectations
- Anytime you find yourself saying "let me just start coding and figure it out"

### Key Commands
- `/spec` - Define what success looks like
- `/create_plan` - Design how to get there (uses spec as input)

### Why This Matters
Starting at `/create_plan` merges requirements discovery and implementation planning into one step. This means the agent optimizes for "get to the plan" and rushes past assumptions it should challenge. The `/spec` command forces a deliberate pause to define what we're building before deciding how.
