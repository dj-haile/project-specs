---
name: commit
description: Create git commits with clear, atomic messages
context: core
---

# Commit Changes

Create git commits with clear, atomic messages following your project's style configuration.

## Setup (read before proceeding)
1. Check if `specs.config.yaml` exists at project root
2. Read relevant config values:
   - `ci_mode`: true/false (controls interactive behavior)
   - `commit_style`: conventional or freeform
   - `thoughts_directory`: true/false (whether thoughts/ should be excluded)
   - `thoughts_path`: path to thoughts directory (if enabled)
3. Apply appropriate behavior based on config

## Behavior

### If ci_mode = false (interactive)
1. Show the user what files will be staged
2. Ask for confirmation before proceeding
3. Request a commit message following your commit_style
4. Show the commit plan before executing
5. Execute only after user approval

### If ci_mode = true (CI/non-interactive)
1. Stage only relevant files automatically
2. Generate commit message based on commit_style
3. Commit without prompts or delays
4. Log actions for audit trail

## Files to Exclude
- **Always exclude**: `thoughts/` directory (regardless of config)
- **Always exclude**: dummy files, generated build artifacts, node_modules, .env files
- **Only include**: source changes, documentation updates, configuration changes

## Commit Message Format

### If commit_style = conventional
```
type(scope): subject

body (optional)

footer (optional)
```

Types: feat, fix, docs, refactor, test, chore, ci, perf

### If commit_style = freeform
Write clear, descriptive commit messages in plain English.

## Process

1. **Stage files**
   - Use `git add` with explicit file paths (never `git add -A` or `git add .`)
   - Skip thoughts/ directory
   - Skip dummy/generated files
   - Ensure atomic, logical grouping

2. **Generate message**
   - Analyze staged changes
   - Match configured commit_style
   - Keep message clear and actionable

3. **Preview (interactive mode)**
   - Show `git diff --cached` output
   - Show commit message
   - Ask for user confirmation

4. **Commit**
   - Execute `git commit -m "message"`
   - Never use git hooks bypasses (--no-verify, --no-gpg-sign)
   - Never add Claude attribution or co-author info

## Philosophy
- **Atomic commits**: One logical change per commit
- **Clear history**: Future developers understand why changes were made
- **Reviewable**: Each commit should be independently meaningful
- **No noise**: Skip temporary files, build artifacts, and local config

## Common Patterns

### Feature commit (conventional)
```
feat(auth): add password reset flow

- Add ResetPasswordForm component
- Add reset token validation
- Add email notification service
```

### Bug fix (conventional)
```
fix(api): handle null response in getUserData

The API may return null instead of empty object.
Added guard clause to prevent undefined access.
```

### Documentation (freeform)
```
Update API authentication guide with new OAuth2 examples
```

### Multiple changes, single theme (freeform)
```
Refactor database layer for better transaction handling

- Extract transaction logic to TransactionManager
- Update all queries to use new transaction API
- Add rollback error handling
```

## Error Handling

- If no files to stage: inform user and ask for next steps
- If commit fails: show git error message and suggest resolution
- If ci_mode mismatch: verify config and explain applied behavior
