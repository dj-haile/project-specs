---
name: spec
description: Define requirements and acceptance criteria before planning
model: planning
---

# Spec

You are tasked with producing a requirements specification. You are NOT planning implementation yet. Your job is to define WHAT we're building, WHY, and how we'll know it's done.

## Setup (read before proceeding)

1. Check if `specs.config.yaml` exists at project root
2. If `thoughts_directory: true`, use `{thoughts_path}` for document storage
3. If `thoughts_directory: false` or config missing, ask the user where to save the spec document
4. Note the `ticket_id_pattern` for extracting ticket IDs from branch names or user input

## Initial Response

When this command is invoked:

1. **Check if parameters were provided**:
   - If a file path, ticket reference, or description was provided, read it immediately and fully
   - Begin the requirements discovery process

2. **If no parameters provided**, respond with:
```
I'll help you define clear requirements before we start planning.

Please provide:
1. What problem are you trying to solve? (or a ticket/issue reference)
2. Who is affected by this problem?
3. Any constraints I should know about (timeline, tech stack, dependencies)?

Tip: Starting with /spec before /create_plan saves hours of rework by catching assumptions early.
```

Then wait for the user's input.

## Output Artifact

Produce a spec document with these sections:

### 1. Problem Statement
What's broken or missing, and for whom. Be specific — "users can't X" not "X needs improvement."

### 2. Desired Outcome
What success looks like from the user's perspective. Describe the end state, not the implementation.

### 3. Acceptance Criteria
Specific, testable conditions. Each criterion carries a stable identifier and exactly one verification mode:

```
**AC-1 — [short title].**
`mode: automated`
Given [precondition] when [action] then [expected result].
```

Assign identifiers and modes per [criterion-binding](../../conventions/criterion-binding.md) §1, which owns the identifier scheme, the parse rule, and the extra elements a `manual-only` criterion carries. Modes come from the closed set `automated` | `manual-only`, one per criterion — zero, two, or an unrecognized value makes the spec incomplete.

A `manual-only` criterion is not finished at the mode line. It carries all four of §1's labeled elements — why automation is not feasible, the exact steps to run, the observable condition that decides pass or fail, and who performs it. Any one of them missing makes the spec incomplete, exactly as a missing mode line does.

When any criterion is `manual-only`, the spec also carries a `## Manual-Only Approval` section recording `approved_by:`, `approved_at:`, and the identifiers approved. Step 4 covers how that approval is obtained.

Stay solution-neutral: name no test, file path, or framework in any criterion. Downstream, `/create_plan` binds each `automated` criterion to one test group; the spec supplies the identifier and the mode, nothing more.

Every criterion must be verifiable. Prefer automatable criteria where possible. If a criterion can't be tested, it's not a real requirement — rewrite it until it is.

### 4. Scope Boundaries
What's explicitly OUT of scope. This is as important as what's in scope. Be exhaustive — list everything that someone might reasonably assume is included but isn't.

### 5. Assumptions
List every assumption. Mark each as:
- **Verified** — confirmed through code research or stakeholder input
- **Needs confirmation** — believed true but not verified

Use research agents to verify assumptions against the actual codebase before finalizing.

### 6. Dependencies
What must exist or be true before work begins:
- External services or APIs
- Other features or PRs that must land first
- Configuration or infrastructure requirements
- Team decisions that haven't been made yet

### 7. Open Questions
Anything unresolved. **This section must be empty before passing to /create_plan.** If you can't resolve a question through research, escalate it to the user.

## Process Steps

### Step 1: Understand the Problem

1. **Read all provided context** — tickets, documents, code references
2. **Research the codebase** (capability-gated — see [subagent-fallback](../../conventions/subagent-fallback.md)): if `capabilities.subagents: true`, spawn these agents in parallel; if `false`, perform the same research inline and sequentially per each agent's definition file.
   - **codebase-locator** — find affected files and modules
   - **codebase-analyzer** — understand current behavior
   - If `thoughts_directory: true`, **thoughts-locator** — find prior work on this area
3. **Identify the real problem** — tickets describe symptoms, not root causes. Dig deeper.

### Step 2: Define Requirements

1. **Surface assumptions FIRST, before writing any spec content.** Silent assumptions are the most dangerous form of misunderstanding — the spec's entire purpose is to catch them before code exists. Present them in this exact format and wait for the user's response:

   ```
   ASSUMPTIONS I'M MAKING:
   1. [e.g., This is a web app, not native mobile]
   2. [e.g., Auth is session-based, per existing middleware in src/auth/]
   3. [e.g., PostgreSQL, based on the Prisma schema]
   → Correct me now, or I'll proceed with these.
   ```

   Do not silently fill in an ambiguous requirement with a guess. Either verify it through code research, or put it in this block.
2. **Write the problem statement** based on research, not just the ticket text
3. **Define acceptance criteria** — at least 3, preferably 5+
4. **Draw scope boundaries** — list at least 3 things that are out of scope
5. **Verify remaining assumptions** — at least 5 total, verified through code research where possible

### Step 3: Validate with the User

Present the draft spec and ask:
```
Here's my requirements spec based on the ticket and codebase research.

Key findings that shaped these requirements:
- [Discovery from codebase research]
- [Assumption that was verified or disproven]

Please review:
1. Are the acceptance criteria complete and testable?
2. Is anything missing from scope boundaries?
3. Do you agree with the assumptions?
4. Can you resolve the open questions?
```

### Step 4: Finalize

1. Resolve all open questions (or explicitly defer with user agreement)
2. Ensure every acceptance criterion is testable
3. **Get the manual-only set approved before saving.** Present every `manual-only` criterion together with its stated reason for not being automated, and wait for a human's approval. Record it in `## Manual-Only Approval` — who approved, when, and which identifiers. Until that record exists the spec does not save as complete. Under `ci_mode: true` in `specs.config.yaml`, never self-approve: stop, report the unapproved manual-only set, and leave it for a human to close.
4. Save the spec document:
   - If `thoughts_directory: true`: save to `{thoughts_path}/specs/YYYY-MM-DD-description.md`
   - Otherwise: save to the location the user specified
5. Present the final spec with:
```
Spec complete and saved to [path].

This spec defines [N] acceptance criteria across [scope summary].

Next step: Run /create_plan to design the implementation approach.
The plan will use these acceptance criteria as its success criteria.
```

## Key Behaviors

- **Do NOT suggest implementation approaches.** That's create_plan's job. If you catch yourself writing "we could implement this by...", stop and reframe as a requirement.
- **Challenge vague requirements.** "Improve performance" is not a requirement. "Response time under 200ms at p95" is.
- **Every acceptance criterion must be verifiable** — automatable preferred, but at minimum manually testable with clear pass/fail.
- **If the user says "just build it," push back.** Five minutes on spec saves hours of rework.
- **Research before writing.** Don't write requirements based on assumptions when you can verify against the actual codebase.

## Common Shortcuts to Avoid

When defining requirements, you will be tempted to rationalize skipping rigor. These are the most common excuses and why they're wrong:

| Excuse | Rebuttal |
|--------|----------|
| "Requirements are obvious from the ticket." | Tickets describe symptoms. Specs define solutions. Extract the actual acceptance criteria. |
| "We can figure out scope as we go." | Undefined scope is how a 2-day task becomes a 2-week task. Define boundaries now. |
| "The user knows what they want." | The user knows the problem. The spec translates that into verifiable outcomes. |
| "This is too small to need a spec." | If it's truly small, the spec takes 5 minutes. If it's not (and it usually isn't), you just saved a failed implementation. |
| "I'll write the criteria now and label the modes later." | An unlabeled criterion is invisible to the pairing gate: nothing binds it, nothing accounts for it, and it can be dropped silently. Assign the identifier and the mode as you write each criterion. |
| "The manual-only criteria are clearly fine — I'll approve them myself and note that I did." | Self-approval is not approval. `manual-only` is the one label the pairing gate cannot check for you, so a human signs off on the set and the spec records who and when. Under `ci_mode` you stop and report instead. |

## Integration with create_plan

When `/create_plan` is invoked after `/spec`:

1. The plan command should check for an existing spec file and reference it
2. Acceptance criteria from the spec become the plan's success criteria
3. Scope boundaries from the spec constrain what the plan can include
4. Assumptions marked "needs confirmation" must be resolved before planning proceeds

The handoff is: **spec defines what success looks like; plan defines how to get there.**

## Red Flags

Observable signs that you are drifting off this workflow. If you notice any of these in your own output, stop and correct course:

- You are describing HOW to build something (class names, file paths, libraries) — that's implementation, not requirements
- An acceptance criterion contains words like "better", "improved", or "faster" with no measurable threshold
- You have written more than two requirements without asking the user a single clarifying question
- You are filling in an ambiguous requirement with a guess instead of listing it as an assumption
- The spec has no explicit out-of-scope section
- A criterion has no identifier or no mode line, or names a test — the pairing gate cannot read it, and naming tests here is the plan's job
- A `manual-only` criterion is missing its reason, its steps, its pass/fail condition, or its named performer — or you are about to save the spec with no recorded human approval of the manual-only set

## Verification

Before declaring the spec complete, confirm every item below. If any fails, the spec is not done:

- [ ] Every acceptance criterion has a clear pass/fail test (automated preferred, manual acceptable)
- [ ] Every criterion carries a unique identifier and exactly one mode line, so the pairing gate can bind and account for it
- [ ] No criterion names a test, a file path, or a framework — the pairing gate binds tests in the plan, never in the spec
- [ ] Every `manual-only` criterion carries all four of its required elements, and the manual-only set has a recorded human approval — self-approval is not approval, and under `ci_mode: true` the run stopped instead
- [ ] The "Assumptions I'm Making" block was presented to the user and confirmed or corrected
- [ ] Scope boundaries state what is explicitly OUT of scope, not just what's in
- [ ] No implementation decisions appear anywhere in the document
- [ ] The spec file is saved to the configured location and its path reported to the user
