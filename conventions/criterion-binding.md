---
domain: verification
status: approved
sdlc_stage: all
---

# Criterion Binding — the acceptance-criteria pairing gate

Every automated acceptance criterion **MUST** be bound to exactly one individually runnable named test group, and **MUST** carry re-runnable evidence of that group failing before the change and passing after it.

This file is the **single normative source** for the pairing gate. `/spec`, `/create_plan`, `/implement_plan`, and `/validate_plan` reference these rules by relative link; none of them restates a rule defined here. The failing-first bar itself is not defined here either — it is the standing one in [definition-of-done](../references/definition-of-done.md), which this gate makes per-criterion and mechanical.

---

## 1. Criterion identity and mode

**Identifier.** `AC-<n>`, where `n` is a positive integer assigned in order of first appearance and never reused. A criterion inserted between published identifiers takes a lowercase-letter suffix ascending from `b` (`AC-3b`), so no existing identifier is renumbered. A deleted criterion retires its identifier on a `Retired identifiers:` line.

**Rendering.** A criterion block in a spec is exactly this shape:

```markdown
**AC-7 — Red evidence exists.**
`mode: automated`
Given [precondition] when [action] then [expected result].
```

**Parse rule.** A block opens on a line matching `^\*\*(AC-\d+[a-z]?) — .+\*\*$`. The next non-blank line must match ``^`mode: (automated|manual-only)`$``. Exactly one mode line per block — zero, two, or an unrecognized value makes the spec incomplete.

**Manual-only blocks** additionally carry all four elements as fixed labels, in this order:

```markdown
`mode: manual-only`
- *Why not automated:* …
- *Steps:* …
- *Pass/fail:* …
- *Performed by:* …
```

**The spec stays solution-neutral.** A criterion block may contain the mode line and, for `manual-only`, the four labeled elements — and nothing else structured. No `group:`, `test:`, or `file:` field; no path-like token matching `\S+\.(py|js|ts|tsx|go|rb|java|md)\b`; no test-framework name. A spec criterion **MUST NOT** name a test, a file path, or a test framework — tests are named by the plan, never by the spec.

---

## 2. Binding format in plans

The plan carries one section, `## Criterion Bindings`, with exactly one row per `automated` criterion:

| Criterion | Test group | Invocation | Stakes domain | Phase |
|---|---|---|---|---|
| `AC-27` | `scripts/validate.py::check_gate_sections` | `python3 scripts/validate.py --check check_gate_sections` | `none` | 3 |

- **Test group** — `<path>::<name>` for a class, `describe` block, or named assertion; bare `<path>` for a file-level group. Injectivity is checked on this column: a test group **MUST NOT** be bound to more than one criterion. Nesting between a file-level group and a named group inside the same file is permitted and must be declared in the plan.
- **Invocation** — the literal command that runs *exactly* that group. Copied verbatim into evidence records.
- **Stakes domain** — a value from the closed vocabulary in §3, comma-separated if several. A bound criterion with a missing stakes value makes the plan incomplete.
- **Phase** — the phase whose work satisfies the criterion. Determines the code state the red record is taken against (§7).

`manual-only` criteria never appear in this table. They are listed under `## Manual-Only Criteria` with a pointer to the spec's recorded approval.

---

## 3. Stakes domains and their keywords

Closed vocabulary: `none` · `auth` · `billing` · `data-integrity` · `security`.

**Assignment is mechanical, not judgment.** A criterion's stakes domain is the set of domains whose keyword set appears, case-insensitively, in that criterion's own spec text. If no keyword matches, the value is `none`. `/validate_plan` reads this column from the plan and never re-derives it, which is what keeps stakes handling inside the gate's reproducibility guarantee (§6).

| Domain | Keywords (case-insensitive, whole word) |
|---|---|
| `auth` | auth, authentication, authorization, login, logout, session, token, credential, password, permission, role, sso, oauth |
| `billing` | billing, payment, invoice, charge, refund, subscription, price, pricing, currency, tax, payout |
| `data-integrity` | migration, schema, backup, restore, delete, deletion, corruption, consistency, transaction, idempotent, integrity, checksum |
| `security` | security, vulnerability, injection, xss, csrf, secret, encryption, decryption, certificate, sandbox, privilege, exploit |

---

## 4. Evidence records

**Storage.** `{thoughts_path}/evidence/<YYYY-MM-DD>-<plan-slug>.md`, one file per plan, carrying the standard frontmatter of [thoughts-directory](thoughts-directory.md). Validation reports get the sibling location `{thoughts_path}/validations/<YYYY-MM-DD>-<plan-slug>.md`, each carrying a `validated_at_code_state:` field so §6's touched set is computable.

**Schema.** Each record is one fenced `yaml` block. No parser is shipped; the format is fixed so a human and a model read it identically.

```yaml
criterion: AC-27
group: scripts/validate.py::check_gate_sections
outcome: red                  # red | green
command: "python3 scripts/validate.py --check check_gate_sections"
code_state: "git:9f2c1ab7e4d38c05b6119ad2f7e0c4413ab2d9f1"
output: |
  exit 1
  ERROR commands/core/spec.md: section 'Red Flags' never mentions the obligation
strength: single-group        # single-group | degraded
recorded_at: "2026-08-07T14:02:11Z"
```

Every evidence record **MUST** contain `command`, `code_state`, and `output` — the three required elements. A record missing any one is treated as absent, and absent red evidence is a blocking verdict.

**`code_state` must be re-runnable.** Accepted forms: `git:<40-hex sha>` for a commit, or `git:<40-hex sha>` produced by `git stash create` for an uncommitted state — that yields a real dangling commit reachable with `git checkout`. A working-tree reference such as `git:<sha>-dirty` is not re-runnable, and a record carrying one is absent.

**Red and green must differ.** The green record's `code_state` **MUST** differ from the red record's for the same criterion.

**`strength`** is `single-group` when the invocation executes exactly the bound group and nothing else, and `degraded` when it executes a superset. Granularity is irrelevant: running `scripts/validate.py` for a criterion whose bound group *is* `scripts/validate.py` is `single-group`.

**A `degraded` record** additionally requires `degraded_reason:`, and its `output` must quote the lines that individually identify the bound group's outcome. If the bound group's outcome is not identifiable in the captured output, the record does not count as red or green evidence at all — it is rejected, not merely labeled.

---

## 5. Single-group invocation config

Two optional top-level keys in `specs.config.yaml`, documented in `specs.config.example.yaml`:

```yaml
# Optional. Command template for running ONE named test group individually.
# Placeholders: {group} = the full group name from the plan's binding table;
# {file} = everything before the last "::"; {name} = everything after it.
# Unset (default) → red/green evidence degrades to full-suite runs.
test_group_command: ""     # e.g. "pytest -q {file}::{name}" | "npm test -- -t {name}"

# Optional. Used for a file-level group (a group name with no "::"), and as the
# full-suite fallback when test_group_command is unset.
test_suite_command: ""     # e.g. "pytest -q" | "npm test"
```

**Substitution** is brace-delimited single-token replacement, matching the framework's existing `{thoughts_path}` convention. No shell interpolation — the group name is inserted verbatim. `{file}` and `{name}` split on the **last** `::`; if there is none, `{file}` is the whole name, `{name}` is empty, and `test_suite_command` is used.

**Degradation.** When `test_group_command` is unset and the bound group is not file-level, the evidence record sets `strength: degraded` with `degraded_reason: "test_group_command unset"`. A report must never present a degraded record as equivalent to single-group evidence. If the criterion's stakes domain is anything other than `none`, degraded evidence is a blocking verdict, naming the domain match and "set `test_group_command`" as the remediation.

---

## 6. Deterministic sample selection and the re-run floor

Sampling must be a pure function of the artifact set, so two independent validators select the same group. Random selection is excluded.

**Selection rule.**

1. Let `S` be the list of bound group names for every `automated` criterion holding **both** a red and a green record, sorted by byte value (`LC_ALL=C` ordering).
2. Let `H = SHA-256( "\n".join(green_code_state[g] for g in S) + "\n" )`, UTF-8 encoded, rendered lowercase hex.
3. Let `i = int(H[0:8], 16) mod len(S)`. The sampled group is `S[i]`.
4. If `len(S) == 0` there is nothing to sample; the unbound/no-evidence rules already produce the blocking verdict.

Reproduce by hand:

```bash
printf '%s\n' <green code_state values, in S order> | shasum -a 256
```

The hash input is the green code states, so the sample rotates as the code moves rather than pinning one group forever.

**Floor — one plus every criterion touched since the last validation.** The re-run set is:

> `{ the deterministic sample }` ∪ `{ every bound criterion whose criterion text or bound group changed since the last recorded validation }`

"Last recorded validation" is the newest file in `{thoughts_path}/validations/` carrying `validated_at_code_state:`. If none exists, the touched set is **all** bound criteria. Change detection is itself artifact-derived:

```bash
git diff --name-only <validated_at_code_state>..<current> -- <paths in bound group names>
git diff <validated_at_code_state>..<current> -- <spec file>   # criterion blocks that differ
```

**Re-run semantics.** Execute each selected record's stored `command` against its stored `code_state` and compare with the stored `output`. A command that cannot be re-run, or whose output contradicts the record, makes that criterion's evidence absent and the blocking verdict applies.

**Reproducibility.** Given identical spec, plan, evidence records, and repository state, the pairing and red→green portion of a validation is identical across two runs or two validators. Judgment-based findings elsewhere in the report may differ; this portion may not.

---

## 7. Verdict vocabulary

Named distinctly from the `blocking` / `concern` / `note` severities `/validate_plan` already imports from the plan-skeptic review, so the two vocabularies never collide.

| Per-criterion verdict | When |
|---|---|
| `pass` | automated; bound; red and green present and well-formed; re-run agreed if sampled |
| `gate-blocked` | unbound automated criterion; no red record, or a red record showing a pass; re-run impossible or contradicting; degraded evidence on a non-`none` stakes domain |
| `awaiting-human-verdict` | manual-only, no recorded human verdict |
| `deferred` | manual-only under `ci_mode: true` — non-success, non-halting, distinguishable from `gate-blocked` |
| `manual-pass` / `manual-fail` | a human recorded a verdict |
| `legacy-unenforced` | legacy spec; gate not enforced, reason stated |

**Overall run result.** `success` only if every criterion is `pass` or `manual-pass`. Any `gate-blocked` → `blocked`. Otherwise → `incomplete` (non-success, non-blocking). A fully green automated pipeline therefore cannot report success while any criterion is unbound or unevidenced.

---

## 8. What "pre-change code" means for red evidence

Pre-change code is **the code state immediately before the specific change that satisfies that criterion**, identified by the `Phase` column of the binding table — not the branch point. This is the only reading under which a criterion satisfied in a late phase can have red evidence at all, and it is what makes the red record discriminating rather than incidental.

A bound group that passes on its first run against that state is not red evidence. Report it unsatisfied, naming both possible causes: the group does not discriminate the change, or the behavior already exists.

---

## 9. Legacy specs

**Classification keys on the spec's own format, never on a date.** A spec in which no line matches §1's mode-line pattern is `legacy-unlabeled`. Nothing about when the spec was written, when its filename says it was written, or when this convention landed enters the decision — a spec authored today with no mode lines is legacy, and one upgraded years ago is not. Reading the file is the whole test, so two readers reach the same classification.

**All three downstream commands accept a legacy spec and proceed without error.** `/create_plan`, `/implement_plan`, and `/validate_plan` do their ordinary work against it. The gate simply has nothing to act on: no identifiers to bind, no modes to separate automated from manual, and therefore no binding table and no evidence obligations. An unlabeled criterion is not a defect in the spec and is not reported as one.

**The gate is reported unenforced, and never as passed.** `/validate_plan` records `legacy-unenforced` (§7) and states the reason in the report: the spec carries no criterion labels, so the pairing gate had nothing to enforce. Silence is not allowed either — a report that omits the gate reads as a gate that found nothing wrong. No criterion-level pass, no tick, no "no gate issues", and no overall `success` resting on the gate's approval.

**Upgrading is an insertion, not a rewrite.** Re-invoking `/spec` on a legacy spec assigns identifiers and modes by §1 in the order the criteria already appear. Each criterion's own sentence is preserved exactly; the only lines the upgrade may add are the identifier heading, the mode line, and — for `manual-only` — the four labeled elements. Any diff that changes a criterion's wording is a failed upgrade, however small the improvement looks: the old text is what people agreed to. The assignments are listed for a human to review before the upgraded spec is saved, and the manual-only approval of §1 applies as it does to any other spec. The upgrade binds nothing — test groups arrive later, from `/create_plan`.
