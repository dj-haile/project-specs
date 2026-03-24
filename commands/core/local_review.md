---
name: local_review
description: Set up worktree for reviewing colleague's branch
context: core
---

# Local Review Setup

Set up a git worktree for reviewing a colleague's branch alongside your current work, with proper isolation and cleanup.

## Setup (read before proceeding)
1. Check if `specs.config.yaml` exists at project root
2. Read relevant config values:
   - `worktree_base_path`: directory for worktrees (if configured)
3. Determine worktree location:
   - If configured: use `{worktree_base_path}/`
   - If not: ask user where to create worktree or use `./.worktrees/`
4. Verify sufficient disk space for full repository clone

## Purpose

Worktrees let you:
- **Review code in isolation**: Full working directory for colleague's branch
- **Run tests independently**: Verify changes don't break existing tests
- **Keep current work safe**: Your main working directory stays unchanged
- **Compare side-by-side**: Easy switching between branches for comparison
- **Clean up easily**: Remove worktree when review is done

## When to Use

- Reviewing a colleague's pull request
- Testing someone else's feature branch
- Comparing different implementations
- Avoiding interruption to your current work
- Checking out long-running feature branches

## Process

### Phase 1: Plan Worktree

1. **Identify target branch**
   - Which colleague's branch do you want to review?
   - What's the full branch name? (e.g., `feature/user-auth`)
   - Does it exist in remote?

2. **Choose worktree location**
   - If `worktree_base_path` configured: use that directory
   - If not configured: ask user for location
   - Default pattern: `./.worktrees/{branch-name}/`
   - Or: `~/wt/{project-name}/{branch-name}/`

3. **Verify workspace**
   - Current worktree is clean: `git status`
   - Target branch exists: `git branch -a | grep branch-name`
   - You have access to remote: `git fetch`

### Phase 2: Create Worktree

1. **Fetch latest**
   ```bash
   git fetch origin
   ```

2. **Create worktree**
   ```bash
   # Option A: Track remote branch
   git worktree add --track -b {branch-name} \
     {worktree_path} origin/{remote-branch-name}

   # Option B: Check out existing local branch
   git worktree add {worktree_path} {branch-name}
   ```

   Example:
   ```bash
   git worktree add --track -b feature-auth \
     ./.worktrees/feature-auth origin/feature/user-auth
   ```

3. **Verify creation**
   ```bash
   cd ./.worktrees/feature-auth
   git branch                    # Should show correct branch
   git log -1 --oneline         # Show current commit
   ```

### Phase 3: Set Up Environment

1. **Install dependencies**
   ```bash
   npm install          # or equivalent for your project
   ```

2. **Build if necessary**
   ```bash
   npm run build        # if applicable
   ```

3. **Verify environment**
   ```bash
   npm run test         # Run test suite
   npm run lint         # Check code style
   ```

### Phase 4: Review Code

1. **Understand the changes**
   ```bash
   # See what changed from main
   git diff main...HEAD --stat

   # Show actual changes
   git diff main...HEAD

   # Show commits in this branch
   git log main..HEAD --oneline
   ```

2. **Review by file**
   ```bash
   # Look at specific file
   git show HEAD:src/file.js

   # Compare with main
   git diff main HEAD -- src/file.js
   ```

3. **Run tests and checks**
   ```bash
   npm test                    # Verify tests pass
   npm run lint                # Check code style
   npm run type-check          # If TypeScript
   ```

4. **Build and run locally**
   ```bash
   npm run dev                 # Start dev server
   npm run build               # Build for production
   ```

5. **Take notes**
   - What's good about this implementation?
   - Are there concerns or issues?
   - Do tests cover the changes adequately?
   - Is the code style consistent?
   - Are there performance implications?

### Phase 5: Compare With Alternatives

If you want to compare multiple implementations:

1. **Create worktree for alternative branch**
   ```bash
   git worktree add ./.worktrees/alternative-approach origin/feature/alt-approach
   ```

2. **Switch between worktrees**
   ```bash
   cd ./.worktrees/feature-auth      # Review original
   # ... inspect code ...

   cd ./.worktrees/alternative-approach  # Review alternative
   # ... inspect code ...
   ```

3. **Compare directly**
   ```bash
   # From project root
   diff -r ./.worktrees/feature-auth/.src ./.worktrees/alternative-approach/src
   ```

### Phase 6: Provide Feedback

1. **Document findings**
   - What works well
   - What could be improved
   - Questions for the author
   - Suggestions for alternatives

2. **Share feedback**
   - Add comments to pull request if applicable
   - Direct message colleague with detailed review
   - Reference specific code locations
   - Link to relevant documentation or patterns

### Phase 7: Clean Up

When review is complete:

1. **Return to main worktree**
   ```bash
   cd /path/to/main/repository
   ```

2. **Remove worktree**
   ```bash
   git worktree remove ./.worktrees/feature-auth

   # If there are uncommitted changes
   git worktree remove --force ./.worktrees/feature-auth
   ```

3. **Verify removal**
   ```bash
   git worktree list          # Should not show removed worktree
   ls -la ./.worktrees/       # Directory should be gone
   ```

## Useful Commands

### Explore Changes
```bash
# Summary of changes
git diff main --stat

# Full diff
git diff main

# Show commits
git log main..HEAD

# Show specific commit
git show {commit-hash}
```

### Review Code
```bash
# View file at specific commit
git show {commit-hash}:path/to/file.js

# Compare file across branches
git diff main HEAD -- path/to/file.js

# Show blame (who changed what)
git blame path/to/file.js
```

### Verify Quality
```bash
# Run tests
npm test

# Check code style
npm run lint

# Type checking
npm run type-check

# Build verification
npm run build
```

### Work with Multiple Worktrees
```bash
# List all worktrees
git worktree list

# Lock worktree (prevent accidental removal)
git worktree lock ./.worktrees/feature-auth

# Unlock worktree
git worktree unlock ./.worktrees/feature-auth
```

## Review Checklist

### Code Quality
- [ ] Code follows project style guide
- [ ] No obvious bugs or logic errors
- [ ] Error handling is adequate
- [ ] Performance implications understood
- [ ] No security vulnerabilities visible

### Testing
- [ ] Existing tests still pass
- [ ] New tests cover the changes
- [ ] Edge cases tested
- [ ] Test quality is good

### Documentation
- [ ] Code has appropriate comments
- [ ] README or docs updated if needed
- [ ] API documentation accurate
- [ ] Configuration options documented

### Integration
- [ ] Changes don't break other features
- [ ] Dependencies are compatible
- [ ] No conflicts with other work
- [ ] Database migrations handled (if applicable)

### Architecture
- [ ] Follows project patterns and conventions
- [ ] Doesn't introduce unnecessary complexity
- [ ] Reasonable design decisions
- [ ] Fits with overall architecture

## Common Review Patterns

### Quick review (20 minutes)
1. Create worktree
2. Run: `git diff main --stat`
3. Read: `git log main..HEAD`
4. Run tests
5. Scan: `git diff main` for critical issues
6. Share quick feedback

### Thorough review (1-2 hours)
1. Create worktree
2. Review all commits individually
3. Read all modified files
4. Run test suite and build
5. Compare with alternative approaches
6. Document detailed feedback
7. Share comprehensive review

### Deep architectural review (2+ hours)
1. Create worktrees for multiple approaches
2. Study design decisions
3. Compare implementations side-by-side
4. Review for scalability/maintainability
5. Check test coverage comprehensively
6. Provide architectural guidance
7. Share strategic feedback

## Error Handling

- If branch doesn't exist: suggest checking branch name, verify remote
- If worktree creation fails: check disk space, verify path is writable
- If tests fail: note test failures in review, investigate blockers
- If dependencies conflict: note dependency issues, suggest resolution
- If build fails: diagnose and document build issues in feedback

## Tips for Effective Review

- **Run tests first**: Verify the branch is in good state
- **Read commits in order**: Understand the thought process
- **Check test coverage**: Are the changes adequately tested?
- **Consider alternatives**: Is this the best approach?
- **Provide constructive feedback**: Explain why, suggest improvements
- **Be specific**: Reference line numbers and code sections
- **Appreciate good work**: Highlight things done well
- **Document assumptions**: State what you're assuming about requirements

## Cleanup Reminders

Don't forget to clean up worktrees when done:
- Unused worktrees waste disk space
- They may cause conflicts if branch is updated
- They can interfere with git operations
- Always: `git worktree remove {path}` when finished

## Worktree Limitations

Be aware of these constraints:
- **One checkout per branch**: Branch can only be checked out once (main working directory OR one worktree)
- **Shared .git**: All worktrees share same repository data
- **Cleanup needed**: Always remove worktree when done
- **Directory conflicts**: Can't create worktree where directory already exists
