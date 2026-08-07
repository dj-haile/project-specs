# Subagent Capability & Fallback Convention

Commands in this framework research the codebase by spawning specialized
**subagents** (codebase-locator, codebase-analyzer, thoughts-locator, etc.) in
parallel. Subagent support varies by provider, so every subagent invocation is
**capability-gated** against this contract.

## The capability flag

Each provider's `providers/<provider>/manifest.yaml` declares:

```yaml
capabilities:
  subagents: true   # or false
```

As of June 2026 all three supported providers — Claude Code, OpenAI Codex CLI,
and Cursor — set `subagents: true`. The fallback below exists for any future
provider (or a degraded environment) that sets `subagents: false`.

## The contract

> **If `capabilities.subagents: true`** (the fast path): spawn the named agents
> as parallel sub-tasks exactly as the command describes. Each agent runs in its
> own context and returns file:line-referenced findings.
>
> **If `capabilities.subagents: false`** (the inline fallback): do NOT attempt to
> spawn sub-tasks. Instead, perform the same research yourself, inline and
> sequentially, by following the procedure documented in that agent's definition
> file (`agents/<agent-name>.md`). The agent definitions are written as
> standalone instructions, so you can execute them directly. The **output must be
> equivalent** — same files located, same data flow traced, same file:line
> references. Only the execution differs (one context, sequential) and it will be
> slower and use more context budget.

## What never changes regardless of capability

- Read all explicitly-mentioned files FULLY in the main context **before** any
  research (subagent or inline) — this rule is independent of subagent support.
- Verify findings against the actual codebase; don't accept unexpected results.
- Produce specific file:line references.

When a command says *"spawn the **codebase-locator** agent (see
subagent-fallback)"* — the link being `../../conventions/subagent-fallback.md`
relative to the command's location — this contract is what that parenthetical
refers to.

## Sub-task Spawning Best Practices

*Applies when `capabilities.subagents: true`. When subagents are unavailable, follow the same intent inline per the contract above.*

When spawning research sub-tasks:

1. **Spawn multiple tasks in parallel** for efficiency
2. **Each task should be focused** on a specific area
3. **Provide detailed instructions** including:
   - Exactly what to search for
   - Which directories to focus on
   - What information to extract
   - Expected output format
4. **Be EXTREMELY specific about directories**:
   - Include the full path context in your prompts
5. **Specify read-only tools** to use
6. **Request specific file:line references** in responses
7. **Wait for all tasks to complete** before synthesizing
8. **Verify sub-task results**:
   - If a sub-task returns unexpected results, spawn follow-up tasks
   - Cross-check findings against the actual codebase
   - Don't accept results that seem incorrect

Example of spawning multiple tasks:
```python
# Spawn these tasks concurrently:
tasks = [
    Task("Research database schema", db_research_prompt),
    Task("Find API patterns", api_research_prompt),
    Task("Investigate UI components", ui_research_prompt),
    Task("Check test patterns", test_research_prompt)
]
```
