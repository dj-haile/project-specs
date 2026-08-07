# Validation Report Template

The report shape `/validate_plan` produces in Step 3. Copy it, keep the section order, and fill every section — an omitted section reads as a section with nothing to report.

```markdown
## Validation Report: [Plan Name]

### Plan Review Findings (from plan-skeptic — Step 1.5)
- [blocking] [Objection with file:line evidence] — must resolve before trusting the plan
- [concern] [Objection] — conscious trade-off needed
- [note] [Objection]
_(or: "No blocking objections to the plan.")_

### Implementation Status
✓ Phase 1: [Name] - Fully implemented
✓ Phase 2: [Name] - Fully implemented
⚠️ Phase 3: [Name] - Partially implemented (see issues)

### Automated Verification Results
✓ Build passes: [command used]
✓ Tests pass: [command used]
✗ Linting issues: [command used] (3 warnings)
_A green pipeline is not a verdict — the pairing gate accounting below decides the overall result._

### Acceptance Criteria Accounting
| Criterion | Mode | Bound group | Red | Green | Strength | Verdict |
|---|---|---|---|---|---|---|
| `AC-1` | automated | `path/to/file::group_name` | ✓ | ✓ | single-group | pass |
| `AC-2` | automated | none | — | — | — | gate-blocked |

Overall gate result: [success | blocked | incomplete]
Re-run set: [groups] · sample: [group] (hash [first 8 hex] → index [i]) · [agrees | not re-runnable | contradicts]

_Legacy-unlabeled spec: replace the table with a `legacy-unenforced` line and its reason, per Step 2.5. The section is never omitted._

### Code Review Findings

#### Matches Plan:
- [Description with file:line reference]
- [Another match description]

#### Deviations from Plan:
- Used different variable names in [file:line]
- Added extra validation in [file:line] (improvement)

#### Potential Issues:
- Missing validation in [area]
- No error handling in [scenario]

### Manual Testing Required:
1. UI functionality:
   - [ ] Verify [feature] appears correctly
   - [ ] Test error states with invalid input

2. Integration:
   - [ ] Confirm works with existing [component]
   - [ ] Check performance with large datasets

### Recommendations:
- Address [specific issue] before merge
- Consider adding integration test for [scenario]
- Document new API endpoints
```
