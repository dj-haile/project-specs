# PR Decomposition

One-line summary: when a change is too big to review as one PR, split it into a stack of dependency-ordered branches with `/stack_pr`; otherwise ship a single PR.

As agent-generated code volume grows, the bottleneck moves from writing code to reviewing it. A 1,500-line PR gets a worse review than five 300-line PRs of the same content. Stacking restores reviewability without slowing the author down.

## When to Stack

Stack when **any** of these holds:

| Signal | Threshold |
|--------|-----------|
| Diff size | > 500 lines |
| Spread | > 3 files across more than one architectural layer (data / API / UI) |
| Plan shape | Implementation plan has > 2 phases |

## When to Ship a Single PR

Single PR when **all** of these hold:

- Change is focused on a single concern
- Diff is under 300 lines
- A reviewer can hold the whole change in their head in one sitting

## The 300-500 Line Middle Ground

Between the thresholds, use judgment and lean single PR. Stack only if the change crosses architectural layers with a real dependency seam between them — a 400-line change inside one module reviews fine as one PR; a 350-line change that touches a migration, an endpoint, and a component may not.

## Suggest, Don't Require

Commands that see the diff (`/implement_plan`, `/validate_plan`, `/describe_pr`) should **suggest** running `/stack_pr` when a threshold is crossed — state which threshold and the current numbers. The user decides. Never auto-stack, and never block on the suggestion in CI-mode; note it in output and continue.

## Layer Rules

- Layers follow **dependency direction**: each layer may depend only on layers below it. Data model → API → wiring → UI is the canonical shape, but derive layers from the actual change (plan phases are often the natural cut).
- Every layer leaves the codebase **green**: builds, tests pass, no references to code that only exists higher in the stack.
- Each layer gets **scoped review questions** — 2-4 questions naming layer-specific risks, not "LGTM?" prompts. The question tells the reviewer where the risk lives.
- Keep stacks to **5-6 layers max**; merge adjacent thin layers rather than fragmenting.

## Tooling

The stack workflow uses the official GitHub CLI extension:

```bash
gh extension install github/gh-stack
```

Key commands: `gh stack init` (start), `gh stack add` (add a layer), `gh stack submit` (push branches, open/update PRs), `gh stack sync` (fetch, cascade-rebase, force-push safely), `gh stack view` (inspect).

## Caveat: Signed Commits and the Web "Rebase Stack" Button

GitHub's web UI offers a "Rebase stack" button on stacked PRs. **Do not use it on repositories whose branch protection requires signed commits.** The server-side rebase resets the committer and strips commit signatures, so the rebased commits fail the signed-commit check and the stack cannot merge.

Instead, rebase locally where your signing key lives:

```bash
gh stack sync
```

This cascade-rebases every branch onto its updated parent and pushes atomically with `--force-with-lease`, preserving your commit signatures.

## Workflow Position

```
/implement_plan → /validate_plan → /stack_pr → /describe_pr (one PR per layer)
                                └─ or ────→ /commit → /describe_pr (single PR)
```

`/stack_pr` commits each layer to its own branch, so the stacked path does not use `/commit` separately. `/describe_pr` detects a stack via the stack map file in `{thoughts_path}/prs/` and switches to per-layer PR mode; with no stack present its behavior is unchanged.

See [commands/core/stack_pr.md](../commands/core/stack_pr.md) for the full decomposition procedure and [workflow-patterns.md](workflow-patterns.md) for the surrounding workflow.
