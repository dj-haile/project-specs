# Model Selection Guide

The project-specs framework supports multiple Claude models, each optimized for different types of work. Selecting the right model for each task balances capability, speed, and cost.

## Model Overview

### Claude Opus
- **Best For**: Deep reasoning, architecture decisions, planning, complex research
- **Strengths**: Superior reasoning, handles ambiguous problems, excellent at planning and design
- **Speed**: Slowest
- **Cost**: Highest
- **Tokens**: Best for complex, multi-step reasoning

### Claude Sonnet
- **Best For**: Code analysis, implementation, pattern finding, standard tasks
- **Strengths**: Balanced speed and capability, excellent at code generation, good reasoning
- **Speed**: Medium (2-3x faster than Opus)
- **Cost**: Medium
- **Tokens**: Efficient for typical development work

### Claude Haiku
- **Best For**: Simple lookups, classification, formatting, quick searches
- **Strengths**: Very fast, lowest cost, sufficient for straightforward tasks
- **Speed**: Fastest (10x+ faster than Opus)
- **Cost**: Lowest
- **Tokens**: Great for simple, focused queries

## Model Assignment by Task

### Commands

| Command | Recommended | Reason |
|---------|-------------|--------|
| `/research_codebase` | Opus | Needs to understand architecture and patterns deeply |
| `/create_plan` | Opus | Strategic planning requires superior reasoning |
| `/iterate_plan` | Opus | Complex refinement and trade-off analysis |
| `/implement_plan` | Sonnet | Code generation from plan is straightforward |
| `/validate_plan` | Sonnet | Review against plan is pattern-matching |
| `/commit` | Sonnet | Commit message generation is standard |
| `/describe_pr` | Sonnet | PR writing is well-structured |
| `/debug` | Opus | Root cause analysis requires reasoning |
| `/ticket_research` | Opus | Understanding requirements deeply |
| `/ticket_plan` | Opus | Planning from ticket spec |
| `/ticket_impl` | Sonnet | Implementation from plan |
| `/ticket_oneshot` | Opus | Full automation needs end-to-end reasoning |
| `/founder_mode` | Sonnet | Retroactive documentation is pattern-based |
| `/create_handoff` | Sonnet | Summarization is straightforward |
| `/resume_handoff` | Sonnet | Context restoration is lookup-based |

### Agents

| Agent Type | Recommended | Reason |
|------------|-------------|--------|
| codebase-analyzer | Sonnet | Analyze structure and patterns |
| pattern-finder | Sonnet | Locate similar code sections |
| dependency-mapper | Haiku | Simple graph traversal |
| log-analyzer | Haiku | Pattern matching in logs |
| git-historian | Sonnet | Understand code evolution |
| file-locator | Haiku | Simple file search and lookup |
| test-analyzer | Sonnet | Understand test patterns |

## Configuration

Set model defaults in `specs.config.yaml`:

```yaml
models:
  # Default model for all commands/agents
  default: sonnet

  # Override for specific commands
  commands:
    create_plan: opus
    research_codebase: opus
    implement_plan: sonnet
    commit: sonnet

  # Override for specific agent types
  agents:
    codebase-analyzer: sonnet
    log-analyzer: haiku
    file-locator: haiku

  # Per-command override (highest priority)
  # Specified in command YAML frontmatter:
  # ---
  # model: opus
  # ---
```

## Cost and Speed Tradeoffs

### Time Comparison (approximate, single task)
- Opus: 30-60 seconds
- Sonnet: 10-20 seconds
- Haiku: 1-5 seconds

### Cost Comparison (relative)
- Opus: 1.0x (baseline)
- Sonnet: 0.25x
- Haiku: 0.05x

### When to Use Each

#### Use Opus When
- The task is inherently complex (planning, architecture)
- Reasoning quality directly impacts project outcome
- You're making high-stakes decisions
- The task involves ambiguity or trade-offs
- One extra minute of thinking saves hours of implementation
- Examples: `/create_plan`, `/debug production issues`, `/iterate_plan`

#### Use Sonnet When
- The task is well-defined (implement from plan, analyze code)
- Speed matters but quality is non-negotiable
- Pattern matching and code generation
- You're executing a predetermined approach
- The task is moderately complex but not open-ended
- Examples: `/implement_plan`, `/commit`, `/describe_pr`, most agents

#### Use Haiku When
- The task is genuinely simple (search, lookup, classify)
- Speed is critical (real-time response needed)
- Reasoning depth is not required
- You have a clear, narrow problem
- Cost matters more than marginal quality improvement
- Examples: file locator agents, log searchers, simple classification

## Performance Optimization

### Reduce Cost Without Sacrificing Quality
1. Use appropriate model for the task level
2. Pre-filter information before passing to models
3. Use agents to gather data, then Sonnet to synthesize
4. Cache expensive Opus results in thoughts/

### Optimize Speed
1. Use Haiku for simple lookup agents
2. Run independent agents in parallel
3. Break large Opus tasks into smaller Sonnet tasks where possible
4. Use streaming for long outputs

### Optimize Quality
1. Use Opus for planning and decision-making
2. Use Sonnet for implementation
3. Combine outputs intelligently
4. Validate Sonnet results with review steps

## Model Capability Matrix

| Capability | Haiku | Sonnet | Opus |
|------------|-------|--------|------|
| Simple search/lookup | ✓✓ | ✓✓ | ✓ |
| Code analysis | ✓ | ✓✓ | ✓✓ |
| Code generation | ✓ | ✓✓ | ✓✓ |
| Reasoning/planning | ✗ | ✓ | ✓✓ |
| Complex design decisions | ✗ | ✓ | ✓✓ |
| Root cause analysis | ✗ | ✓ | ✓✓ |
| Handling ambiguity | ✗ | ✓ | ✓✓ |

Legend: ✗ (not recommended) | ✓ (works) | ✓✓ (optimal)

## Setting Model per Command

Override default in command YAML frontmatter:

```yaml
---
description: Creates comprehensive implementation plan
model: opus
---

[Command instructions...]
```

## Setting Model per Agent

Override default in agent YAML frontmatter:

```yaml
---
name: codebase-analyzer
description: Analyzes codebase structure
tools:
  - glob
  - grep
  - read
model: sonnet
---

[Agent instructions...]
```

## Examples

### Simple Workflow (Cost-Optimized)
```
Research → Plan → Implement → Commit

/research_codebase (Opus: understand structure)
  → Agents analyze (Sonnet/Haiku: gather data)
/create_plan (Opus: design approach)
/implement_plan (Sonnet: code from plan)
/commit (Sonnet: write message)

Cost: 1x + 0.25x + 0.25x + 0.25x = 1.75x
vs all Opus: 4x
```

### Complex Investigation (Quality-Optimized)
```
/debug production_issue (Opus: root cause analysis)
  → Multiple agents (Sonnet: gather signals)
  → Agents (Haiku: search logs, simple lookups)

Result: Deep reasoning for diagnosis,
targeted data collection, fast searches
```

### Balanced Ticket Workflow
```
/ticket_research (Opus: understand requirements)
/ticket_plan (Opus: design solution)
/ticket_impl (Sonnet: implement)
/commit (Sonnet: message)
/describe_pr (Sonnet: documentation)

Cost: 1.75x
Quality: Very high (planning is optimal)
```

## Monitoring and Adjustment

If a task doesn't work well, try:
- **Too slow?** Try dropping from Opus to Sonnet
- **Quality issues?** Try upgrading from Sonnet to Opus
- **Reasoning errors?** Increase model capability
- **Cost overruns?** Use Haiku for simple components

Review model assignments quarterly based on task outcomes.
