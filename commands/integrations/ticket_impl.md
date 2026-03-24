---
title: ticket_impl
description: Implement highest priority ticket with worktree setup
model: sonnet
---

# Ticket Implementation

Implement the highest priority ticket by setting up a worktree and launching an implementation session.

## Setup

Read configuration from `specs.config.yaml`:
- `ticket_system`: The ticket management system (linear, jira, asana, github-issues)
- `ticket_mcp_prefix`: MCP tool prefix for this system (e.g., mcp__linear, mcp__jira)
- `ticket_id_pattern`: Regex pattern for identifying ticket IDs
- `ticket_statuses`: Map of generic statuses to system-specific labels (e.g., in_development)
- `worktree_base_path`: Base directory for creating worktrees (e.g., ../worktrees)
- `thoughts_directory`: Whether to support thoughts document sync
- `thoughts_path`: Default path for thoughts storage

## Process

### Part I: Fetch and Select Ticket

1. Use the configured MCP tools via `{ticket_mcp_prefix}` to fetch tickets
2. Query for tickets in the "ready_for_dev" or "ready_for_implementation" status from `ticket_statuses`
3. Sort by priority and select the highest priority ticket
4. Extract ticket ID using `ticket_id_pattern` regex
5. Log the selected ticket details (ID, title, description, plan reference)

### Part II: Set Up Worktree

1. Use `/create_worktree` command to set up a new git worktree for this ticket:
   - Pass the extracted ticket ID for worktree naming
   - Use `worktree_base_path` from config for directory structure
   - Create a feature branch following project conventions
2. Confirm worktree has been created and is ready for development

### Part III: Launch Implementation Session

1. Use `/implement_plan` command to begin implementing the plan:
   - Load the plan from the ticket or from `thoughts_path` if applicable
   - Set up session context with worktree path and ticket ID
   - Execute implementation steps from the plan
2. As implementation progresses:
   - Use `/commit` command to create meaningful commits for each logical step
   - Reference the ticket ID in commit messages using `ticket_id_pattern` format
3. Upon completion:
   - Use `/describe_pr` command to generate a comprehensive PR description
   - Reference the ticket ID and link to the ticket system
   - Update ticket status to "in_review" or equivalent from `ticket_statuses`
4. Confirm all changes are committed and ready for review

## Notes

- Use Claude Code's native slash commands (/commit, /describe_pr, /implement_plan) for execution
- The worktree_base_path provides configurable directory structure for organizing development branches
- Use only config-driven ticket_statuses for workflow progression
- The ticket system MCP tools are loaded automatically via `{ticket_mcp_prefix}`
- Store implementation notes and progress in `thoughts_path` if enabled
- Worktree naming should include ticket ID for easy tracking
