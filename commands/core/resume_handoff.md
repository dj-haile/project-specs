---
name: resume_handoff
description: Resume work from handoff document with context analysis and validation
context: core
---

# Resume from Handoff

Resume work from a handoff document with full context analysis, validation, and environment verification.

## Setup (read before proceeding)
1. Check if `specs.config.yaml` exists at project root
2. Read relevant config values:
   - `thoughts_directory`: true/false (whether to look in thoughts/)
   - `thoughts_path`: path to thoughts directory (if enabled)
3. Determine handoff location:
   - If thoughts_directory = true: look in `{thoughts_path}/handoffs/`
   - If false: ask user for handoff file path
4. Load and parse the handoff document

## Process

### Phase 1: Load and Validate Handoff

1. **Locate handoff**
   - If configured path: list available handoffs
   - If user-provided path: verify file exists
   - Parse YAML frontmatter

2. **Validate content**
   - Check all required sections present
   - Verify timestamps and creator info
   - Confirm branch and project names match current environment

3. **Parse structure**
   - Extract summary and current status
   - Identify in-progress tasks
   - Note blocked/pending items
   - List key files and modifications

### Phase 2: Analyze and Understand

1. **Read full context**
   - Understand what was being worked on
   - Learn about key decisions and reasoning
   - Review technical context

2. **Identify critical information**
   - What must be done next?
   - What's blocked and how to unblock?
   - What's uncertain (open questions)?
   - What's the current environment state?

3. **Check for changes**
   - Has code changed since handoff was created?
   - Are there new commits on this branch?
   - Has someone else worked on this?

### Phase 3: Verify Environment

1. **Check git state**
   ```bash
   git branch                    # Verify correct branch
   git log -3 --oneline          # Check recent commits
   git status                    # See current modifications
   ```

2. **Verify file state**
   - Check key files mentioned in handoff
   - Confirm they match description
   - Look for unexpected changes

3. **Check environment setup**
   - Run any setup commands from handoff
   - Verify dependencies are available
   - Test build/run commands

4. **Run existing tests**
   ```bash
   # From handoff's test commands
   npm test              # Or equivalent for your project
   ```

### Phase 4: Resume Work

1. **Review immediate next steps**
   - What did previous session identify as next action?
   - Are those steps still valid?
   - Have priorities changed?

2. **Check for blockers**
   - Are listed blockers still blocking?
   - Has any external dependency resolved?
   - Do you have what's needed to proceed?

3. **Understand status gaps**
   - If code has changed since handoff: reconcile with handoff state
   - If tests failing: diagnose what broke
   - If environment issues: troubleshoot setup

4. **Continue from where you left off**
   - Start with next steps from handoff
   - Reference key decisions from handoff
   - Use open questions to guide investigation

## Handoff Sections to Focus On

### Summary
Start here. Get the big picture of what's being worked on.

### Current Status
Understand what's done, in-progress, blocked, and pending. This guides your next actions.

### Known Issues & Workarounds
If you hit a problem, check this first. Someone already investigated it.

### Open Questions
Use these to guide your investigation or research.

### Next Steps
These are specifically for you. Follow them in order unless circumstances have changed.

### Key Files
Know which files matter. Understanding modifications helps you understand the approach.

### Testing
Understand test status. Run tests to verify environment works.

## Common Scenarios

### Everything is broken (tests failing)
1. Run `git status` and `git diff` to see what changed
2. Review "Known Issues & Workarounds" in handoff
3. Check if new commits broke things: `git log --oneline -n 20`
4. Read implementation details to understand expected behavior
5. Investigate most recent failures first

### Branch has new commits (not from handoff creator)
1. Review those commits: `git log --since="24 hours ago"`
2. Check if they conflict with handoff context
3. Merge/rebase if necessary
4. Update your understanding of current state
5. Verify tests still pass

### Handoff is old (created > 1 week ago)
1. Check for significant recent commits
2. Verify blockers are still actual blockers
3. Confirm environment is still valid
4. Review if priorities might have changed
5. Consider if original approach still makes sense

### You're new to this project
1. Read summary carefully
2. Review "Technical Context" section
3. Study "Architecture Decisions" and reasoning
4. Check "Key Files" to understand structure
5. Ask questions if open questions section exists
6. Run all tests and verify environment works

### You're resuming after context switch
1. Read summary to refresh context
2. Check current status section
3. Review "Next Steps" - are they still relevant?
4. Check for blockers that might have changed
5. Verify environment still works
6. Run tests to establish baseline

### Work was blocked, now trying to unblock
1. Find specific item in "Blocked" section
2. Review reason for block and what's needed
3. Check if that external dependency now available
4. Review "Open Questions" for investigation hints
5. Determine if alternative approach now viable

## Verification Checklist

Before proceeding with development:

- [ ] Handoff document is valid and complete
- [ ] Correct branch checked out: `git branch` shows expected branch
- [ ] Recent commits make sense: `git log -5 --oneline`
- [ ] No unexpected modifications: `git status` is clean (except expected changes)
- [ ] Environment set up: dependencies installed, build succeeds
- [ ] Tests pass: `npm test` or equivalent shows all green
- [ ] Key files exist and are as documented
- [ ] No unresolved merge conflicts
- [ ] You understand the next immediate action
- [ ] You understand why that action is next

## Context Bridge Questions

Ask yourself these to ensure you own the context:

1. **What problem are we solving?** (From summary)
2. **What's complete?** (From completed tasks)
3. **What are we working on?** (From in-progress tasks)
4. **Why this approach?** (From architecture decisions)
5. **What's blocked and why?** (From blocked items)
6. **What's the next step?** (From next steps)
7. **What am I unsure about?** (From open questions)

## If Something Doesn't Match

Handoff assumptions may be outdated. Common mismatches:

| Issue | Check | Resolution |
|-------|-------|-----------|
| Tests failing | `git log` for recent changes | Review new commits, adjust approach |
| Files missing | Directory structure changed? | Search for files, confirm project state |
| Dependencies wrong | `package.json` or `requirements.txt` changed? | Re-run install/setup commands |
| Branch diverged | New commits from others? | Merge/rebase with main, resolve conflicts |
| Blocker resolved | Did external dependency arrive? | Resume from where you were blocked |

## Session Integration

### Bring context into session
- Reference specific sections of handoff document
- Quote relevant decisions or reasoning
- Link to specific next steps
- Mention open questions that guide investigation

### Update your understanding
- As you work, compare against handoff assumptions
- If assumptions wrong, note it for next handoff
- If you discover new info, update open questions
- Keep track of how approach evolves

### Prepare next handoff
- As work progresses, update status sections
- Note any new blockers that appear
- Document new decisions and reasoning
- Add new findings to open questions
- Keep file location same or note if moving

## Error Handling

- If handoff file not found: ask user for file path, confirm before loading
- If YAML frontmatter corrupted: try to parse what exists, warn about missing metadata
- If branch doesn't match: warn user, ask if they want to continue on different branch
- If tests fail immediately: suggest running full diagnostic before proceeding
- If environment setup fails: reference handoff's "Environment Setup" section, debug together

## Tips for Effective Resumption

- **Read the whole thing first**: Skim summary, status, next steps before starting
- **Verify environment works**: Run tests to confirm you're in good state
- **Start with next steps**: They're there for you, they're actionable
- **Reference decisions**: When confused, look at "Architecture Decisions" and reasoning
- **Use open questions**: They're breadcrumbs for investigation
- **Keep line of sight**: Remember the big picture from summary
- **Don't ignore blockers**: If something was blocked, understand why before working around it
