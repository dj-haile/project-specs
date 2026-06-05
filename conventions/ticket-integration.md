# Ticket Integration Convention

Integration commands (`ticket_plan`, `ticket_research`, `ticket_impl`,
`ticket_oneshot`, `ticket_manage`, `founder_mode`, `create_worktree`) interact
with a ticket system. *How* they reach that system is provider- and
project-dependent, controlled by two config keys in `specs.config.yaml`:

```yaml
ticket_integration: "mcp"        # mcp | cli | none
ticket_mcp_prefix: "mcp__linear" # used when ticket_integration: mcp
ticket_cli: ""                   # used when ticket_integration: cli (e.g. "linear-cli")
```

Command bodies write ticket operations in the **`mcp` form** —
`{ticket_mcp_prefix}__<operation>` (e.g. `{ticket_mcp_prefix}__create_issue`).
Resolve that operation according to `ticket_integration`:

| `ticket_integration` | How to perform `{ticket_mcp_prefix}__<operation>` |
|----------------------|---------------------------------------------------|
| `mcp` (default)      | Call the MCP tool `{ticket_mcp_prefix}__<operation>` directly (requires the provider to support MCP and the server to be configured). |
| `cli`               | Shell out to `{ticket_cli}` with the equivalent subcommand/flags (e.g. `{ticket_cli} issue create …`). Map the operation name to the CLI's verb. |
| `none`              | No ticket system is wired up. Skip the ticket operation and instead **ask the user** to perform it manually, or record the intended change in the thoughts/ ticket notes if `thoughts_directory: true`. Never fail hard — degrade to manual. |

### Operation vocabulary

The common operations referenced across commands:
`create_issue`, `get_issue` / `get_issues`, `update_issue` (status changes),
`add_comment`. Whatever the mode, preserve the **intent** of the operation; only
the mechanism changes.

### Capability note

`mcp` mode requires `capabilities.mcp: true` in the active provider manifest. All
three current providers (Claude, Codex, Cursor) support MCP, but a project may
still choose `cli` or `none` regardless of provider.

When a command says *"use `{ticket_mcp_prefix}__update_issue` (see
ticket-integration)"* — the link being `../../conventions/ticket-integration.md`
relative to the command's location — this table is what resolves the call for the
project's configured mode.
