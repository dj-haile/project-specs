# Handoff: Add Stacked PR Decomposition to project-specs

**Created:** 2026-08-07
**Status:** Ready to implement
**Source:** GitHub stacked PRs (Source 89 in playbook), PostHog PR stacking (Source 27)
**Why this matters:** project-specs currently produces one PR per feature via `/describe_pr`. As agent-generated code volume grows, single large PRs become unreviewable. GitHub now has native stacked PR support with an agent skill — this is the infrastructure that makes decomposition practical.

## What to change

### 1. New command: `/stack_pr`

Add a command between `/implement_plan` and `/describe_pr` that decomposes a large implementation into reviewable layers.

**Location:** `commands/stack-pr/`

**Behavior:**
- Reads the implementation diff and the plan from `thoughts/plans/`
- Decomposes into layers by dependency order (data model → API → wiring → UI is GitHub's worked example, but the layers should be derived from the actual change)
- Each layer gets its own branch stacked on the previous one
- Each layer gets scoped review questions (not just "LGTM" — what specifically should the reviewer check for this layer?)
- Outputs a stack map showing the dependency chain

**Dependencies:**
- `gh extension install github/gh-stack` (GitHub CLI extension)
- Or: `npx skills add github/gh-stack` for agent consumption

### 2. Update workflow-patterns.md

Add a step between "Output: Modified files, code changes" and the commit step:

```
User: /stack_pr [optional: layer hints]
  ↓
Stack Command: Analyze diff, decompose into reviewable layers, create stacked branches
  ↓
Output: Stack of branches, each with scoped review questions
  ↓
---
User: /describe_pr [creates one PR per stack layer]
```

### 3. Update `/describe_pr` to be stack-aware

When a stack exists, `/describe_pr` should:
- Create one PR per layer, not one PR for the whole feature
- Include the stack map at the top of each PR
- Include layer-specific review questions
- Set the base branch correctly (each layer targets the one below it)

### 4. Add convention: `conventions/pr-decomposition.md`

Rules for when to stack vs. single PR:
- **Stack when:** diff touches >3 files across >1 layer (data/API/UI), or diff is >500 lines, or implementation plan has >2 phases
- **Single PR when:** change is focused, <300 lines, single concern
- Agent should suggest stacking when the threshold is hit, not require explicit invocation

### 5. Caveat from GitHub's article

The web-based "Rebase stack" button resets the committer and unsigns commits — breaks branch protection that requires signed commits. Use `gh stack rebase && gh stack push` locally instead. Document this in the convention.

## Implementation order

1. Install `gh-stack` extension
2. Write `commands/stack-pr/` command
3. Update `conventions/workflow-patterns.md`
4. Update `commands/describe-pr/` to be stack-aware
5. Add `conventions/pr-decomposition.md`
6. Test on a real multi-layer feature branch
