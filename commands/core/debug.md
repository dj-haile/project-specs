---
name: debug
description: Debug issues by investigating logs, database state, and git history
context: core
---

# Debug Issues

Investigate system issues by analyzing logs, database state, and git history in parallel. This is pure investigation—no file editing.

## Setup (read before proceeding)
1. Check if `specs.config.yaml` exists at project root
2. Read relevant config values:
   - `log_directory`: path to logs (if configured)
   - `database_path`: path to database/state files (if configured)
3. Ask user for log/database paths if not configured
4. Confirm read-only investigation scope

## Principles

- **Read-only investigation**: Never modify files during debug
- **Parallel analysis**: Check logs, database, and git history simultaneously
- **Pattern recognition**: Look for timing correlations across sources
- **Context preservation**: Keep relevant information in session for analysis

## Process

### Phase 1: Understand the Issue

Ask user to describe:
1. What happened (observed behavior)?
2. When did it happen (timestamp/event)?
3. What should have happened (expected behavior)?
4. Are there error messages or symptoms?

### Phase 2: Gather Information

**Check logs**
- Identify log directory (from config or user input)
- List recent log files
- Filter for relevant timeframe
- Search for error patterns, exceptions, warnings
- Note sequence of events

**Check database/state**
- Identify database/state file location (from config or user input)
- Read current state without modifications
- Compare with expected state
- Note inconsistencies

**Check git history**
- Review recent commits
- Check current branch status
- Look for deployments or releases near error time
- Verify version consistency

### Phase 3: Correlate Findings

1. Timeline alignment
   - Match log timestamps with issue report time
   - Identify what was happening in database at that moment
   - Check recent git activity

2. Pattern detection
   - Recurring errors in logs?
   - Cascading failures?
   - State corruption indicators?
   - Deployment timing coincidences?

3. Root cause hypotheses
   - Most likely causes based on evidence
   - Supporting evidence for each hypothesis
   - Contradicting evidence (rules out causes)

### Phase 4: Communicate Findings

Present investigation results:
1. **Timeline**: What happened and when
2. **Evidence**: Log excerpts, state snapshots, git context
3. **Root cause**: Most likely cause with supporting evidence
4. **Next steps**: What to investigate further or how to resolve

## Investigation Techniques

### Log Analysis
```bash
# Find errors in timeframe
grep -i "error\|exception" logs/*.log | grep "timestamp-range"

# Follow a request/transaction ID
grep "transaction-123" logs/*.log | sort

# Show context around a specific error
grep -B5 -A5 "error-pattern" logs/*.log
```

### Database State
- Read current configuration state
- Identify incomplete transactions
- Check for data inconsistencies
- Compare with previous known-good state

### Git Context
```bash
# Show recent deployments
git log --oneline -n 20 --grep="deploy\|release"

# Check for changes near issue time
git log --since="24 hours ago" --oneline

# Show what changed in specific file
git log -p filename | head -100
```

## Common Issue Patterns

### Service crash/hang
- Check logs for last activity before hang
- Look for resource exhaustion (memory, file handles, database connections)
- Verify recent deployments
- Check for deadlocks or infinite loops

### Data corruption
- Compare current state with backups/snapshots
- Trace when corruption occurred (git history)
- Check transaction logs for incomplete operations
- Look for concurrent access issues

### Performance degradation
- Check logs for increased error rates
- Look for resource usage patterns
- Review recent code changes
- Identify slow queries or operations

### Intermittent failures
- Correlate failures with timing in logs
- Check for race conditions
- Look for resource contention
- Review recent changes affecting timing

## Output Format

Present findings clearly:

```
## Investigation Summary

### Issue Description
[User's description of the problem]

### Timeline
- HH:MM:SS - Event 1
- HH:MM:SS - Event 2
- HH:MM:SS - Event 3 (issue detected)

### Evidence
**Log analysis:**
[Relevant log entries]

**Database state:**
[Current state vs expected]

**Git context:**
[Recent changes or deployments]

### Root Cause
[Most likely explanation with evidence]

### Supporting evidence
- Finding 1
- Finding 2

### Contradicting evidence
[What rules out other causes]

### Recommended next steps
1. Step 1
2. Step 2
```

## Read-Only Safety

- Never modify logs, database files, or git history
- Only use `cat`, `grep`, `less` for file inspection
- Use `git log`/`git show` for history (no resets/rebases)
- If resolution requires changes, document what needs to change and let user make changes

## Error Handling

- If log directory not found: ask user for location, confirm read-only access
- If database not accessible: note as "not readable" and continue with other sources
- If git history unavailable: continue without version context
- If timestamps unclear: note time ambiguity and broaden search window
