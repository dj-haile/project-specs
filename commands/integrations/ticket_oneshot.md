---
title: ticket_oneshot
description: Research, plan, and implement a ticket in one automated flow
model: planning
---

# Ticket Oneshot

Research, plan, and implement a ticket in one continuous automated flow. This command chains together research, planning, and implementation without requiring manual session switches or external launchers.

## Setup

Read configuration from `specs.config.yaml`:
- `ticket_system`: The ticket management system (linear, jira, asana, github-issues)
- `ticket_integration`: How to reach the ticket system — `mcp`, `cli`, or `none` (see [ticket-integration](../../conventions/ticket-integration.md))
- `ticket_mcp_prefix`: MCP tool prefix when `ticket_integration: mcp` (e.g., mcp__linear, mcp__jira)
- `ticket_cli`: CLI command when `ticket_integration: cli` (e.g., linear-cli)
- `ticket_id_pattern`: Regex pattern for identifying ticket IDs
- `ticket_statuses`: Map of generic statuses to system-specific labels
- `worktree_base_path`: Base directory for creating worktrees (e.g., ../worktrees)
- `thoughts_directory`: Whether to support thoughts document sync
- `thoughts_path`: Default path for thoughts storage

## Process

This command executes the full workflow in sequence:

### Step 1: Research Phase

1. Fetch the highest priority ticket needing research from your ticket system
2. Use `/ticket_research` to conduct comprehensive investigation:
   - Query codebase for related implementations
   - Identify affected code areas and architectural patterns
   - Document findings and recommendations
3. Update ticket status to "researched"
4. Store detailed findings in ticket comments and `thoughts_path` if enabled

### Step 2: Planning Phase

1. Using the researched ticket, execute `/ticket_plan` to create implementation plan:
   - Break down work into phases and tasks
   - Identify dependencies and blockers
   - Define success criteria and testing strategy
2. Update ticket status to "planning" or equivalent
3. Document the plan in ticket comments

### Step 3: Implementation Phase

1. Execute `/ticket_impl` to set up worktree and begin implementation:
   - Create feature branch with ticket ID
   - Load and execute the implementation plan
   - Make atomic commits using `/commit` command
   - Reference ticket ID in all commit messages
2. Upon completion, generate PR description using `/describe_pr`
3. Update ticket status to "in_review"
4. Confirm all changes are committed

## Workflow Details

**Ticket Status Progression:**
- Initial status (determined by `ticket_statuses`) → researched → planning → in_development → in_review → done

**Session Management:**
- This command is self-contained and does not require external session launchers
- All three phases execute in the same session context
- Ticket and worktree context is maintained throughout

**Configuration-Driven:**
- All MCP tool calls use `{ticket_mcp_prefix}` for system independence
- All status updates use `ticket_statuses` mappings from config
- All directory paths use `worktree_base_path` from config

## Notes

- This is a full-cycle automation: research → plan → implement → review
- Uses Claude Code's native slash commands throughout
- All ticket IDs extracted via `ticket_id_pattern` regex
- Worktrees created and cleaned up automatically using configured `worktree_base_path`
- Suitable for high-priority tickets that need rapid turnaround
- Each phase can be interrupted if needed, and the ticket remains in the appropriate state
