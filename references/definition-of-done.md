# Definition of Done

A standing, project-wide bar that every change must clear before it counts as done.

This is distinct from acceptance criteria. Acceptance criteria vary per task and answer "did we build the right thing?" The Definition of Done is the same every time and answers "is this finished to our standard?" A task is done only when **both** are satisfied.

| | Acceptance Criteria | Definition of Done |
|---|---|---|
| Scope | Specific to one spec/task | Applies to every change |
| Changes | Different each time | Fixed and reused |
| Answers | "Did we build *this thing*?" | "Is it *ready*?" |
| Defined by | `/spec` for each task | This file, once per project |

Commands that must apply this checklist as a final gate: `/validate_plan`, `/local_review`, `/ticket_oneshot`, `/founder_mode`.

## The Standing Checklist

### Correctness
- [ ] All acceptance criteria from the spec are met, each with an explicit pass/fail verdict
- [ ] Behavior verified at runtime — executed, not just compiled or type-checked
- [ ] New behavior is covered by tests that fail without the change and pass with it
- [ ] Existing tests still pass; no regressions introduced

### Code health
- [ ] Follows existing project patterns, or the deviation is documented and justified
- [ ] No commented-out code, debug output, or TODO markers without a linked ticket
- [ ] Error paths are handled, not just the happy path

### Scope
- [ ] Only files listed in the plan were modified; any deviation was approved and recorded
- [ ] No unrelated refactors or "while we're at it" changes bundled in

### Documentation & handoff
- [ ] Documentation updated where the change makes existing docs wrong
- [ ] Plan checkboxes reflect actual completion state
- [ ] Commit messages follow the configured `commit_style`

## Customizing per project

Projects may extend this checklist (never shorten it) by adding a `definition_of_done` section to `specs.config.yaml` listing additional project-specific gates, e.g.:

```yaml
definition_of_done:
  - "Accessibility check passes (axe-core, zero violations)"
  - "Changelog entry added under Unreleased"
```

Commands that apply the Definition of Done should read this key and append its items to the standing checklist above.
