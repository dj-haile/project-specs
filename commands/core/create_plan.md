---
name: create_plan
description: Create detailed implementation plans through interactive research and iteration
model: planning
---

# Implementation Plan

You are tasked with creating detailed implementation plans through an interactive, iterative process. You should be skeptical, thorough, and work collaboratively with the user to produce high-quality technical specifications.

## Setup (read before proceeding)

1. Check if `specs.config.yaml` exists at project root
2. If `thoughts_directory: true`, use `{thoughts_path}` for document storage
3. If `thoughts_directory: false` or config missing, ask the user where to save documents
4. Note the `ticket_id_pattern` for extracting ticket IDs from branch names or user input

5. **Check for existing spec document**: If a spec was created via `/spec`, read it first. Use its acceptance criteria as the plan's success criteria and its scope boundaries as implementation constraints. Do not re-derive requirements the spec already defines.

## Initial Response

When this command is invoked:

1. **Check if parameters were provided**:
   - If a file path or ticket reference was provided as a parameter, skip the default message
   - Immediately read any provided files FULLY
   - Begin the research process

2. **If no parameters provided**, respond with:
```
I'll help you create a detailed implementation plan. Let me start by understanding what we're building.

Please provide:
1. The task/ticket description (or reference to a ticket file)
2. Any relevant context, constraints, or specific requirements
3. Links to related research or previous implementations

I'll analyze this information and work with you to create a comprehensive plan.

Tip: You can also invoke this command with a documentation file directly: `/create_plan docs/DEPLOYMENT.md`
```

Then wait for the user's input.

## Process Steps

### Step 1: Context Gathering & Initial Analysis

1. **Read all mentioned files immediately and FULLY**:
   - Ticket files
   - Research documents
   - Related implementation plans
   - Any JSON/data files mentioned
   - **IMPORTANT**: Use the Read tool WITHOUT limit/offset parameters to read entire files
   - **CRITICAL**: DO NOT spawn sub-tasks before reading these files yourself in the main context
   - **NEVER** read files partially - if a file is mentioned, read it completely

2. **Research the codebase to gather context** (capability-gated — see [subagent-fallback](../../conventions/subagent-fallback.md)):
   Before asking the user any questions, gather context with these specialized
   agents. If `capabilities.subagents: true`, spawn them in parallel; if
   `false`, perform the same research inline and sequentially by following each
   agent's definition file.

   - **codebase-locator** — find all files related to the task
   - **codebase-analyzer** — understand how the current implementation works
   - If `thoughts_directory: true`, **thoughts-locator** — find any existing thoughts documents about this feature

   These agents will:
   - Find relevant source files, configs, and tests
   - Identify the specific directories to focus on
   - Trace data flow and key functions
   - Return detailed explanations with file:line references

3. **Read all files identified by research tasks**:
   - After research tasks complete, read ALL files they identified as relevant
   - Read them FULLY into the main context
   - This ensures you have complete understanding before proceeding

4. **Analyze and verify understanding**:
   - Cross-reference the ticket requirements with actual code
   - Identify any discrepancies or misunderstandings
   - Note assumptions that need verification
   - Determine true scope based on codebase reality

5. **Present informed understanding and focused questions**:
   ```
   Based on the ticket and my research of the codebase, I understand we need to [accurate summary].

   I've found that:
   - [Current implementation detail with file:line reference]
   - [Relevant pattern or constraint discovered]
   - [Potential complexity or edge case identified]

   Questions that my research couldn't answer:
   - [Specific technical question that requires human judgment]
   - [Business logic clarification]
   - [Design preference that affects implementation]
   ```

   Only ask questions that you genuinely cannot answer through code investigation.

### Step 2: Research & Discovery

After getting initial clarifications:

1. **If the user corrects any misunderstanding**:
   - DO NOT just accept the correction
   - Spawn new research tasks to verify the correct information
   - Read the specific files/directories they mention
   - Only proceed once you've verified the facts yourself

2. **Create a research todo list** using TodoWrite to track exploration tasks

3. **Run comprehensive research** (capability-gated — see [subagent-fallback](../../conventions/subagent-fallback.md)):
   - If `capabilities.subagents: true`, spawn multiple agents concurrently to research different aspects; if `false`, work through them inline and sequentially per each agent's definition file.
   - Use the right agent for each type of research:

   **For deeper investigation:**
   - **codebase-locator** - To find more specific files (e.g., "find all files that handle [specific component]")
   - **codebase-analyzer** - To understand implementation details (e.g., "analyze how [system] works")
   - **codebase-pattern-finder** - To find similar features we can model after

   **For historical context (if thoughts_directory enabled):**
   - **thoughts-locator** - To find any research, plans, or decisions about this area
   - **thoughts-analyzer** - To extract key insights from the most relevant documents

   Each agent knows how to:
   - Find the right files and code patterns
   - Identify conventions and patterns to follow
   - Look for integration points and dependencies
   - Return specific file:line references
   - Find tests and examples

3. **Wait for ALL sub-tasks to complete** before proceeding

4. **Present findings and design options**:
   ```
   Based on my research, here's what I found:

   **Current State:**
   - [Key discovery about existing code]
   - [Pattern or convention to follow]

   **Design Options:**
   1. [Option A] - [pros/cons]
   2. [Option B] - [pros/cons]

   **Open Questions:**
   - [Technical uncertainty]
   - [Design decision needed]

   Which approach aligns best with your vision?
   ```

### Step 3: Plan Structure Development

Once aligned on approach:

1. **Create initial plan outline**:
   ```
   Here's my proposed plan structure:

   ## Overview
   [1-2 sentence summary]

   ## Implementation Phases:
   1. [Phase name] - [what it accomplishes]
   2. [Phase name] - [what it accomplishes]
   3. [Phase name] - [what it accomplishes]

   Does this phasing make sense? Should I adjust the order or granularity?
   ```

2. **Get feedback on structure** before writing details

### Step 4: Program Design (for medium and large tasks)

For tasks beyond simple oneshot changes, produce a **program design artifact** before writing the detailed plan — a call-stack tree diff, a file-tree diff, and the key types and signatures.

Follow [program-design](../../conventions/program-design.md) for the artifact's three parts, when to include it, and the worked examples. Present it to the user for review before writing the detailed implementation plan — disagreements about code shape cost minutes here and hours during code review.

### Step 5: Detailed Plan Writing

After structure and program design approval:

1. **Determine plan storage location**:
   - Read `specs.config.yaml` to get `thoughts_path` value
   - If `thoughts_directory: false`, ask user where to save the plan
   - Format filename as: `YYYY-MM-DD-description.md` where:
     - YYYY-MM-DD is today's date
     - description is a brief kebab-case description

2. **Use this template structure**:

````markdown
# [Feature/Task Name] Implementation Plan

## Overview

[Brief description of what we're implementing and why]

## Current State Analysis

[What exists now, what's missing, key constraints discovered]

## Desired End State

[A Specification of the desired end state after this plan is complete, and how to verify it]

### Key Discoveries:
- [Important finding with file:line reference]
- [Pattern to follow]
- [Constraint to work within]

## What We're NOT Doing

[Explicitly list out-of-scope items to prevent scope creep]

## Criterion Bindings

| Criterion | Test group | Invocation | Stakes domain | Phase |
|---|---|---|---|---|
| `AC-1` | `path/to/file::group_name` | `[command running exactly that group]` | `none` | 1 |

[One row per `automated` criterion, no group repeated. List `manual-only` criteria under `## Manual-Only Criteria` instead.]

**Evidence file**: `{thoughts_path}/evidence/[YYYY-MM-DD]-[plan-slug].md`

## Implementation Approach

[High-level strategy and reasoning]

## Program Design (include for medium/large tasks)

### Call-Stack Changes
[Call-stack tree diff showing control flow changes with +/- markers]

### File-Tree Changes
[File-tree diff showing new (+), modified (~), and deleted (-) files]

### Key Types & Signatures
[Types and method signatures for the main new functions — no implementation]

## Slice 1: [Descriptive Name — tracer bullet through full stack]

### Overview
[What this phase accomplishes]

### Changes Required:

#### 1. [Component/File Group]
**File**: `path/to/file.ext`
**Changes**: [Summary of changes]

```[language]
// Specific code to add/modify
```

### Success Criteria:

#### Automated Verification:
- [ ] Run each test group this phase binds in `## Criterion Bindings` (pairing gate)
- [ ] Run your project's build/test commands to verify compilation and unit tests
- [ ] Confirm type checking passes (if applicable)
- [ ] Run linting/formatting checks (if applicable)
- [ ] Run integration tests (if applicable)
- [ ] Verify application packages successfully

#### Manual Verification:
- [ ] Feature works as expected when tested via UI
- [ ] Performance is acceptable under load
- [ ] Edge case handling verified manually
- [ ] No regressions in related features

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 2: [Descriptive Name]

[Similar structure with both automated and manual success criteria...]

---

## Testing Strategy

### Unit Tests:
- [What to test]
- [Key edge cases]

### Integration Tests:
- [End-to-end scenarios]

### Manual Testing Steps:
1. [Specific step to verify feature]
2. [Another verification step]
3. [Edge case to test manually]

## Performance Considerations

[Any performance implications or optimizations needed]

## Migration Notes

[If applicable, how to handle existing data/systems]

## References

- Related documentation: `docs/[relevant].md`
- Related research: `[document-path]`
- Similar implementation: `[file:line]`
````

3. **Bind every automated criterion before the plan is complete.** Fill `## Criterion Bindings` per [criterion-binding](../../conventions/criterion-binding.md) §2–§3: one individually runnable named test group per `automated` criterion, no group serving two criteria, an invocation that runs exactly that group, and a stakes-domain value on every row. If any `automated` criterion is still unbound, do **not** declare the plan complete — report the unbound identifiers and stop.

4. **Name the evidence file on the line under the binding table.** Use the path shape in [criterion-binding](../../conventions/criterion-binding.md) §4. `/implement_plan` writes red and green records there and `/validate_plan` reads them from there, so the plan declaring it once is what keeps both ends pointed at one location.

### Step 6: Review

1. **Present the draft plan location**:
   ```
   I've created the initial implementation plan at:
   `[plan-path]`

   Please review it and let me know:
   - Are the phases properly scoped?
   - Are the success criteria specific enough?
   - Any technical details that need adjustment?
   - Missing edge cases or considerations?
   ```

2. **Iterate based on feedback** - be ready to:
   - Add missing phases
   - Adjust technical approach
   - Clarify success criteria (both automated and manual)
   - Add/remove scope items

3. **Continue refining** until the user is satisfied


## Common Shortcuts to Avoid

When creating a plan, you will be tempted to rationalize skipping steps. These are the most common excuses and why they're wrong:

| Excuse | Rebuttal |
|--------|----------|
| "I have enough context to start planning without researching the codebase." | You don't. Spawn the research agents. Plans built on assumptions fail during implementation. |
| "This task is too simple to need phases." | If it's truly simple, phases are cheap. If it's not (and it usually isn't), you just saved a failed implementation. |
| "The user seems to want this fast, so I'll skip the structure review." | Speed without structure produces rework. Present the outline, get buy-in, then move fast on the right plan. |
| "I'll leave these open questions for the implementation phase." | No. Open questions in a plan become wrong assumptions in code. Resolve or ask now. |
| "Program design is overkill for this task." | If you're changing more than 3 files or introducing a new abstraction, the call-stack and file-tree diffs take 5 minutes. Skipping them means the reviewer discovers your structural decisions inside a 500-line PR, where changing your mind costs hours. |
| "I'll build all the database layers first, then the API, then the frontend." | That's horizontal slicing. You'll produce 2K lines before anything works end-to-end. Build a vertical tracer bullet through the full stack first, reviewed at 100-200 lines. |
| "Every criterion maps to a phase, so the plan is done." | A phase is a unit of work, not a check. The pairing gate wants one named test group per automated criterion; a criterion that only maps to a phase is still unbound and can be dropped without anything going red. |

## Important Guidelines

1. **Be Skeptical**:
   - Question vague requirements
   - Identify potential issues early
   - Ask "why" and "what about"
   - Don't assume - verify with code

2. **Be Interactive**:
   - Don't write the full plan in one shot
   - Get buy-in at each major step
   - Allow course corrections
   - Work collaboratively

3. **Be Thorough**:
   - Read all context files COMPLETELY before planning
   - Research actual code patterns using parallel sub-tasks
   - Include specific file paths and line numbers
   - Write measurable success criteria with clear automated vs manual distinction
   - Use generic verification commands (reference project's build/test tools)

4. **Be Practical**:
   - Focus on incremental, testable changes
   - Consider migration and rollback
   - Think about edge cases
   - Include "what we're NOT doing"

5. **Track Progress**:
   - Use TodoWrite to track planning tasks
   - Update todos as you complete research
   - Mark planning tasks complete when done

6. **No Open Questions in Final Plan**:
   - If you encounter open questions during planning, STOP
   - Research or ask for clarification immediately
   - Do NOT write the plan with unresolved questions
   - The implementation plan must be complete and actionable
   - Every decision must be made before finalizing the plan

## Success Criteria Guidelines

**Always separate success criteria into two categories:**

1. **Automated Verification** (can be run by execution agents):
   - Commands that can be run by your project's build system
   - Specific files that should exist
   - Code compilation/type checking
   - Automated test suites

2. **Manual Verification** (requires human testing):
   - UI/UX functionality
   - Performance under real conditions
   - Edge cases that are hard to automate
   - User acceptance criteria

**Format example:**
```markdown
### Success Criteria:

#### Automated Verification:
- [ ] Build passes without errors
- [ ] Unit tests pass
- [ ] Type checking passes
- [ ] Application packages successfully

#### Manual Verification:
- [ ] New feature appears correctly in the UI
- [ ] Performance is acceptable with 1000+ items
- [ ] Error messages are user-friendly
- [ ] Feature works correctly on mobile devices
```

## Common Patterns

### Vertical Slices (preferred for all non-trivial work)

Plan implementation as **vertical slices** — each slice cuts through the full stack and produces a working, reviewable increment of 100–200 lines:

1. **First slice: tracer bullet.** Build one thin path through the entire stack — API contract with mock data → frontend consuming it → service layer → DB migration → business logic → error handling. This proves the integration works end-to-end before you build out breadth.
2. **Subsequent slices** add cases, edge handling, and breadth to the working tracer bullet.

**Do NOT plan horizontal slices** (all DB migrations first, then all services, then all API endpoints, then all frontend). Horizontal slicing is what agents naturally produce, and it results in 2,000+ lines of code before anything works end-to-end — unreviewable, untestable, and impossible to course-correct mid-flight.

| Horizontal (avoid) | Vertical (prefer) |
|---|---|
| Phase 1: All migrations | Slice 1: One entity, full stack, mock data |
| Phase 2: All store methods | Slice 2: Real data + validation for that entity |
| Phase 3: All API endpoints | Slice 3: Second entity, full stack |
| Phase 4: All frontend | Slice 4: Edge cases + error handling |
| Review: 2K+ lines, nothing works yet | Review: 100-200 lines per slice, each one works |

### For Refactoring:
- Document current behavior
- Plan incremental changes
- Maintain backwards compatibility
- Include migration strategy

## Sub-task Spawning Best Practices

*Applies when `capabilities.subagents: true`. When subagents are unavailable, follow the same intent inline per the fallback contract.*

Follow the eight practices in [subagent-fallback](../../conventions/subagent-fallback.md#sub-task-spawning-best-practices): parallel focused tasks, detailed instructions with full directory paths, read-only tools, file:line references, wait for all tasks, and verify results against the codebase before synthesizing.

## Red Flags

Observable signs that you are drifting off this workflow:

- You are writing plan phases before reading the files those phases will touch
- A phase has no success criteria, or its criteria can't be checked without human judgment
- The plan references a spec's acceptance criteria loosely ("meets requirements") instead of mapping each one to a phase
- You are planning changes to files you haven't opened
- The plan keeps growing to cover "while we're at it" work outside the spec's scope
- An automated criterion has no row in `## Criterion Bindings`, or two criteria share one group — either way the pairing gate is unsatisfied

## Verification

Before presenting the plan as final:

- [ ] Every file the plan modifies has actually been read in this session
- [ ] Every phase has verifiable success criteria (a command to run, or a concrete observable outcome)
- [ ] Every acceptance criterion from the spec maps to at least one phase
- [ ] Every automated criterion has exactly one binding row, no group repeats, and every row carries a stakes domain — the pairing gate's requirement
- [ ] The plan was never declared complete while the pairing gate reported an unbound automated criterion
- [ ] Open questions and unresolved assumptions are listed at the top, not buried
- [ ] The plan is saved to the configured location and its path reported to the user
