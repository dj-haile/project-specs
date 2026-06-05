# Model Assumptions Registry

Every harness component encodes an assumption about what the model can't do on its own. These assumptions become stale as models improve. This file documents each assumption so you know what to re-evaluate when you upgrade models.

> "Every component in a harness encodes an assumption about what the model can't do on its own, and those assumptions are worth stress testing."
> — Anthropic Engineering, "Harness Design for Long-Running Apps" (Mar 2026)

---

## Model-Independent Patterns (survive model upgrades)

These are process-level constraints that don't depend on model capabilities:

- **Structured handoffs** between agents (typed inputs/outputs)
- **Typed output contracts** (Zone 2 — fixed schemas with no freeform channel)
- **Tool Gateway with policy-as-code** (Zone 3 — OPA/Cedar enforcement)
- **Generation/verification separation** (separate agents for writing vs. reviewing)
- **Eval harness** (measurement doesn't depend on what's being measured)
- **Kill switch and rate limiting** (batch-and-confirm on destructive operations)
- **Source attribution on memory entries** (metadata tagging regardless of model)
- **Vault-mediated credentials** (agent never sees API keys)

---

## Model-Dependent Patterns (re-evaluate on every model upgrade)

| Component | Assumption | Calibrated For | Failure Mode That Motivated It |
|-----------|-----------|----------------|-------------------------------|
| Compression at 60% threshold | Models degrade past ~130K tokens (lost-in-the-middle) | General — validated across GPT-4, Sonnet 4.5, Opus 4.6 | Quality cliff in mid-context information retrieval |
| Compression at 80% threshold | Heavy compression needed before hard limits | General | Context overflow and cost spikes |
| Context reset vs. compaction | Context anxiety causes premature task completion | Sonnet 4.5 (severe), Opus 4.6 (improved) | Agent rushing to finish, cutting corners mid-task |
| Task decomposition granularity | Model can't handle full long-horizon tasks in one session | Sonnet 4.5 (required sprint decomposition) | Lost track of goals, incomplete execution |
| Model routing cost tiers | Haiku $0.80 / Sonnet $3 / Opus $5 / Opus >200K $10 | Pricing as of Mar 2026 | Cost overruns from routing everything to Opus |
| Multi-hop reasoning from stubs | Nano models fail at reconstructing from compressed context | Context-Bench: nano <45%, Sonnet 4.5 74%, GPT-5 73% | Silent quality degradation after compression |
| Restorable compression stub format | Agents can reconstruct from source URL + title + 3 key findings | Current frontier models (Sonnet 4.5, Opus 4.6) | Over-sparse stubs that models can't use; over-rich stubs that defeat compression |

---

## Design Decisions: Restorable Compression Stub Format

**VP decision: restorable compression is mandatory.** All observation masking must produce stubs that retain enough metadata for the agent to re-fetch the original content. Dumb stubs (`[Result processed: 847 tokens]`) are not acceptable.

### Standard stub format

```
[Content removed: {source_type}={source_ref} | summary="{one_line}" | key_data: {up_to_3_points}]
```

### Examples by source type

**Web page:**
```
[Web page removed: URL=https://docs.example.com/api-v3 | summary="API rate limits and auth reference" | key_data: rate_limit=1000/min, auth=OAuth2, pagination=cursor-based]
```

**File content:**
```
[File removed: path=/src/auth/handler.ts | summary="OAuth2 token refresh logic" | key_data: refresh_interval=3600s, retry_on_401=true, 240 lines]
```

**Tool result (API response):**
```
[Tool result removed: tool=get_slack_messages(channel=#eng, since=2026-03-01) | summary="23 messages about deploy freeze" | key_data: freeze_starts=Mar 15, requested_by=@alice, 3 threads]
```

**ChromaDB query result:**
```
[Query result removed: query="Project X deadline risk" | summary="4 documents, 2 high-trust" | key_data: earliest_mention=Feb 12, conflicting_dates=[Mar 30, Apr 15], top_source=jira]
```

### Convention rules

1. **source_ref must be re-fetchable** — a URL the agent can visit, a file path it can read, a tool call it can re-execute, or a query it can re-run
2. **summary is one sentence max** — enough to decide whether re-fetching is worth it
3. **key_data is 1-3 data points** — the most decision-relevant facts, not a mini-summary
4. **This is a model-dependent format** — as models improve at reconstructing from sparser metadata, the stub can be simplified. Re-evaluate when upgrading models by testing whether agents can still make correct decisions from stubs alone vs. needing to re-fetch

---

## How to Use This File

**On model upgrade:**
1. Walk the "Model-Dependent Patterns" table
2. For each row, ask: does the new model still need this constraint?
3. Test by relaxing the constraint in eval and measuring quality impact
4. Update the "Calibrated For" column with the new model version and findings

**When adding new harness components:**
1. Ask: does this component encode a model assumption?
2. If yes, add it to the table with the assumption, model version, and failure mode
3. If no (it's a process-level constraint), add it to the Model-Independent list

---

*Last updated: April 1, 2026*
*Source: Learning #14 (Anthropic Engineering), Learning #15 (Manus), Learning #17 (Intercom — frontier vs fine-tune decision)*
