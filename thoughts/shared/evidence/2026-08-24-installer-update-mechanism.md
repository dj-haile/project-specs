---
date: 2026-08-24
branch: feature/installer-update-mechanism
status: in-progress
tags:
  - installer
  - evidence
---

# Evidence — Installer Update Mechanism

Red and green records for every automated criterion in
`thoughts/shared/specs/2026-08-24-installer-update-mechanism-spec.md`, bound by
`thoughts/shared/plans/2026-08-24-installer-update-mechanism-plan.md`.

Invocation template from `specs.config.yaml`: `python3 {file} --check {name}`, so every
record below is `strength: single-group` — the run executed exactly the bound group.

---

## Phase 1 — Install record

```yaml
criterion: AC-1
group: scripts/test_installer.py::check_fresh_install_writes_record
outcome: red
command: "python3 scripts/test_installer.py --check check_fresh_install_writes_record"
code_state: "git:03195aa0dc5ac4456824441c606f3d6cf0cddc83"
output: |
  exit 1
  
  test_installer.py [check_fresh_install_writes_record]: 1 failure(s)
  
    FAIL  check_fresh_install_writes_record: no .project-specs.json written into the target project
strength: single-group
```

```yaml
criterion: AC-2
group: scripts/test_installer.py::check_record_hashes_match_disk
outcome: red
command: "python3 scripts/test_installer.py --check check_record_hashes_match_disk"
code_state: "git:03195aa0dc5ac4456824441c606f3d6cf0cddc83"
output: |
  exit 1
  
  test_installer.py [check_record_hashes_match_disk]: 1 failure(s)
  
    FAIL  check_record_hashes_match_disk: no .project-specs.json written into the target project
strength: single-group
```

```yaml
criterion: AC-3
group: scripts/test_installer.py::check_future_schema_refused
outcome: red
command: "python3 scripts/test_installer.py --check check_future_schema_refused"
code_state: "git:03195aa0dc5ac4456824441c606f3d6cf0cddc83"
output: |
  exit 1
  
  test_installer.py [check_future_schema_refused]: 1 failure(s)
  
    FAIL  check_future_schema_refused: initial install wrote no .project-specs.json; cannot test the refusal
strength: single-group
```

```yaml
criterion: AC-1
group: scripts/test_installer.py::check_fresh_install_writes_record
outcome: green
command: "python3 scripts/test_installer.py --check check_fresh_install_writes_record"
code_state: "git:a87a0ce53d1d6b09bbbfa9fcf33e889065251102"
output: |
  exit 0
  test_installer.py [check_fresh_install_writes_record]: OK
strength: single-group
```

```yaml
criterion: AC-2
group: scripts/test_installer.py::check_record_hashes_match_disk
outcome: green
command: "python3 scripts/test_installer.py --check check_record_hashes_match_disk"
code_state: "git:a87a0ce53d1d6b09bbbfa9fcf33e889065251102"
output: |
  exit 0
  test_installer.py [check_record_hashes_match_disk]: OK
strength: single-group
```

```yaml
criterion: AC-3
group: scripts/test_installer.py::check_future_schema_refused
outcome: green
command: "python3 scripts/test_installer.py --check check_future_schema_refused"
code_state: "git:a87a0ce53d1d6b09bbbfa9fcf33e889065251102"
output: |
  exit 0
  test_installer.py [check_future_schema_refused]: OK
strength: single-group
```


## Phase 2 — Fetch and reference pinning

```yaml
criterion: AC-4
group: scripts/test_installer.py::check_install_from_url_without_clone
outcome: red
command: "python3 scripts/test_installer.py --check check_install_from_url_without_clone"
code_state: "git:877bf54c3ab78095b1569a411a8ce57f2ea10e07"
output: |
  exit 1
  
  test_installer.py [check_install_from_url_without_clone]: 1 failure(s)
  
    FAIL  check_install_from_url_without_clone: installer exited 1: ✗ Unknown flag: --from=file:///var/folders/zp/xp_qs4s54417fqk1jlr2dbfc0000gn/T/specs-installer-test-5817jhti/source
strength: single-group
```

```yaml
criterion: AC-16
group: scripts/test_installer.py::check_install_named_reference
outcome: red
command: "python3 scripts/test_installer.py --check check_install_named_reference"
code_state: "git:877bf54c3ab78095b1569a411a8ce57f2ea10e07"
output: |
  exit 1
  
  test_installer.py [check_install_named_reference]: 1 failure(s)
  
    FAIL  check_install_named_reference: tag install exited 1: ✗ Unknown flag: --from=file:///var/folders/zp/xp_qs4s54417fqk1jlr2dbfc0000gn/T/specs-installer-test-wu0jfa5o/source
strength: single-group
```

```yaml
criterion: AC-4
group: scripts/test_installer.py::check_install_from_url_without_clone
outcome: green
command: "python3 scripts/test_installer.py --check check_install_from_url_without_clone"
code_state: "git:1246a372099c09cd39f19693e04182eb49099253"
output: |
  exit 0
  test_installer.py [check_install_from_url_without_clone]: OK
strength: single-group
```

```yaml
criterion: AC-16
group: scripts/test_installer.py::check_install_named_reference
outcome: green
command: "python3 scripts/test_installer.py --check check_install_named_reference"
code_state: "git:1246a372099c09cd39f19693e04182eb49099253"
output: |
  exit 0
  test_installer.py [check_install_named_reference]: OK
strength: single-group
```


## Phase 3 — Update that fetches, and holds a pin

```yaml
criterion: AC-5
group: scripts/test_installer.py::check_update_fetches_new_revision
outcome: red
command: "python3 scripts/test_installer.py --check check_update_fetches_new_revision"
code_state: "git:512c08793c802435ab7a3d4853540302581f7de2"
output: |
  exit 1
  
  test_installer.py [check_update_fetches_new_revision]: 1 failure(s)
  
    FAIL  check_update_fetches_new_revision: update exited 1: ✗ Unknown provider: claude
  Available providers:
strength: single-group
```

```yaml
criterion: AC-6
group: scripts/test_installer.py::check_update_without_source_argument
outcome: red
command: "python3 scripts/test_installer.py --check check_update_without_source_argument"
code_state: "git:512c08793c802435ab7a3d4853540302581f7de2"
output: |
  exit 1
  
  test_installer.py [check_update_without_source_argument]: 1 failure(s)
  
    FAIL  check_update_without_source_argument: update with no --from exited 1: ✗ Unknown provider: claude
  Available providers:
strength: single-group
```

```yaml
criterion: AC-7
group: scripts/test_installer.py::check_repeat_update_is_stable
outcome: red
command: "python3 scripts/test_installer.py --check check_repeat_update_is_stable"
code_state: "git:512c08793c802435ab7a3d4853540302581f7de2"
output: |
  exit 1
  
  test_installer.py [check_repeat_update_is_stable]: 1 failure(s)
  
    FAIL  check_repeat_update_is_stable: first update failed
strength: single-group
```

```yaml
criterion: AC-8
group: scripts/test_installer.py::check_failed_fetch_leaves_install_intact
outcome: red
command: "python3 scripts/test_installer.py --check check_failed_fetch_leaves_install_intact"
code_state: "git:512c08793c802435ab7a3d4853540302581f7de2"
output: |
  exit 1
  
  test_installer.py [check_failed_fetch_leaves_install_intact]: 1 failure(s)
  
    FAIL  check_failed_fetch_leaves_install_intact: failure never names the unreachable source: '\x1b[0;31m✗\x1b[0m Unknown provider: claude\nAvailable providers:'
strength: single-group
```

```yaml
criterion: AC-12
group: scripts/test_installer.py::check_update_without_record_warns
outcome: red
command: "python3 scripts/test_installer.py --check check_update_without_record_warns"
code_state: "git:512c08793c802435ab7a3d4853540302581f7de2"
output: |
  exit 1
  
  test_installer.py [check_update_without_record_warns]: 1 failure(s)
  
    FAIL  check_update_without_record_warns: update never says edited-file protection was unavailable: 'ar/folders/zp/xp_qs4s54417fqk1jlr2dbfc0000gn/T/specs-installer-test-e5c2uzxb/source/skills/_template/SKILL.md\n  • Provider portability: .claude/conventions/provider-portability.md\n  • PR template: /var/folders/zp/xp_qs4s54417fqk1jlr2dbfc0000gn/T/specs-installer-test-e5c2uzxb/target/pr_description.md'
strength: single-group
```

```yaml
criterion: AC-17
group: scripts/test_installer.py::check_update_keeps_pin
outcome: red
command: "python3 scripts/test_installer.py --check check_update_keeps_pin"
code_state: "git:512c08793c802435ab7a3d4853540302581f7de2"
output: |
  exit 1
  
  test_installer.py [check_update_keeps_pin]: 1 failure(s)
  
    FAIL  check_update_keeps_pin: update exited 1: ✗ Unknown provider: claude
  Available providers:
strength: single-group
```

```yaml
criterion: AC-18
group: scripts/test_installer.py::check_update_moves_pin
outcome: red
command: "python3 scripts/test_installer.py --check check_update_moves_pin"
code_state: "git:512c08793c802435ab7a3d4853540302581f7de2"
output: |
  exit 1
  
  test_installer.py [check_update_moves_pin]: 1 failure(s)
  
    FAIL  check_update_moves_pin: update exited 1: ✗ Unknown provider: claude
  Available providers:
strength: single-group
```

```yaml
criterion: AC-5
group: scripts/test_installer.py::check_update_fetches_new_revision
outcome: green
command: "python3 scripts/test_installer.py --check check_update_fetches_new_revision"
code_state: "git:2f45a71226fc8727da9ec5ee5027393f2aa7a721"
output: |
  exit 0
  test_installer.py [check_update_fetches_new_revision]: OK
strength: single-group
```

```yaml
criterion: AC-6
group: scripts/test_installer.py::check_update_without_source_argument
outcome: green
command: "python3 scripts/test_installer.py --check check_update_without_source_argument"
code_state: "git:2f45a71226fc8727da9ec5ee5027393f2aa7a721"
output: |
  exit 0
  test_installer.py [check_update_without_source_argument]: OK
strength: single-group
```

```yaml
criterion: AC-7
group: scripts/test_installer.py::check_repeat_update_is_stable
outcome: green
command: "python3 scripts/test_installer.py --check check_repeat_update_is_stable"
code_state: "git:2f45a71226fc8727da9ec5ee5027393f2aa7a721"
output: |
  exit 0
  test_installer.py [check_repeat_update_is_stable]: OK
strength: single-group
```

```yaml
criterion: AC-8
group: scripts/test_installer.py::check_failed_fetch_leaves_install_intact
outcome: green
command: "python3 scripts/test_installer.py --check check_failed_fetch_leaves_install_intact"
code_state: "git:2f45a71226fc8727da9ec5ee5027393f2aa7a721"
output: |
  exit 0
  test_installer.py [check_failed_fetch_leaves_install_intact]: OK
strength: single-group
```

```yaml
criterion: AC-12
group: scripts/test_installer.py::check_update_without_record_warns
outcome: green
command: "python3 scripts/test_installer.py --check check_update_without_record_warns"
code_state: "git:2f45a71226fc8727da9ec5ee5027393f2aa7a721"
output: |
  exit 0
  test_installer.py [check_update_without_record_warns]: OK
strength: single-group
```

```yaml
criterion: AC-17
group: scripts/test_installer.py::check_update_keeps_pin
outcome: green
command: "python3 scripts/test_installer.py --check check_update_keeps_pin"
code_state: "git:2f45a71226fc8727da9ec5ee5027393f2aa7a721"
output: |
  exit 0
  test_installer.py [check_update_keeps_pin]: OK
strength: single-group
```

```yaml
criterion: AC-18
group: scripts/test_installer.py::check_update_moves_pin
outcome: green
command: "python3 scripts/test_installer.py --check check_update_moves_pin"
code_state: "git:2f45a71226fc8727da9ec5ee5027393f2aa7a721"
output: |
  exit 0
  test_installer.py [check_update_moves_pin]: OK
strength: single-group
```

