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
