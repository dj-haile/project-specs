---
name: validate_plan
description: Validate implementation against plan, verify success criteria, identify issues
model: planning
---

# Validate Plan

You are tasked with validating that an implementation plan was correctly executed, verifying all success criteria and identifying any deviations or issues.

## Setup (read before proceeding)

1. Check if `specs.config.yaml` exists at project root
2. Note the plan storage location for retrieving plan files
3. Prepare to review implementation against plan specifications

## Initial Setup

When invoked:
1. **Determine context** - Are you in an existing conversation or starting fresh?
   - If existing: Review what was implemented in this session
   - If fresh: Need to discover what was done through git and codebase analysis

2. **Locate the plan**:
   - If plan path provided, use it
   - Otherwise, search recent commits for plan references or ask user

3. **Gather implementation evidence**:
   ```bash
   # Check recent commits
   git log --oneline -n 20
   git diff HEAD~N..HEAD  # Where N covers implementation commits
   ```

## Validation Process

### Step 1: Context Discovery

If starting fresh or need more context:

1. **Read the implementation plan** completely
2. **Identify what should have changed**:
   - List all files that should be modified
   - Note all success criteria (automated and manual)
   - Identify key functionality to verify

3. **Discover implementation** (capability-gated — see [subagent-fallback](../../conventions/subagent-fallback.md)): if `capabilities.subagents: true`, run the tasks below as parallel sub-tasks; if `false`, perform each one inline and sequentially. Either way the verification output is the same.
   ```
   Task 1 - Verify code changes:
   Find all modified files related to [feature].
   Compare actual changes to plan specifications.
   Return: File-by-file comparison of planned vs actual

   Task 2 - Verify test coverage:
   Check if tests were added/modified as specified.
   Run test commands and capture results.
   Return: Test status and any missing coverage

   Task 3 - Verify integration:
   Confirm code integrates properly with existing codebase.
   Check for regressions or compatibility issues.
   Return: Integration validation results
   ```

### Step 1.5: Adversarial Plan Review (capability-gated)

Before validating the implementation against the plan, subject **the plan
itself** to a fresh-context skeptic. A plan that was wrong to begin with will
pass a validation that only checks "did we build what the plan said." This step
catches plans built on unverified assumptions, uncheckable success criteria, or
scope that drifted from the spec.

Capability-gated — see [subagent-fallback](../../conventions/subagent-fallback.md):

- **If `capabilities.subagents: true`**: spawn the **plan-skeptic** agent (see
  [agents/plan-skeptic.md](../../agents/plan-skeptic.md)) as a sub-task. Pass it
  the plan path and the spec/requirements it claims to satisfy. It returns
  numbered objections by severity (blocking/concern/note) with `file:line`
  evidence, or an explicit "no blocking objections" verdict.
- **If `capabilities.subagents: false`**: perform the same review inline and
  sequentially by following the procedure in `agents/plan-skeptic.md` yourself —
  same hunt-list, same output format, same file:line evidence. Only the
  execution differs.

Fold the skeptic's objections into the validation report (see the "Plan Review
Findings" block in Step 3). **Blocking** objections mean the plan — not just the
implementation — needs attention; surface them prominently rather than validating
against a plan that is itself unsound. This step reviews the plan's soundness; it
does not replace validating the implementation against it.

### Step 2: Systematic Validation

For each phase in the plan:

1. **Check completion status**:
   - Look for checkmarks in the plan (- [x])
   - Verify the actual code matches claimed completion

2. **Run automated verification**:
   - Execute each command from "Automated Verification"
   - Document pass/fail status
   - If failures, investigate root cause

3. **Assess manual criteria**:
   - List what needs manual testing
   - Provide clear steps for user verification

4. **Think deeply about edge cases**:
   - Were error conditions handled?
   - Are there missing validations?
   - Could the implementation break existing functionality?

### Step 2.5: Per-Criterion Accounting

Build the accounting from the **spec's** criterion list, never from the plan's restatement of it. A criterion the plan never mentions still gets a record, marked unbound. Emit exactly one record per criterion — no omissions, no merges — carrying identifier, mode, bound test group from the plan (or `none`), red status, green status, evidence strength, and verdict.

Take the verdict vocabulary and the overall-result rule from [criterion-binding](../../conventions/criterion-binding.md) §7. Two consequences to apply directly: an `automated` criterion with no bound group is blocked, and the report names its identifier; and the overall result is not success while any such criterion exists, however green the plan's own check list came back.

### Step 3: Generate Validation Report

Create comprehensive validation summary:

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

## Working with Existing Context

If you were part of the implementation:
- Review the conversation history
- Check your todo list for what was completed
- Focus validation on work done in this session
- Be honest about any shortcuts or incomplete items


## Common Shortcuts to Avoid

When validating a plan, you will be tempted to rationalize incomplete verification. These are the most common excuses and why they're wrong:

| Excuse | Rebuttal |
|--------|----------|
| "Tests pass, so the implementation is correct." | Passing tests are evidence, not proof. Did you verify user-visible behavior? Did you check for regressions in related features? |
| "This deviation from the plan is an improvement, not a problem." | Document it anyway. Undocumented deviations compound. The next person reading the plan will be confused. |
| "Manual testing isn't needed for backend-only changes." | Backend changes surface as user-visible behavior somewhere. Identify where and verify. |
| "Every check the plan named passed, so I'll report success." | The plan's check list does not decide the result — the pairing gate does. One unbound criterion makes the run blocked no matter how green everything else came back. |

## Important Guidelines

1. **Be thorough but practical** - Focus on what matters
2. **Run all automated checks** - Don't skip verification commands
3. **Document everything** - Both successes and issues
4. **Think critically** - Question if the implementation truly solves the problem
5. **Consider maintenance** - Will this be maintainable long-term?

## Validation Checklist

Apply the standing [Definition of Done](../../references/definition-of-done.md) as the final gate — it covers the fixed, project-wide bar. The list below covers plan-specific verification. Both must pass.

Always verify:
- [ ] All phases marked complete are actually done
- [ ] Automated tests pass
- [ ] Code follows existing patterns
- [ ] No regressions introduced
- [ ] Error handling is robust
- [ ] Documentation updated if needed
- [ ] Manual test steps are clear

## Relationship to Other Commands

Recommended workflow:
1. `/create_plan` - Create the implementation plan
2. `/implement_plan` - Execute the implementation
3. `/validate_plan` - Verify implementation correctness
4. Commit and submit for review

The validation works best after implementation is complete and code is ready for review.

Remember: Good validation catches issues before they reach production. Be constructive but thorough in identifying gaps or improvements.

## Red Flags

Observable signs that you are drifting off this workflow:

- You are confirming phases as complete by reading the plan's checkboxes instead of the actual code
- You skipped running an automated check because "implementation already ran it"
- Your validation report contains only successes — real validation almost always surfaces at least minor issues or observations
- You are validating against the plan but never opened the original spec's acceptance criteria
- You are softening findings to avoid contradicting the implementation session
- You built the criterion accounting from the plan's phases rather than the spec's list — the pairing gate exists to catch the criteria the plan forgot

## Verification

A validation run is itself complete only when:

- [ ] Every automated check (tests, lint, types) was executed fresh in this session with results captured
- [ ] Each plan phase was verified against actual code, with file:line evidence
- [ ] Each spec acceptance criterion has an explicit pass/fail verdict
- [ ] The standing [Definition of Done](../../references/definition-of-done.md) checklist was applied
- [ ] Findings are reported honestly, ordered by severity, including "no issues found" only when genuinely true
- [ ] The pairing gate accounting holds exactly one record per spec criterion, built from the spec itself, with nothing omitted or merged
- [ ] Any unbound automated criterion produced the pairing gate's blocking result, and the run was never reported as success while one remained
