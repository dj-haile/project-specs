---
description: Validate implementation against plan, verify success criteria, identify issues
model: opus
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

3. **Spawn parallel research tasks** to discover implementation:
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

### Step 3: Generate Validation Report

Create comprehensive validation summary:

```markdown
## Validation Report: [Plan Name]

### Implementation Status
✓ Phase 1: [Name] - Fully implemented
✓ Phase 2: [Name] - Fully implemented
⚠️ Phase 3: [Name] - Partially implemented (see issues)

### Automated Verification Results
✓ Build passes: [command used]
✓ Tests pass: [command used]
✗ Linting issues: [command used] (3 warnings)

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

## Important Guidelines

1. **Be thorough but practical** - Focus on what matters
2. **Run all automated checks** - Don't skip verification commands
3. **Document everything** - Both successes and issues
4. **Think critically** - Question if the implementation truly solves the problem
5. **Consider maintenance** - Will this be maintainable long-term?

## Validation Checklist

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
