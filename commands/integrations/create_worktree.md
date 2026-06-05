---
title: create_worktree
description: Create worktree and launch implementation session for a plan
model: analysis
---

# Create Worktree

Create a git worktree for a ticket and launch an implementation session. This command handles all worktree creation steps inline without external dependencies.

## Setup

Read configuration from `specs.config.yaml`:
- `ticket_id_pattern`: Regex pattern for identifying ticket IDs (e.g., "ENG-\\d+")
- `worktree_base_path`: Base directory for creating worktrees (e.g., "../worktrees")
- `ticket_system`: The ticket management system (for reference)
- `ticket_integration`: How to reach the ticket system — `mcp`, `cli`, or `none` (see [ticket-integration](../../conventions/ticket-integration.md))
- `ticket_mcp_prefix`: MCP tool prefix when `ticket_integration: mcp`

## Process

### Part I: Extract and Validate Ticket ID

1. Accept a ticket ID as input (or extract from current ticket context)
2. Validate the ticket ID matches `ticket_id_pattern` regex from config
3. Example patterns:
   - Linear: `ENG-\d+` matches "ENG-123"
   - Jira: `[A-Z]+-\d+` matches "PROJ-456"
   - GitHub: `#\d+` or `\d+` matches "#789"
4. Log the validated ticket ID for use in worktree naming

### Part II: Create Feature Branch

1. Determine the primary git branch (usually "main" or "master"):
   - Run: `git rev-parse --abbrev-ref HEAD` to find current branch
   - Or check git config for default branch
2. Create a feature branch with naming convention:
   - Format: `{ticket_id_pattern}-{ticket_id}/{descriptive-name}`
   - Example: `eng-123/add-user-authentication`
   - Or simpler: `feature/{ticket_id}`
3. Run: `git checkout -b {branch_name}`

### Part III: Create Worktree

1. Determine worktree path:
   - Use `worktree_base_path` from config as base directory
   - Subdirectory: `{ticket_id}` or `{ticket_id}-{timestamp}`
   - Full path: `{worktree_base_path}/{ticket_id}`
   - Example: `../worktrees/ENG-123`
2. Create the worktree directory structure:
   ```
   mkdir -p {worktree_base_path}
   ```
3. Create the git worktree:
   ```
   git worktree add {worktree_path} {branch_name}
   ```
4. Confirm worktree was created successfully:
   ```
   git worktree list
   ```

### Part IV: Set Up Worktree Environment

1. Navigate to the worktree directory:
   ```
   cd {worktree_path}
   ```
2. Install dependencies if needed (run appropriate install command):
   - Node: `npm install` or `yarn install`
   - Python: `pip install -r requirements.txt`
   - Ruby: `bundle install`
   - Or equivalent for your project
3. Verify the worktree is ready for development:
   - Check that build system works
   - Run basic tests or lint checks
   - Confirm all dependencies are installed

### Part V: Launch Implementation

1. Document the worktree setup:
   - Ticket ID: {ticket_id}
   - Feature branch: {branch_name}
   - Worktree path: {worktree_path}
   - Ready for implementation
2. Provide context for implementation session:
   - Load the implementation plan from the ticket or thoughts directory
   - Set up session to track progress in this worktree
   - Ready for `/implement_plan` or other development commands
3. Notes for the session:
   - All commits should reference the ticket ID
   - Work is isolated in this worktree
   - Use `/commit` to create atomic commits
   - Use `/describe_pr` when implementation is complete

## Worktree Cleanup

When implementation is complete:

```
# Merge or review the branch
git checkout {primary_branch}
git merge {branch_name}
# OR git push origin {branch_name} for PR review

# Remove the worktree
git worktree remove {worktree_path}

# Verify cleanup
git worktree list
git branch -d {branch_name}  # After merged
```

## Configuration Example

In `specs.config.yaml`:
```yaml
ticket_id_pattern: "ENG-\\d+"
worktree_base_path: "../worktrees"
```

With these settings:
- Ticket: "ENG-123"
- Feature branch: "feature/ENG-123"
- Worktree path: "../worktrees/ENG-123"

## Key Points

- Worktree creation is fully self-contained with inline git commands
- No external shell scripts (hack/create_worktree.sh) required
- Ticket ID extraction uses the configured `ticket_id_pattern` regex
- Worktree paths are controlled via `worktree_base_path` config
- Feature branch naming follows project conventions
- Dependencies are installed before implementation begins
- Worktree can be cleaned up after merge using standard git commands

## Important Notes

- Each ticket gets its own isolated worktree for focused work
- Worktrees allow parallel work on multiple features without switching branches
- All commits in the worktree are on the feature branch (separate from main)
- After pushing and merging the PR, remove the worktree to keep the filesystem clean
- Use `git worktree list` to see all active worktrees
- The ticket ID is embedded in the branch and worktree names for easy tracking
