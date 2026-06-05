---
title: ticket_manage
description: Manage tickets - create, update, comment, and follow workflow patterns
model: planning
---

# Ticket Management

Comprehensive ticket management for your configured ticket system. Create, update, comment on, and manage the workflow for tickets across any supported system: Linear, Jira, Asana, or GitHub Issues.

## Setup

Read configuration from `specs.config.yaml`:
- `ticket_system`: The ticket management system (linear, jira, asana, github-issues)
- `ticket_integration`: How to reach the ticket system — `mcp`, `cli`, or `none` (see [ticket-integration](../../conventions/ticket-integration.md))
- `ticket_mcp_prefix`: MCP tool prefix when `ticket_integration: mcp` (e.g., mcp__linear, mcp__jira)
- `ticket_cli`: CLI command when `ticket_integration: cli` (e.g., linear-cli)
- `ticket_id_pattern`: Regex pattern for identifying ticket IDs
- `ticket_statuses`: Map of generic statuses to system-specific labels:
  - `triage`: Initial intake status
  - `ready_for_spec`: Ready for specification/planning
  - `in_research`: Under investigation
  - `researched`: Research complete
  - `planning`: Plan being created
  - `planned`: Plan complete
  - `ready_for_dev`: Ready for implementation
  - `in_development`: Under active development
  - `in_review`: Waiting for review
  - `reviewed`: Review complete
  - `done`: Completed
- `thoughts_directory`: Whether to support thoughts document sync
- `thoughts_path`: Default path for thoughts storage

## Workflow Overview

Tickets follow this standard progression through the system:

```
Triage → Ready for Spec → In Research → Planning → Ready for Dev → In Development → In Review → Done
```

Each transition is managed through ticket status updates via the configured MCP tools.

## Creating Tickets

### From Thoughts Documents

When `thoughts_directory` is enabled:

1. Create or update a markdown document in `thoughts_path` with problem statement
2. Document the problem to solve, context, and success criteria
3. Use the configured MCP tools via `{ticket_mcp_prefix}__create_issue` to create a ticket:
   - Extract title and description from the thoughts document
   - Set initial status to "triage" from `ticket_statuses`
   - Add appropriate labels for the feature/bug type
   - Link to the thoughts document URL if applicable
4. The ticket is now ready for triage workflow

### Direct Ticket Creation

1. Use `{ticket_mcp_prefix}__create_issue` to create a new ticket directly with:
   - Clear, specific title describing the work
   - Detailed description following the "problem to solve" format:
     * Problem statement
     * Context and impact
     * Success criteria
     * Acceptance criteria
   - Set initial status to "triage"
   - Assign team or labels as needed

## Ticket Management Operations

### Query and View

```
Use {ticket_mcp_prefix}__get_issues to:
- Fetch all open tickets
- Filter by status using ticket_statuses mappings
- Sort by priority to identify next work item
- Search by label, assignee, or date
```

### Update Ticket Status

1. Identify the current status and target status
2. Map both through `ticket_statuses` dictionary from config
3. Use `{ticket_mcp_prefix}__update_issue` to change status
4. Add a comment explaining the status change:
   - Reason for transition
   - What was accomplished or discovered
   - Next steps or blockers
   - Link to related pull requests or documents

### Add Comments to Tickets

1. Use `{ticket_mcp_prefix}__add_comment` to add detailed comments
2. Comment quality guidelines:
   - Be specific and actionable
   - Include code examples if relevant
   - Reference other tickets or documents with links
   - Explain the "why" behind decisions
   - Highlight dependencies or risks
3. Use comments to:
   - Document research findings
   - Explain implementation decisions
   - Provide review feedback
   - Note blockers or delays
   - Link to pull requests

### Workflow Pattern: Research Phase

1. Ticket starts in "ready_for_spec" status
2. Assignee runs `/ticket_research` to investigate
3. Research findings are documented in ticket comments or `thoughts_path`
4. Update status to "researched" via `{ticket_mcp_prefix}__update_issue`
5. Add summary comment with:
   - Key findings
   - Affected code areas
   - Identified risks
   - Recommended approach

### Workflow Pattern: Planning Phase

1. Ticket in "researched" status, ready for planning
2. Assignee runs `/ticket_plan` using research and ticket details
3. Implementation plan is created and documented
4. Update status to "planned" via `{ticket_mcp_prefix}__update_issue`
5. Add comment with:
   - Plan summary and phases
   - Estimated effort
   - Dependencies
   - Testing strategy

### Workflow Pattern: Development Phase

1. Ticket in "planned" status, ready for implementation
2. Assignee runs `/ticket_impl` to create worktree and begin implementation
3. During development:
   - Make commits with ticket ID in message (e.g., "ENG-123: Add feature X")
   - Reference ticket ID in commit messages using `ticket_id_pattern`
4. Update status to "in_development" via `{ticket_mcp_prefix}__update_issue`
5. Upon completion:
   - Create pull request using `/describe_pr` command
   - Update status to "in_review"
   - Add comment linking to pull request

### Workflow Pattern: Review Phase

1. Ticket in "in_review" status with associated pull request
2. Reviewers provide feedback in pull request comments
3. Author addresses feedback with additional commits
4. Once approved:
   - Merge the pull request
   - Update ticket status to "done" via `{ticket_mcp_prefix}__update_issue`
   - Add comment confirming completion and linking to merged commit

## Ticket ID Handling

All ticket IDs in this system follow the pattern defined in `ticket_id_pattern` from config:
- Example: `ENG-123` for Linear, `PROJ-456` for Jira, `GH#789` for GitHub Issues
- Extract IDs using the regex pattern from config
- Reference IDs in commit messages, PR descriptions, and comments
- Use IDs as worktree branch names for organization

## Configuration Requirements

**Required in specs.config.yaml:**
1. `ticket_system`: Which system is in use
2. `ticket_mcp_prefix`: The MCP prefix for your system's tools
3. `ticket_id_pattern`: Regex to extract ticket IDs
4. `ticket_statuses`: Complete mapping of all generic status names to system-specific ones

**Optional:**
1. `thoughts_directory`: Enable/disable thoughts document integration
2. `thoughts_path`: Where to store thoughts documents
3. System-specific IDs if required:
   - Linear: Team ID, workspace ID
   - Jira: Project key, board ID
   - Asana: Project ID, workspace ID
   - GitHub Issues: Repository owner/name, project board ID

**Discovery Note:** System-specific IDs (team IDs, project keys, user IDs) can be discovered via MCP API calls or configured explicitly. Refer to your system's MCP tool documentation for discovery methods.

## Important Notes

- All ticket operations use the configured `ticket_mcp_prefix` for system independence
- All status transitions use the `ticket_statuses` mapping from config
- No hardcoded Linear/Jira/Asana IDs should be used; configure them in specs.config.yaml or discover via MCP
- The "problem to solve" requirement ensures tickets are clear and actionable
- Comments should be detailed and specific to support team understanding
- Maintain workflow discipline to keep tickets moving through the system
- Use ticket_statuses consistently across all commands and scripts
