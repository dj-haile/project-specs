---
name: describe_pr
description: Generate comprehensive PR descriptions following repository templates
context: core
---

# Generate PR Description

Create comprehensive pull request descriptions that follow your repository's template and style conventions.

## Setup (read before proceeding)
1. Check if `specs.config.yaml` exists at project root
2. Read relevant config values:
   - `pr_template_path`: path to PR template file (if specified)
   - `thoughts_directory`: true/false (whether to save to thoughts/)
   - `thoughts_path`: path to thoughts directory (if enabled)
3. Apply appropriate behavior based on config

## Behavior

### If thoughts_directory = true
- Load PR template from configured `pr_template_path`
- Save PR description to `{thoughts_path}/prs/` directory
- Create timestamped or branch-named description file
- Enable async review and iteration

### If thoughts_directory = false
- Use built-in default PR template
- Save to project root or user-specified location
- Display description in session output

## Process

1. **Analyze changes**
   - Run `git diff` against base branch
   - Identify changed files and their purposes
   - Extract commit messages and intent
   - Categorize changes (features, fixes, docs, etc.)

2. **Load or use template**
   - If pr_template_path exists: parse template from file
   - Extract required sections from template
   - Map analysis to template structure
   - If no template: use built-in default below

3. **Generate description**
   - Write summary (1-3 sentences)
   - List changes by category
   - Document testing approach
   - Note any breaking changes
   - Add context/motivation

4. **Verify**
   - Check all template sections are filled
   - Validate completeness
   - Ensure no secrets or sensitive data
   - Format with proper markdown

5. **Save or display**
   - If thoughts_directory enabled: save to structured location
   - If disabled: display in output or ask user for location
   - Provide file path or reference

## Built-in Default Template

Use this if no template found in configuration:

```markdown
## Summary
<!-- 1-3 sentence summary of changes -->

## Changes
### Features
- <!-- List new features -->

### Fixes
- <!-- List bug fixes -->

### Documentation
- <!-- List doc updates -->

### Refactoring
- <!-- List refactoring changes -->

## Testing
- <!-- Describe how changes were tested -->
- <!-- List test cases covered -->
- <!-- Note any edge cases -->

## Breaking Changes
<!-- List breaking changes if any -->
<!-- Document migration path if applicable -->

## Context
<!-- Why were these changes made? -->
<!-- Link to issues or requirements -->

## Verification Checklist
- [ ] Code follows project style guide
- [ ] All tests pass
- [ ] No new console errors/warnings
- [ ] Documentation updated
- [ ] No sensitive data included
```

## Storage Locations

### When thoughts_directory = true
Save to: `{thoughts_path}/prs/`
- Create directory if needed
- Use branch-based naming: `{branch-name}-description.md`
- Or timestamp-based: `pr-description-{timestamp}.md`

### When thoughts_directory = false
- Ask user where to save
- Or save to project root: `current-pr-description.md`
- Or keep in-session only

## Verification Steps

1. **Template compliance**
   - All required sections present
   - Proper markdown formatting
   - No empty sections (unless optional)

2. **Content quality**
   - Summary is clear and concise
   - Changes are well-organized
   - Testing strategy is explicit
   - Context explains the "why"

3. **Safety check**
   - No API keys or credentials
   - No personal information
   - No hardcoded secrets
   - No sensitive file paths

4. **Git integration**
   - Changes match `git diff` analysis
   - Commit messages accurately summarized
   - Base branch is correctly identified

## Common Patterns

### Feature PR
```markdown
## Summary
Adds OAuth2 authentication flow allowing users to sign in with GitHub accounts.

## Changes
### Features
- GitHub OAuth2 integration via `@octokit/auth-oauth-user`
- New `OAuthCallback` component for handling redirect
- User profile sync on first login
```

### Bug fix PR
```markdown
## Summary
Fixes memory leak in WebSocket connection cleanup during component unmount.

## Changes
### Fixes
- Properly abort pending requests in useEffect cleanup
- Prevent event listener accumulation
- Handle disconnection gracefully
```

### Documentation PR
```markdown
## Summary
Updates API documentation with new OAuth2 endpoint examples and migration guide.
```

## Error Handling

- If template file not found but configured: fall back to built-in template
- If no changes detected: inform user and suggest base branch verification
- If save fails: display description and suggest manual save
- If git operations fail: show git error and suggest troubleshooting
