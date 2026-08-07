---
name: stack_pr
description: Decompose a large implementation into a stack of dependency-ordered, reviewable PR branches with scoped review questions
context: core
model: analysis
---

# Stack PR Decomposition

Decompose a large implementation diff into a stack of branches, each small enough to review well. Each layer builds on the one below it and carries its own scoped review questions. Runs between `/validate_plan` and `/describe_pr`.

See [conventions/pr-decomposition.md](../../conventions/pr-decomposition.md) for when to stack versus ship a single PR.

## Setup (read before proceeding)

1. Check that prerequisites are installed:
   - `gh` (GitHub CLI), authenticated
   - `gh-stack` extension: `gh extension list` should show `github/gh-stack`
   - If missing: `gh extension install github/gh-stack`
2. Check if `specs.config.yaml` exists at project root. Read relevant values:
   - `default_base_branch`: trunk the stack targets (default: `main`)
   - `branch_prefix`: prefix for layer branch names
   - `thoughts_directory` / `thoughts_path`: where to save the stack map
3. Confirm the working tree is clean and all implementation changes are committed on the current feature branch. If not, stop and ask the user to commit or stash first.

## When to Use

- The diff crosses the thresholds in [conventions/pr-decomposition.md](../../conventions/pr-decomposition.md) (>500 lines, >3 files across >1 architectural layer, or a plan with >2 phases)
- A reviewer could not hold the whole change in their head in one sitting
- Do NOT stack focused, single-concern changes — a stack of one is overhead with no benefit

## Process

1. **Analyze the change**
   - Run `git diff {base_branch}...HEAD` and list changed files with per-file line counts
   - Read the implementation plan from `{thoughts_path}/plans/` (most recent, or user-referenced)
   - Map each changed file to an architectural layer. Derive layers from the actual change — data model → API → wiring → UI is the canonical example, not a template to force. Plan phases often are the layers.

2. **Propose the decomposition**
   - Present the proposed layers in dependency order: which files, approximate line count, one-line purpose each
   - Every layer must leave the codebase green: it compiles, tests pass, nothing references code that only exists in a higher layer
   - Accept user layer hints as overrides (`/stack_pr [layer hints]`)
   - In interactive mode, confirm the split before creating branches. In CI-mode, proceed with the derived split.

3. **Create the stacked branches**
   - From the base branch, run `gh stack init` to start the stack
   - For each layer, bottom-up:
     - Create the layer branch (`{branch_prefix}{feature}-1-{layer-name}`, numbered by position)
     - Apply only that layer's changes (e.g. `git checkout {feature_branch} -- {layer_files}`, or `git apply` a partial diff when a file spans layers)
     - Commit with a semantic message scoped to the layer
     - Add it to the stack with `gh stack add`
   - Verify each layer builds/tests before moving up. A layer that only passes with a higher layer's code is mis-split — fix the boundary before continuing.

4. **Generate the stack map**
   - Write the map to `{thoughts_path}/prs/{feature}-stack-map.md` (this file is how `/describe_pr` detects the stack)
   - Format:

   ```markdown
   # Stack: {feature name}

   Base: {base_branch}
   Source branch: {feature_branch}
   Plan: {path to plan doc}

   | # | Branch | Layer | Files | Lines | Depends on |
   |---|--------|-------|-------|-------|------------|
   | 1 | feat/x-1-schema | Data model | 3 | ~180 | main |
   | 2 | feat/x-2-api | API endpoints | 4 | ~240 | layer 1 |
   | 3 | feat/x-3-ui | UI components | 5 | ~310 | layer 2 |

   ## Review questions

   ### Layer 1: Data model
   - {scoped question}
   ...
   ```

5. **Write scoped review questions per layer**
   - 2-4 questions per layer that tell the reviewer what to actually check — never generic ("does this look good?")
   - Good questions name a risk specific to the layer: "Does the new index cover the query in layer 2, or will it table-scan?" / "Is the migration reversible?" / "Does the API contract match what the UI in layer 3 consumes?"
   - Derive questions from the plan's success criteria and from what the layer's dependents assume about it

6. **Hand off**
   - Report the stack map location and branch list
   - Next step: `/describe_pr` creates one PR per layer with correct base branches

## Keeping the Stack in Sync

When trunk moves or a lower layer changes after review feedback, sync **locally**:

```bash
gh stack sync
```

`gh stack sync` fetches, cascade-rebases each branch onto its updated parent, and force-pushes atomically with `--force-with-lease`.

**Never use the web UI "Rebase stack" button** on repositories that require signed commits — it rewrites commits server-side, resetting the committer and stripping signatures, which then fails branch protection. See [conventions/pr-decomposition.md](../../conventions/pr-decomposition.md).

## Common Shortcuts to Avoid

- Splitting by file count alone to hit a size target — layers must follow dependency direction, not arithmetic
- Letting a layer depend on code that only exists above it ("it'll be green once the whole stack merges" defeats per-layer review)
- Writing review questions after the fact as summaries of the diff — they must direct the reviewer at risk, not describe the change
- Skipping the per-layer build/test check because the full branch was already validated — validation of the whole does not validate each prefix of the stack

## Red Flags

- A proposed layer over ~400 lines — split it further or justify why it is irreducible
- Circular dependencies between layers — the decomposition is wrong; re-derive
- More than 5-6 layers — reviewers lose the thread; merge adjacent thin layers
- A "misc" or "cleanup" layer collecting homeless changes — every file belongs to a named concern

## Verification

Before reporting done:

1. `gh stack view` shows all layers in the intended order
2. Each layer branch builds and passes tests independently (checked bottom-up during creation)
3. The union of all layer diffs equals the original feature diff — nothing dropped, nothing duplicated (`git diff {base}...{top_layer}` matches `git diff {base}...{feature_branch}`)
4. Stack map file exists in `{thoughts_path}/prs/` and lists every branch
5. Every layer has at least 2 scoped review questions

## Error Handling

- `gh-stack` not installed: offer to install; if declined, stop — do not emulate stacking with raw git
- Dirty working tree: stop and ask the user to commit or stash
- A layer fails its build/test check: stop, report which layer and why, propose a boundary fix
- Diff too entangled to split cleanly (one function spans all layers): report this honestly and recommend a single PR — a forced stack is worse than a big PR
