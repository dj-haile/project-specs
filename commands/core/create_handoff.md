---
name: create_handoff
description: Create handoff document for transferring work to another session
context: core
---

# Create Handoff Document

Create a comprehensive handoff document that enables another session or team member to continue your work with full context and continuity.

## Setup (read before proceeding)
1. Check if `specs.config.yaml` exists at project root
2. Read relevant config values:
   - `thoughts_directory`: true/false (whether to save to thoughts/)
   - `thoughts_path`: path to thoughts directory (if enabled)
3. Determine save location:
   - If thoughts_directory = true: save to `{thoughts_path}/handoffs/`
   - If false: ask user where to save or use project root

## Purpose

Handoff documents preserve:
- **Current context**: What are you working on and why?
- **Progress state**: What's done, what's in progress, what's blocked?
- **Key decisions**: Why were certain approaches chosen?
- **Open questions**: What still needs investigation?
- **Next steps**: What should the next session focus on?
- **Relevant files**: Which files matter most?
- **Test status**: What's tested, what needs testing?

## Handoff Template

```yaml
---
created: "2026-03-24T14:30:00Z"
creator: "Session Name"
project: "Project Name"
branch: "feature/branch-name"
status: "in-progress"
priority: "high"
---

# Handoff: [Project/Feature Name]

## Summary
<!-- 2-3 sentences of what you've been working on -->

## Current Status

### In Progress
- [ ] Task 1 - description and current progress
- [ ] Task 2 - description and current progress

### Completed
- [x] Task 1 - completion notes
- [x] Task 2 - completion notes

### Blocked
- Task 1 - reason blocked, what's needed to unblock
- Task 2 - reason blocked, what's needed to unblock

### Not Started
- [ ] Task 1 - why it's waiting
- [ ] Task 2 - why it's waiting

## Key Files

### Modified
- `src/feature.js` - What changed and why
- `tests/feature.test.js` - New or updated tests

### Referenced (important context)
- `docs/architecture.md` - Relevant architecture decisions
- `config/settings.yaml` - Configuration used

### Generated/Temporary
- `.tmp/analysis-output.json` - Analysis results (can be regenerated)

## Technical Context

### Architecture Decisions
<!-- Why was this approach chosen? -->
- Decision 1: Reasoning
- Decision 2: Reasoning

### Important Dependencies
<!-- What versions, services, or external systems matter? -->
- Dependency 1: Version X, used for...
- Dependency 2: Version Y, used for...

### Environment Setup
<!-- What config or environment is needed? -->
```bash
# Example setup commands
export API_KEY=value
npm install
npm run build
```

## Implementation Details

### Approach
<!-- High-level description of how you're solving the problem -->

### Why This Approach
<!-- Benefits and trade-offs -->
- Benefit 1
- Benefit 2
- Trade-off 1

### Alternative Approaches Considered
- Approach A: Why rejected
- Approach B: Why rejected

## Testing

### Completed Tests
- [x] Unit tests for feature logic
- [x] Integration tests for API calls

### Pending Tests
- [ ] E2E tests (need test environment setup)
- [ ] Performance tests (need load testing framework)

### Test Commands
```bash
npm test                    # Run all tests
npm run test:unit          # Unit tests only
npm run test:integration   # Integration tests
```

## Known Issues & Workarounds

### Issue 1: [Description]
- Status: Blocked
- Workaround: [If exists]
- Resolution: [Next steps]

### Issue 2: [Description]
- Status: Under investigation
- Notes: [What you've learned]
- Next: [What to check]

## Open Questions

1. **Question 1**: What's unclear?
   - Attempted approaches?
   - Why unclear?

2. **Question 2**: What needs clarification?
   - Who might know the answer?
   - Where to look for answer?

## Next Steps

### Immediate (Next Session)
1. Action 1 - Why this is first
2. Action 2 - Dependencies
3. Action 3 - Cleanup or validation

### Short Term (This Week)
1. Feature completion
2. Integration testing
3. Code review

### Longer Term (This Month)
1. Performance optimization
2. Documentation updates
3. Release planning

## How to Resume

### Before Proceeding
1. Read this entire document
2. Check current branch and status: `git status`
3. Verify environment setup: `npm install && npm run build`
4. Review open questions above

### Quick Start
```bash
# Get current state
git status
git log -3 --oneline

# Run tests to verify environment
npm test

# Start with: [First next step from above]
```

### If Blocked
1. Check "Known Issues & Workarounds" section above
2. Review "Open Questions" section
3. Check PR/ticket for additional context

## Session Notes

### What Went Well
- Positive 1
- Positive 2

### What Was Challenging
- Challenge 1: How you approached it
- Challenge 2: How you approached it

### Tools & Resources Used
- Tool 1: Purpose
- Resource 1: Relevant section or link

### Time Spent
- Investigation: X hours
- Implementation: Y hours
- Testing: Z hours

## Contact/Context

- **Project repo**: [Location]
- **Ticket/Issue**: [Link if applicable]
- **Slack thread**: [Link if applicable]
- **Related handoffs**: [Links to previous handoffs if part of longer chain]

## Checklist Before Submitting Handoff

- [ ] Summary is clear and actionable
- [ ] Status of all tasks is explicit
- [ ] Key decisions are documented with reasoning
- [ ] File changes are explained
- [ ] Test status is clear
- [ ] Next steps are specific and ordered
- [ ] Open questions are documented
- [ ] Environment setup is reproducible
- [ ] No secrets or credentials in document
- [ ] Links to resources are valid
```

## Storage

### If thoughts_directory = true
```
{thoughts_path}/
└── handoffs/
    ├── feature-auth-oauth.md          (timestamp or feature-based naming)
    ├── fix-memory-leak-20260324.md
    └── setup-database-migration.md
```

### If thoughts_directory = false
Ask user where to save:
- Project root as `handoff-feature-name.md`
- User-specified directory
- Document location in session notes

## Creation Process

1. **Gather current state**
   - List modified files: `git status`
   - Show recent changes: `git log -5 --oneline`
   - Check branch: `git branch`
   - Run tests to verify status

2. **Document progress**
   - What's complete?
   - What's in progress?
   - What's blocked and why?

3. **Record decisions**
   - Why did you choose this approach?
   - What alternatives did you consider?
   - What assumptions are you making?

4. **List next steps**
   - What should the next session focus on?
   - What's highest priority?
   - What's blocked waiting for external input?

5. **Verify document**
   - All sections filled?
   - Is it clear to someone new to the project?
   - Are all commands reproducible?
   - No secrets included?

6. **Save to configured location**
   - Create or confirm destination directory
   - Use clear naming convention
   - Note file location in session output

## Tips for Good Handoffs

- **Be specific**: "Fixed bug with null check" is less useful than "Added guard clause for null response in getUserData at line 42, preventing TypeError"
- **Show your work**: Explain why you chose an approach, not just what you did
- **Document unknowns**: Open questions are valuable for the next person
- **Test before handing off**: Verify your work is stable
- **Keep it current**: Update handoff as work progresses, not just at the end
- **Include context**: Links to issues, documentation, or related work

## Error Handling

- If save location doesn't exist: create directory structure
- If file already exists: ask user to confirm overwrite or use new name
- If config values missing: ask user for required information
- If document seems incomplete: warn user before saving
