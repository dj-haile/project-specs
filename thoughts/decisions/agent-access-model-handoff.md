# Handoff: Apply Agent Access Model Principles to project-specs

**Created:** 2026-08-07
**Status:** Ready to implement
**Source:** Cloudflare Agent Access Model (Source 84 in playbook)
**Why this matters:** project-specs agents currently run with ambient access to everything the user has access to. As you deploy these agents to more teams and more sensitive codebases, you need task-scoped access control — not just "can this user run this agent" but "can this agent, on this task, access this resource."

## What applies to project-specs today

### 1. Task-scoped credentials instead of standing keys

**Current state:** Agents inherit whatever credentials the user has configured (GitHub tokens, API keys in environment). An agent running `/implement_plan` has the same access as one running `/research_codebase`, even though research needs read-only and implementation needs write.

**Change:** Add a `permissions` block to each command/agent definition specifying what it needs:

```yaml
# commands/research-codebase/command.yaml
permissions:
  github: read
  filesystem: read
  thoughts_directory: write

# commands/implement-plan/command.yaml
permissions:
  github: read_write
  filesystem: write
  thoughts_directory: write
```

The runner checks declared permissions against the actual task before dispatch. An agent that declares `github: read` cannot push commits even if the user's token allows it.

### 2. Trust Ratchet for destructive operations

**Current state:** If an agent encounters an error mid-implementation, it retries with the same permissions. There's no mechanism to reduce capability when something goes wrong.

**Change:** Add ratchet events to `conventions/workflow-patterns.md`:

- **Test failure after code change** → remove `filesystem: write`, agent switches to analysis-only mode and reports what went wrong
- **Unexpected file deletion** → remove `filesystem: write` immediately, log the event, require human re-authorization
- **Git conflict during commit** → remove `github: write`, agent reports the conflict for human resolution

The ratchet is one-way within a task. The agent can't re-escalate its own permissions. A new task starts fresh.

### 3. Frozen request pattern on tool calls

**Current state:** Agent decides to call a tool, then calls it. Nothing prevents the arguments from changing between the decision and the execution (e.g., an agent decides to write to `src/config.ts` but a prompt injection mid-chain redirects to `.env`).

**Change:** Add a `FrozenRequest` convention to `conventions/three-layer-architecture.md`:

- Skills construct the full request (file path, operation, content) before execution
- The request is validated against the command's permission scope
- The validated request is what executes — no re-evaluation of arguments after authorization

This is most important for the `/commit` and `/implement_plan` commands where file writes happen.

### 4. Activity log for grant review

**Current state:** Agent actions are logged in `thoughts/` as human-readable markdown. No structured telemetry.

**Change:** Add structured event logging alongside the human-readable output:

```yaml
# thoughts/activity-log/2026-08-07T14-30-00.yaml
task_id: implement-plan-abc123
events:
  - type: tool_call
    tool: file_write
    resource: src/config.ts
    decision: authorized
    permission_source: command.yaml
  - type: tool_call
    tool: git_push
    resource: origin/feature-branch
    decision: denied
    reason: permission scope is read_only for github
```

This log feeds future permission refinement — you can review what agents actually accessed and tighten templates accordingly.

### 5. Convention: `conventions/agent-access-control.md`

New convention document covering:
- Permission declaration per command/agent
- Ratchet events and one-way capability reduction
- Frozen request validation on tool calls
- Activity log schema
- Multi-principal rule: if multiple users share an agent context (e.g., in a team setting), treat each user's work as a separate task with separate permissions

## Implementation order

1. Add `permissions` block schema to command/agent YAML format
2. Write `conventions/agent-access-control.md`
3. Update runner to enforce declared permissions at dispatch
4. Add ratchet events to workflow patterns
5. Add structured activity logging
6. Retrofit existing commands with permission declarations
7. Test: verify an agent with `github: read` cannot push, even with a write-capable token

## What this does NOT cover

- **Multiplayer access control** — Cloudflare explicitly marks this unsolved. Don't try to build it yet.
- **Network-layer enforcement** — project-specs agents run locally, so network egress controls aren't applicable. If agents move to cloud execution, revisit.
- **DPoP/RFC 8693 credential binding** — overkill for local agent execution. Relevant when agents call remote APIs on behalf of users.
