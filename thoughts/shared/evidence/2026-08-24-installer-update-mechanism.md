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

## Slice 1 — Install record

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

