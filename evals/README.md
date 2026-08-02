# Routing Evals

A command or agent is only useful if the user's phrasing actually reaches it.
The **frontmatter `description`** (plus the `name`) is the routing surface: when
a user types a request, the model picks a command by matching their words against
those descriptions. If two descriptions overlap, or one is diluted by filler, the
wrong command runs — silently.

These evals are a deterministic, CI-safe proxy for that match. They catch a
description edit that quietly breaks routing at PR time, instead of in the field.

Run them:

```bash
python3 scripts/run_evals.py
```

Debug a single phrasing (shows the top-10 ranking):

```bash
python3 scripts/run_evals.py --explain "create a plan for the top ticket"
```

## How it works

`scripts/run_evals.py` (Python + PyYAML only — no Node, no network, no
randomness) does three things:

1. **Indexes** every command (`commands/**/*.md`) and agent (`agents/*.md`) into
   a single unified TF‑IDF space over their `name` + `description`. Text is
   lowercased, tokenized, stop‑worded, and lightly **stemmed** (so
   `plans`/`planning`/`planned` all fold to `plan`). Vectors are L2‑normalized,
   so ranking is cosine similarity. One unified space matters: a prompt competes
   against **all** commands and agents at once — the realistic setting.

2. **Runs cases** from `evals/cases/*.json`:
   - **positive** prompts must rank their command within `top_k`.
   - **negative** prompts must _not_ rank the command `#1`; if an `owner` is
     given, the owner must outrank the command (the prompt belongs to the owner).

3. **Detects collisions**: any two descriptions whose cosine similarity meets or
   exceeds `COLLISION_THRESHOLD` (currently `0.72`) are flagged as a routing
   hazard — too alike to route between reliably.

## Case schema

One JSON file per command/agent, named `evals/cases/<command>.json`:

```json
{
  "command": "create_plan",
  "trigger": {
    "positive": [
      { "prompt": "create an implementation plan for adding OAuth login", "top_k": 1 }
    ],
    "negative": [
      { "prompt": "create a plan for the highest priority ticket", "owner": "ticket_plan" }
    ]
  }
}
```

- `command` — the command/agent frontmatter `name` this file is about.
- `positive[].prompt` — a natural user phrasing that should route here.
- `positive[].top_k` — allowed rank (default `1`). Use `2` only for genuinely
  tight clusters, and prefer sharpening the description over loosening `top_k`.
- `negative[].prompt` — a phrasing that should route _elsewhere_.
- `negative[].owner` — optional; the command the prompt actually belongs to.
  The eval asserts `owner` outranks `command`.

## A failure means "fix the description," not "fix the eval"

When a case fails, the default assumption is that a **description** is wrong —
too vague, too jokey, or overlapping a neighbor — not that the test is unfair.
The prompts here are natural things a user would type; if a natural phrasing for
command X routes to command Y, users will hit the same wall.

In order of preference, resolve a failure by:

1. **Sharpening the losing description** so its distinctive words carry more
   signal (name the artifact it produces, the trigger, the phase). This is the
   fix that actually helps users.
2. **Differentiating two overlapping descriptions** so the collision check and
   the negative cases both pass. Ask: what one word tells them apart? Make sure
   both descriptions contain their own side of it.
3. **Only if the phrasing was genuinely ambiguous** (a prompt a human router
   couldn't confidently place either): reword the case prompt, or raise `top_k`
   to `2` — and leave a comment in the PR explaining why.

Editing a case to paper over a real routing bug defeats the purpose. Reach for
option 3 last.

## Priority collision pairs covered

These near-neighbors are the ones most likely to steal each other's prompts;
each has positive cases for both sides plus cross‑guarding negatives:

| Pair | Distinction |
|------|-------------|
| `create_plan` vs `ticket_plan` | free-form feature plan vs plan the top ticket |
| `research_codebase` vs `ticket_research` | document the codebase vs investigate a ticket |
| `ticket_oneshot` vs `founder_mode` | automate a ticket end-to-end vs retro-document a shipped feature |
| `codebase-locator` vs `codebase-pattern-finder` | where files live vs example code to model after |
| `thoughts-locator` vs `thoughts-analyzer` | find thoughts docs vs deep-dive one doc |

## Adding coverage

Add or extend a `evals/cases/<command>.json` file. Keep prompts natural (write
what a user would actually type, not a keyword-stuffed restatement of the
description). Run `python3 scripts/run_evals.py` locally; CI runs it on every PR.
