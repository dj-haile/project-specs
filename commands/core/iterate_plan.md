---
description: Iterate on existing implementation plans with thorough research and updates
model: opus
---

# Iterate Implementation Plan

You are tasked with updating existing implementation plans based on user feedback. You should be skeptical, thorough, and ensure changes are grounded in actual codebase reality.

## Setup (read before proceeding)

1. Check if `specs.config.yaml` exists at project root
2. If `thoughts_directory: true`, use `{thoughts_path}` for document storage
3. If `thoughts_directory: false` or config missing, ask the user where plans are stored
4. Note the `ticket_id_pattern` for extracting ticket IDs

## Initial Response

When this command is invoked:

1. **Parse the input to identify**:
   - Plan file path
   - Requested changes/feedback

2. **Handle different input scenarios**:

   **If NO plan file provided**:
   ```
   I'll help you iterate on an existing implementation plan.

   Which plan would you like to update? Please provide the path to the plan file.

   Tip: You can list recent plans with `ls -lt [plans-directory] | head`
   ```
   Wait for user input, then re-check for feedback.

   **If plan file provided but NO feedback**:
   ```
   I've found the plan at [path]. What changes would you like to make?

   For example:
   - "Add a phase for migration handling"
   - "Update the success criteria to include performance tests"
   - "Adjust the scope to exclude feature X"
   - "Split Phase 2 into two separate phases"
   ```
   Wait for user input.

   **If BOTH plan file AND feedback provided**:
   - Proceed immediately to Step 1
   - No preliminary questions needed

## Process Steps

### Step 1: Read and Understand Current Plan

1. **Read the existing plan file COMPLETELY**:
   - Use the Read tool WITHOUT limit/offset parameters
   - Understand the current structure, phases, and scope
   - Note the success criteria and implementation approach

2. **Understand the requested changes**:
   - Parse what the user wants to add/modify/remove
   - Identify if changes require codebase research
   - Determine scope of the update

### Step 2: Research If Needed

**Only perform research if the changes require new technical understanding.**

If the user's feedback requires understanding new code patterns or validating assumptions:

1. **Create a research todo list** using TodoWrite

2. **Use built-in tools for research**:
   - **Glob** - To find relevant files by pattern
   - **Grep** - To search for specific code patterns or text
   - **Read** - To examine file contents in detail

   **Be specific about your search**:
   - Focus on relevant directories mentioned in the plan
   - Search for patterns related to the requested changes
   - Read files completely (no limit/offset) for thorough understanding

3. **Read any new files identified by research**:
   - Read them FULLY into the main context
   - Cross-reference with the plan requirements

4. **Complete all research** before proceeding

### Step 3: Present Understanding and Approach

Before making changes, confirm your understanding:

```
Based on your feedback, I understand you want to:
- [Change 1 with specific detail]
- [Change 2 with specific detail]

My research found:
- [Relevant code pattern or constraint]
- [Important discovery that affects the change]

I plan to update the plan by:
1. [Specific modification to make]
2. [Another modification]

Does this align with your intent?
```

Get user confirmation before proceeding.

### Step 4: Update the Plan

1. **Make focused, precise edits** to the existing plan:
   - Use the Edit tool for surgical changes
   - Maintain the existing structure unless explicitly changing it
   - Keep all file:line references accurate
   - Update success criteria if needed

2. **Ensure consistency**:
   - If adding a new phase, ensure it follows the existing pattern
   - If modifying scope, update "What We're NOT Doing" section
   - If changing approach, update "Implementation Approach" section
   - Maintain the distinction between automated vs manual success criteria

3. **Preserve quality standards**:
   - Include specific file paths and line numbers for new content
   - Write measurable success criteria
   - Use generic verification commands (reference project's build/test tools)
   - Keep language clear and actionable

### Step 5: Review Changes

1. **Present the changes made**:
   ```
   I've updated the plan at `[filename].md`

   Changes made:
   - [Specific change 1]
   - [Specific change 2]

   The updated plan now:
   - [Key improvement]
   - [Another improvement]

   Would you like any further adjustments?
   ```

2. **Be ready to iterate further** based on feedback

## Important Guidelines

1. **Be Skeptical**:
   - Don't blindly accept change requests that seem problematic
   - Question vague feedback - ask for clarification
   - Verify technical feasibility with code research
   - Point out potential conflicts with existing plan phases

2. **Be Surgical**:
   - Make precise edits, not wholesale rewrites
   - Preserve good content that doesn't need changing
   - Only research what's necessary for the specific changes
   - Don't over-engineer the updates

3. **Be Thorough**:
   - Read the entire existing plan before making changes
   - Research code patterns if changes require new technical understanding
   - Ensure updated sections maintain quality standards
   - Verify success criteria are still measurable

4. **Be Interactive**:
   - Confirm understanding before making changes
   - Show what you plan to change before doing it
   - Allow course corrections
   - Don't disappear into research without communicating

5. **Track Progress**:
   - Use TodoWrite to track update tasks if complex
   - Update todos as you complete research
   - Mark tasks complete when done

6. **No Open Questions**:
   - If the requested change raises questions, ASK
   - Research or get clarification immediately
   - Do NOT update the plan with unresolved questions
   - Every change must be complete and actionable

## Success Criteria Guidelines

When updating success criteria, always maintain the two-category structure:

1. **Automated Verification** (can be run by execution agents):
   - Build compilation and tests via project's build system
   - Unit tests
   - Integration tests
   - Specific files that should exist
   - Code type checking

2. **Manual Verification** (requires human testing):
   - UI/UX functionality
   - Performance under real conditions
   - Edge cases that are hard to automate
   - User acceptance criteria

## Research Best Practices

When conducting research for plan updates:

1. **Only research if truly needed** - don't research for simple changes
2. **Use appropriate tools for the task**:
   - **Glob** for finding files by pattern
   - **Grep** for code pattern searches
   - **Read** for detailed examination of specific files
3. **Be specific about your search scope**
4. **Read files completely** - don't use limit/offset unless absolutely necessary
5. **Include specific file:line references** in your findings
6. **Verify findings** - cross-check against actual code before using

## Example Interaction Flows

**Scenario 1: User provides everything upfront**
```
User: /iterate_plan [plan-path] - add phase for monitoring setup
Assistant: [Reads plan, researches monitoring patterns in codebase, updates plan]
```

**Scenario 2: User provides just plan file**
```
User: /iterate_plan [plan-path]
Assistant: I've found the plan. What changes would you like to make?
User: Split Phase 2 into two phases - one for backend, one for frontend
Assistant: [Proceeds with update]
```

**Scenario 3: User provides no arguments**
```
User: /iterate_plan
Assistant: Which plan would you like to update? Please provide the path...
User: [plan-path]
Assistant: I've found the plan. What changes would you like to make?
User: Add more specific success criteria for automated testing
Assistant: [Proceeds with update]
```
