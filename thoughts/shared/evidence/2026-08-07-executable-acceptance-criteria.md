---
date: 2026-08-07
git_commit: 53b15a5
branch: feature/executable-acceptance-criteria
status: in_progress
tags:
  - acceptance-criteria
  - evidence
  - pairing-gate
  - dogfooding
---

# Evidence — Executable Acceptance Criteria

Red and green records for the five automated criteria bound by
[the plan](../plans/2026-08-07-executable-acceptance-criteria-plan.md), in the
record format that plan fixes (Decision 3). Each record carries the three
required elements: the exact `command`, a re-runnable `code_state`, and the
captured `result`.

`code_state` values are 40-hex commits. `git:53b15a5ac752b74f5578e9100617df7b989c9edc` is the dangling
commit produced by `git stash create` at the end of Phase 1; `git checkout` can
reach it, and every red result below was reproduced from a clean worktree at
that commit before being recorded.

## Status

| Criterion | Test group | Red | Green |
|---|---|---|---|
| `AC-22` | `scripts/validate.py` | recorded | Phase 9 |
| `AC-24` | `scripts/run_evals.py::check_core_command_coverage` | recorded | Phase 9 |
| `AC-27` | `scripts/validate.py::check_gate_sections` | recorded | Phase 3 |
| `AC-28` | `scripts/validate.py::check_gate_single_source` | recorded | Phase 3 |
| `AC-29` | `scripts/validate.py::check_command_size_budget` | recorded | Phase 2 |

All five reds are `strength: single-group` — each invocation runs exactly its
bound group and nothing else. `AC-22`'s bound group *is* `scripts/validate.py`,
so running the whole script is still single-group for it (Decision 3).

---

## Red records — Phase 1

### AC-22 — red

`validate.py` exits 1 because the three new gate checks inside it fail.

```yaml
criterion: AC-22
group: scripts/validate.py
edge: red
command: "python3 scripts/validate.py"
code_state: "git:53b15a5ac752b74f5578e9100617df7b989c9edc"
result: |
  exit 1
  validate.py: 14 error(s) across 26 agent/command files
    ERROR   commands/core/spec.md: section 'Common Shortcuts to Avoid' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/spec.md: section 'Red Flags' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/spec.md: section 'Verification' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/create_plan.md: section 'Common Shortcuts to Avoid' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/create_plan.md: section 'Red Flags' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/create_plan.md: section 'Verification' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/implement_plan.md: section 'Common Shortcuts to Avoid' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/implement_plan.md: section 'Red Flags' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/implement_plan.md: section 'Verification' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/validate_plan.md: section 'Common Shortcuts to Avoid' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/validate_plan.md: section 'Red Flags' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/validate_plan.md: section 'Verification' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   conventions/criterion-binding.md: the pairing gate's single normative source does not exist
    ERROR   commands/core/create_plan.md: 549 lines exceeds the 500-line ceiling — extract body text to a convention or reference file (conventions/three-layer-architecture.md:182-185)
strength: single-group
recorded_at: "2026-08-07T18:18:26Z"
```

### AC-24 — red

`evals/cases/validate_plan.json` does not exist.

```yaml
criterion: AC-24
group: scripts/run_evals.py::check_core_command_coverage
edge: red
command: "python3 scripts/run_evals.py --check check_core_command_coverage"
code_state: "git:53b15a5ac752b74f5578e9100617df7b989c9edc"
result: |
  exit 1
  run_evals.py [check_core_command_coverage]: 1 failure(s)
    FAIL  evals/cases/validate_plan.json: missing — every core routed command needs a case file
strength: single-group
recorded_at: "2026-08-07T18:18:26Z"
```

### AC-27 — red

The token `pairing gate` appears in no core command's Common Shortcuts / Red Flags / Verification section.

```yaml
criterion: AC-27
group: scripts/validate.py::check_gate_sections
edge: red
command: "python3 scripts/validate.py --check check_gate_sections"
code_state: "git:53b15a5ac752b74f5578e9100617df7b989c9edc"
result: |
  exit 1
  validate.py [check_gate_sections]: 12 error(s)
    ERROR   commands/core/spec.md: section 'Common Shortcuts to Avoid' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/spec.md: section 'Red Flags' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/spec.md: section 'Verification' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/create_plan.md: section 'Common Shortcuts to Avoid' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/create_plan.md: section 'Red Flags' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/create_plan.md: section 'Verification' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/implement_plan.md: section 'Common Shortcuts to Avoid' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/implement_plan.md: section 'Red Flags' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/implement_plan.md: section 'Verification' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/validate_plan.md: section 'Common Shortcuts to Avoid' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/validate_plan.md: section 'Red Flags' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
    ERROR   commands/core/validate_plan.md: section 'Verification' never mentions the 'pairing gate' obligation — see conventions/criterion-binding.md
strength: single-group
recorded_at: "2026-08-07T18:18:26Z"
```

### AC-28 — red

`conventions/criterion-binding.md` does not exist and no command links to it.

```yaml
criterion: AC-28
group: scripts/validate.py::check_gate_single_source
edge: red
command: "python3 scripts/validate.py --check check_gate_single_source"
code_state: "git:53b15a5ac752b74f5578e9100617df7b989c9edc"
result: |
  exit 1
  validate.py [check_gate_single_source]: 1 error(s)
    ERROR   conventions/criterion-binding.md: the pairing gate's single normative source does not exist
strength: single-group
recorded_at: "2026-08-07T18:18:26Z"
```

### AC-29 — red

`create_plan.md` is 549 lines against an enforced ceiling of 500.

```yaml
criterion: AC-29
group: scripts/validate.py::check_command_size_budget
edge: red
command: "python3 scripts/validate.py --check check_command_size_budget"
code_state: "git:53b15a5ac752b74f5578e9100617df7b989c9edc"
result: |
  exit 1
  validate.py [check_command_size_budget]: 1 error(s)
    ERROR   commands/core/create_plan.md: 549 lines exceeds the 500-line ceiling — extract body text to a convention or reference file (conventions/three-layer-architecture.md:182-185)
strength: single-group
recorded_at: "2026-08-07T18:18:26Z"
```

---

## Green records

Added as each criterion's satisfying change lands: `AC-29` in Phase 2, `AC-27`
and `AC-28` in Phase 3, `AC-22` and `AC-24` in Phase 9. Each green record must
carry a `code_state` different from its red record's.

## AC-29 — green

```yaml
criterion: AC-29
group: "scripts/validate.py::check_command_size_budget"
command: "python3 scripts/validate.py --check check_command_size_budget"
code_state: "git:37b4ea7"
result: "exit 0 — all four core commands within ceilings (create_plan.md 460/500)"
strength: single-group
recorded_at: "2026-08-07"
phase: 2
```
