---
title: ticket_plan
description: Create implementation plan for highest priority ticket ready for spec
model: planning
---

# Ticket Plan

Create an implementation plan for the highest priority ticket ready for spec from your configured ticket system.

## Setup

Read configuration from `specs.config.yaml`:
- `ticket_system`: The ticket management system (linear, jira, asana, github-issues)
- `ticket_integration`: How to reach the ticket system — `mcp`, `cli`, or `none` (see [ticket-integration](../../conventions/ticket-integration.md))
- `ticket_mcp_prefix`: MCP tool prefix when `ticket_integration: mcp` (e.g., mcp__linear, mcp__jira)
- `ticket_cli`: CLI command when `ticket_integration: cli` (e.g., linear-cli)
- `ticket_id_pattern`: Regex pattern for identifying ticket IDs
- `ticket_statuses`: Map of generic statuses to system-specific labels (e.g., ready_for_spec)
- `thoughts_directory`: Whether to support thoughts document sync
- `thoughts_path`: Default path for thoughts storage

## Process

### Part I: Fetch and Select Ticket

1. Use the configured MCP tools via `{ticket_mcp_prefix}` to fetch tickets
2. Query for tickets matching the "ready_for_spec" status from `ticket_statuses`
3. Sort by priority field and select the highest priority ticket
4. Extract ticket ID using `ticket_id_pattern` regex
5. Log the selected ticket details (ID, title, description)

### Part II: Create Implementation Plan

1. Examine the ticket's description and requirements
2. Use `/create_plan` command to generate a comprehensive implementation plan
   - Break down into phases: research, implementation, testing, review
   - Include file paths, API boundaries, testing strategy
   - Consider the project's existing architecture from earlier context
3. Document the plan in the ticket's comments or as a note within the plan structure
4. Ensure plan follows the structure outlined in the /create_plan documentation

### Part III: Update Ticket Workflow State

1. Use configured MCP tools to transition the ticket to the "planning" or equivalent status
2. Add a comment describing the plan creation:
   - Summary of phases and scope
   - Estimated complexity and effort
   - Any dependencies or blockers identified
3. Confirm the ticket has been updated successfully

## Notes

- Use only config-driven ticket_statuses for workflow progression
- The ticket system MCP tools are loaded automatically via `{ticket_mcp_prefix}`
- Store any generated plans in the configured `thoughts_path` if `thoughts_directory` is enabled
- All hardcoded Linear/Jira/Asana IDs should be discovered via MCP API calls or configured explicitly in specs.config.yaml
