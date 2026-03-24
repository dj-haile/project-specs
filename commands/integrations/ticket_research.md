---
title: ticket_research
description: Research highest priority ticket needing investigation
model: opus
---

# Ticket Research

Research the highest priority ticket needing investigation from your configured ticket system.

## Setup

Read configuration from `specs.config.yaml`:
- `ticket_system`: The ticket management system (linear, jira, asana, github-issues)
- `ticket_mcp_prefix`: MCP tool prefix for this system (e.g., mcp__linear, mcp__jira)
- `ticket_id_pattern`: Regex pattern for identifying ticket IDs
- `ticket_statuses`: Map of generic statuses to system-specific labels (e.g., in_research)
- `thoughts_directory`: Whether to support thoughts document sync
- `thoughts_path`: Default path for thoughts storage

## Process

### Part I: Fetch and Select Ticket

1. Use the configured MCP tools via `{ticket_mcp_prefix}` to fetch tickets
2. Query for tickets in the "in_research" or "ready_for_research" status from `ticket_statuses`
3. Sort by priority and select the highest priority ticket
4. Extract ticket ID using `ticket_id_pattern` regex
5. Log the selected ticket details (ID, title, description, acceptance criteria)

### Part II: Conduct Research

1. Use `/research_codebase` command to investigate:
   - Relevant code files and modules mentioned in the ticket
   - Existing implementations of similar features
   - Current project architecture and patterns
   - API boundaries and contracts that may be affected
2. Document findings including:
   - Affected code areas
   - Existing patterns to follow
   - Potential risks or complexity factors
   - Alternative approaches considered

### Part III: Update Ticket with Research Results

1. Use configured MCP tools to add detailed comments to the ticket with:
   - Summary of research findings
   - Key code locations and files
   - Architecture considerations
   - Recommended approach with justification
2. Update ticket status to "researched" or next step from `ticket_statuses`
3. Confirm the ticket has been updated successfully

## Notes

- Use only config-driven ticket_statuses for workflow progression
- Store detailed research notes in the configured `thoughts_path` if `thoughts_directory` is enabled
- The ticket system MCP tools are loaded automatically via `{ticket_mcp_prefix}`
- Extract any existing research from ticket description to avoid duplication
