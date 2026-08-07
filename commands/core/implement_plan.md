---
name: implement_plan
description: Implement technical plans with phase-by-phase verification
model: planning
---

# Implement Plan

You are tasked with implementing an approved technical plan. These plans contain phases with specific changes and success criteria.

## Setup (read before proceeding)

1. Check if `specs.config.yaml` exists at project root
2. If `thoughts_directory: true`, use `{thoughts_path}` for document references
3. Note the plan storage location for retrieving and updating plan files

## Getting Started

When given a plan path:
- Read the plan completely and check for any existing checkmarks (- [x])
- Read the original ticket and all files mentioned in the plan
- **Read files fully** - never use limit/offset parameters, you need complete context
- Think deeply about how the pieces fit together
- Create a todo list to track your progress
- Start implementing if you understand what needs to be done

If no plan path provided, ask for one.

## Implementation Philosophy

Plans are carefully designed, but reality can be messy. Your job is to:
- Follow the plan's intent while adapting to what you find
- Implement each phase fully before moving to the next
- Verify your work makes sense in the broader codebase context
- Update checkboxes in the plan as you complete sections

When things don't match the plan exactly, think about why and communicate clearly. The plan is your guide, but your judgment matters too.

If you encounter a mismatch:
- STOP and think deeply about why the plan can't be followed
- Present the issue clearly:
  ```
  Issue in Phase [N]:
  Expected: [what the plan says]
  Found: [actual situation]
  Why this matters: [explanation]

  How should I proceed?
  ```


## Scope Discipline

**Touch only what the plan specifies.** This is non-negotiable.

- If a change requires modifying a file not listed in the plan, STOP.
- Present the deviation: what file, why it's needed, what happens if you don't.
- Wait for explicit approval before touching it.
- If approved, note the deviation in the plan file itself.

Do not:
- Refactor adjacent code that "could be better"
- Fix unrelated TODOs you encounter
- Modernize imports or patterns in files you're passing through
- "Clean up" code outside the plan's scope

A focused PR that does one thing is mergeable. A PR that does one thing plus three drive-by improvements gets reverted.

## Verification Approach

After implementing a phase, run the appropriate automated verification commands from the plan's success criteria.

**Key verification patterns:**
- Run your project's build command for backend changes
- Run your project's test command for unit/integration tests
- Run your project's type checking (if applicable)
- Run your project's linting/formatting checks (if applicable)

**The pairing gate.** Before checking off a plan item, confirm every `automated` criterion that item satisfies has a binding row in the plan's `## Criterion Bindings` table, and run that bound group. An item whose criterion is unbound cannot be checked off: report the unbound identifier and stop, per [criterion-binding](../../conventions/criterion-binding.md).

**Failing-first evidence.** Every `automated` criterion earns two records in the evidence file the plan declares, written in the schema at [criterion-binding](../../conventions/criterion-binding.md) §4:

1. **Before** writing the change that satisfies the criterion, run its bound group and record the failure. The state you run against is that criterion's pre-change code as §8 defines it — the state just before this specific change, not the branch point.
2. **After** the change, re-run the same invocation and record the pass. Its code-state reference must not be the one the red record carries.
3. A record that omits any of §4's three required elements counts as no record at all.
4. If the group passes on first contact, you have no red record and the criterion is unsatisfied. Report it as such and name both causes §8 gives — the group may not discriminate this change, or the behavior may already be there. Fix the group or take the criterion back to `/spec` for re-moding; do not treat that run as evidence.
5. Do not check off a plan item whose criterion has no red record. Name the criterion missing failing-first evidence and stop.

**Evidence strength.** Every record carries a `strength` value, and which one you may write is decided by the invocation you actually ran, not by how confident you are. Read `test_group_command` from `specs.config.yaml` and follow [criterion-binding](../../conventions/criterion-binding.md) §5:

- Key set → substitute the bound group into the template and record `strength: single-group`. The run executed that group and nothing else.
- Key unset, and the bound group is not file-level → you fall back to the full suite. Record `strength: degraded` with `degraded_reason: "test_group_command unset"`.
- A degraded record must capture output in which the bound group's own outcome is visible on its own. If you cannot point at the lines saying whether *that* group passed or failed, the record is rejected outright — it is not weaker red or green evidence, it is none.

Red→green is additive. It displaces nothing: the full-suite and no-regression obligations in [definition-of-done](../../references/definition-of-done.md) and in this command's own Verification checklist below apply exactly as before.

After running automated checks:
- Fix any issues before proceeding
- Update your progress in both the plan and your todos
- Check off completed items in the plan file itself using Edit
- **Pause for human verification**: After completing all automated verification for a phase, pause and inform the human that the phase is ready for manual testing. Use this format:
  ```
  Phase [N] Complete - Ready for Manual Verification

  Automated verification passed:
  - [List automated checks that passed]

  Please perform the manual verification steps listed in the plan:
  - [List manual verification items from the plan]

  Let me know when manual testing is complete so I can proceed to Phase [N+1].
  ```

Phase completion is gated on verification. There are no exceptions to this sequence. After completing all automated verification for a phase, you must present results and wait for human confirmation before starting the next phase. A phase that passes automated checks but skips manual verification is not complete.

Do not check off items in the manual testing steps until confirmed by the user.


## Common Shortcuts to Avoid

When implementing a plan, you will be tempted to rationalize skipping steps. These are the most common excuses and why they're wrong:

| Excuse | Rebuttal |
|--------|----------|
| "This change is small enough to do without phase-by-phase verification." | Small changes cause large outages. Run verification after every phase regardless of size. |
| "These phases are closely related, so I'll implement them together." | Phase boundaries exist because verification between them catches compounding errors. Implement one at a time. |
| "The plan is slightly outdated so I'll adapt as I go." | If the plan doesn't match reality, STOP and present the deviation. Don't silently rewrite the plan while implementing. |
| "I need to refactor this adjacent file to make my change work." | If a file isn't in the plan, don't touch it. Present the dependency and let the human decide. |
| "The criterion is clearly satisfied — I'll tick the box and sort the binding out later." | Ticking an unbound criterion is the exact move the pairing gate exists to stop. Get the binding into the plan first, run the group, then check the box. |
| "The bound group passed on the first run, so that criterion is already done." | A group that never failed tells you nothing about your change. That run is not red evidence — report the criterion unsatisfied, name both causes, and fix the group before continuing. |
| "I'll implement first and capture the red run afterwards from memory." | Red evidence is a recorded run against the pre-change state. Once the change is in, that state is gone and the record would be a reconstruction, not evidence. |
| "The whole suite went red, and my group is in the suite, so that is my red record." | Only if the output shows that group's own outcome. A suite-level failure that could have come from anywhere is not evidence about your criterion — mark it degraded with the reason, and if the group's result is not identifiable in the captured output, the pairing gate has no record at all. |

## If You Get Stuck

When something isn't working as expected:
- First, make sure you've read and understood all the relevant code
- Consider if the codebase has evolved since the plan was written
- Present the mismatch clearly and ask for guidance

Use sub-tasks sparingly - mainly for targeted debugging or exploring unfamiliar territory.

## Resuming Work

If the plan has existing checkmarks:
- Trust that completed work is done
- Pick up from the first unchecked item
- Verify previous work only if something seems off

Remember: You're implementing a solution, not just checking boxes. Keep the end goal in mind and maintain forward momentum.

## Red Flags

Observable signs that you are drifting off this workflow:

- You are editing a file that is not listed in the plan, without having stopped to ask
- You have completed two phases without running any verification in between
- You are marking a checkbox complete based on "should work" rather than an observed result
- You hit a plan/reality mismatch and adapted silently instead of presenting the issue
- Your diff is growing with cleanups and refactors the plan never asked for
- You are checking off an item whose acceptance criterion has no binding row — the pairing gate is being walked past
- You are recording a green run for a criterion that has no red run before it, or writing a record with the command, the code state, or the captured output left out
- You are writing `strength: single-group` on a record produced by a run that swept up other groups too, or leaving `degraded_reason` off a degraded record

## Verification

Before declaring implementation complete:

- [ ] Every phase's success criteria were checked and passed — with observed output, not assumption
- [ ] All checkboxes in the plan file reflect actual state (nothing checked optimistically)
- [ ] Any deviation from the plan is noted in the plan file with the user's approval recorded
- [ ] No files outside the plan's scope were modified
- [ ] Tests and checks specified by the plan were run in this session, and their results reported
- [ ] No item was checked off while the pairing gate showed its automated criterion unbound
- [ ] Every automated criterion has a recorded failing run and a recorded passing run, taken at different code states, each complete on the three required elements
- [ ] Any bound group that passed on first contact was reported unsatisfied with both causes named, and was never written up as red evidence
- [ ] Every record states the strength the invocation actually earned, degraded ones carry their reason, and no degraded record was kept whose output leaves the bound group's outcome unidentifiable
