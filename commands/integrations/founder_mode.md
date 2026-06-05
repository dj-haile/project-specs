---
title: founder_mode
description: Create ticket and PR for experimental features after implementation
model: planning
---

# Founder Mode

After implementing an experimental feature, automatically create a ticket and pull request documenting the work for team awareness and potential integration.

## Setup

Read configuration from `specs.config.yaml`:
- `ticket_system`: The ticket management system (linear, jira, asana, github-issues)
- `ticket_integration`: How to reach the ticket system — `mcp`, `cli`, or `none` (see [ticket-integration](../../conventions/ticket-integration.md))
- `ticket_mcp_prefix`: MCP tool prefix when `ticket_integration: mcp` (e.g., mcp__linear, mcp__jira)
- `ticket_cli`: CLI command when `ticket_integration: cli` (e.g., linear-cli)
- `ticket_id_pattern`: Regex pattern for identifying ticket IDs
- `ticket_statuses`: Map of generic statuses to system-specific labels
- `thoughts_directory`: Whether to support thoughts document sync
- `thoughts_path`: Default path for thoughts storage

## Process

### Part I: Create Experimental Ticket

1. Use `{ticket_mcp_prefix}__create_issue` to create a new ticket with:
   - **Title**: Describe the experimental feature in clear terms
     - Example: "Experimental: Real-time collaboration sync for documents"
   - **Description**: Comprehensive overview including:
     - What was built and why (the experiment hypothesis)
     - Feature summary and key capabilities
     - Motivation and business impact
     - Current implementation status
     - Known limitations or caveats
     - Recommendations for integration
   - **Status**: Set to "in_review" from `ticket_statuses` (indicates implementation complete)
   - **Labels**: Add "experimental", "founder-mode", or equivalent to flag for team
2. Confirm ticket has been created and note the ticket ID for later reference

### Part II: Create Pull Request

1. Prepare commits if not already done:
   - All experimental feature code should be committed to a feature branch
   - Commits should follow project conventions
   - Include the ticket ID in commit messages using `ticket_id_pattern` format once the ticket exists
2. Use `/describe_pr` command to generate a comprehensive pull request:
   - Title should match the experimental ticket
   - Description should include:
     * Link to the experimental ticket created in Part I
     * Summary of what was implemented
     * Key architectural decisions
     * Testing that was performed
     * Screenshots, demos, or examples if applicable
     * Known issues or future improvements
   - Include implementation context and code organization
3. Create the pull request on the repository
4. Confirm the PR is created and note the PR number

### Part III: Link Ticket to PR

1. Use `{ticket_mcp_prefix}__add_comment` to add a comment on the ticket:
   - Provide the pull request link/number
   - Summarize the PR for quick reference
   - Indicate next steps:
     * Code review status
     * Timeline for potential integration
     * Dependencies or blockers
2. Optionally use `{ticket_mcp_prefix}__update_issue` to set status to "done" or keep in "in_review" if awaiting feedback

## Workflow Details

**Typical Founder Mode Flow:**
1. Founder implements experimental feature in a feature branch
2. Tests and validates the feature works as intended
3. Runs `/founder_mode` command to create ticket + PR
4. Team can review the ticket and pull request
5. Either integrate into main if valuable, or archive/close if not

**Ticket Status:**
- Created with "in_review" status to indicate implementation is complete
- Can be transitioned to "done" after team acknowledgment
- Or updated to "planning" if team decides to integrate

**PR Linking:**
- Tickets and PRs remain linked through comments and ticket ID references
- Makes it easy for team to find associated work
- Centralizes discussion in either ticket or PR depending on context

## Key Points

- This command bridges the gap between experimental work and team visibility
- No external session launchers required
- Uses Claude Code's native `/describe_pr` command
- Parameterized for any ticket system via `{ticket_mcp_prefix}`
- Maintains ticket ID consistency using `ticket_id_pattern`
- Suitable for rapid experimentation and team synchronization

## Notes

- "Experimental" features can later be integrated into the main product workflow
- Tickets created here are for awareness and evaluation, not necessarily committed work
- Use descriptive titles and descriptions so team understands the experiment's purpose
- Include sufficient detail for team to evaluate usefulness and integration complexity
- The ticket and PR remain linked for future reference and decision-making
