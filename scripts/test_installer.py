#!/usr/bin/env python3
"""
test_installer.py — Behavioral test groups for setup.sh.

scripts/validate.py checks that the framework's *files* are consistent. This
script checks what the *installer does*: what it writes into a target project,
what it records about the install, what it refuses, and what it leaves alone.

Every check is a named entry in CHECKS and is individually runnable, so a single
acceptance criterion binds to exactly one of them (see
conventions/criterion-binding.md).

Hermetic by construction: every group builds its own source repository, target
directory, and fetch cache under one temporary root, and removes it afterwards.
Sources are local `file://` git remotes, so no group touches the network.

Requires: python3 + PyYAML + git (same prerequisites as setup.sh — no new deps).

Exit codes: 0 = all clear, 1 = one or more failures.
Usage:
  python3 scripts/test_installer.py                 # every group
  python3 scripts/test_installer.py --list-checks   # names, one per line
  python3 scripts/test_installer.py --check <name>  # exactly one group
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
RECORD_NAME = ".project-specs.json"

# Directories never copied into a fixture source repo: either irrelevant to an
# install, or large enough to slow every group down.
SOURCE_SKIP = {
    ".git", ".venv", "venv", "node_modules", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "thoughts", "evals", "examples", "skills",
}

failures = []


def fail(group: str, msg: str) -> None:
    failures.append(f"  FAIL  {group}: {msg}")


# --- Fixture helpers ---------------------------------------------------------

def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run git in `repo` with identity and hooks forced to a known state, so a
    developer's global git config cannot change a group's outcome."""
    env = dict(os.environ)
    env.update({
        "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.invalid",
        "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
    })
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, env=env, check=check,
    )


def make_source(root: Path, name: str = "source") -> Path:
    """Copy the framework into a fresh git repo under `root` and commit it.

    The copy is the real tree minus SOURCE_SKIP, so groups exercise the actual
    installer against actual content rather than a hand-built stub.
    """
    src = root / name
    src.mkdir(parents=True)
    for entry in sorted(ROOT.iterdir()):
        if entry.name in SOURCE_SKIP:
            continue
        dest = src / entry.name
        if entry.is_dir():
            shutil.copytree(entry, dest, symlinks=True)
        else:
            shutil.copy2(entry, dest)
    git(src, "init", "-q", "-b", "main")
    git(src, "add", "-A")
    git(src, "commit", "-q", "-m", "initial")
    return src


def advance_source(src: Path, message: str, edits: "dict[str, str] | None" = None) -> str:
    """Commit a change on top of `src` and return the new revision."""
    edits = edits or {"conventions/naming-conventions.md": "\n<!-- upstream change -->\n"}
    for rel, addition in edits.items():
        path = src / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(addition)
    git(src, "add", "-A")
    git(src, "commit", "-q", "-m", message)
    return git(src, "rev-parse", "HEAD").stdout.strip()


def run_setup(src: Path, target: Path, *extra: str,
              cache: "Path | None" = None) -> subprocess.CompletedProcess:
    """Invoke the installer under test. Always non-interactive."""
    env = dict(os.environ)
    if cache is not None:
        env["SPECS_CACHE"] = str(cache)
    return subprocess.run(
        ["bash", str(src / "setup.sh"), str(target), "--yes", *extra],
        capture_output=True, text=True, env=env,
    )


@contextmanager
def sandbox():
    """One temporary root holding the source repo, the target, and the cache."""
    tmp = Path(tempfile.mkdtemp(prefix="specs-installer-test-"))
    try:
        target = tmp / "target"
        target.mkdir()
        cache = tmp / "cache"
        yield tmp, target, cache
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def read_record(target: Path):
    path = target / RECORD_NAME
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(target: Path) -> "dict[str, str]":
    """Content fingerprint of every regular file under `target`, for
    before/after comparison. Symlinks are recorded by their destination."""
    out = {}
    for p in sorted(target.rglob("*")):
        rel = str(p.relative_to(target))
        if p.is_symlink():
            out[rel] = "link:" + os.readlink(p)
        elif p.is_file():
            out[rel] = digest(p)
    return out


# --- Groups: install record --------------------------------------------------

def check_fresh_install_writes_record() -> None:
    """AC-1 — a fresh install writes an install record naming the record format
    version, the source, the reference, the revision, the provider, the mode,
    and the install time."""
    g = "check_fresh_install_writes_record"
    with sandbox() as (tmp, target, cache):
        src = make_source(tmp)
        head = git(src, "rev-parse", "HEAD").stdout.strip()
        proc = run_setup(src, target, "--copy", cache=cache)
        if proc.returncode != 0:
            fail(g, f"installer exited {proc.returncode}: {proc.stderr.strip()[:400]}")
            return
        rec = read_record(target)
        if rec is None:
            fail(g, f"no {RECORD_NAME} written into the target project")
            return
        for field in ("schema", "source", "ref", "commit", "provider", "mode",
                      "installed_at", "files"):
            if field not in rec:
                fail(g, f"record is missing required field: {field}")
        if rec.get("schema") != 1:
            fail(g, f"record schema is {rec.get('schema')!r}, expected 1")
        if rec.get("provider") != "claude":
            fail(g, f"record provider is {rec.get('provider')!r}, expected 'claude'")
        if rec.get("mode") != "copy":
            fail(g, f"record mode is {rec.get('mode')!r}, expected 'copy'")
        if rec.get("commit") != head:
            fail(g, f"record commit {rec.get('commit')!r} != source HEAD {head!r}")
        stamp = str(rec.get("installed_at", ""))
        if not stamp.endswith("Z") or "T" not in stamp:
            fail(g, f"installed_at {stamp!r} is not a UTC ISO-8601 timestamp")


def check_record_hashes_match_disk() -> None:
    """AC-2 — the record carries a content fingerprint for every file the
    installer wrote, and each one matches the file on disk."""
    g = "check_record_hashes_match_disk"
    with sandbox() as (tmp, target, cache):
        src = make_source(tmp)
        proc = run_setup(src, target, "--copy", cache=cache)
        if proc.returncode != 0:
            fail(g, f"installer exited {proc.returncode}: {proc.stderr.strip()[:400]}")
            return
        rec = read_record(target)
        if rec is None:
            fail(g, f"no {RECORD_NAME} written into the target project")
            return
        files = rec.get("files")
        if not isinstance(files, dict) or not files:
            fail(g, "record 'files' is missing, not a mapping, or empty")
            return
        # Every file the installer is known to write must be represented.
        expected = [
            ".claude/commands/core/create_plan.md",
            ".claude/agents/codebase-locator.md",
            ".claude/conventions/criterion-binding.md",
            "standards/statements.json",
            "specs.config.yaml",
            "pr_description.md",
        ]
        for rel in expected:
            if rel not in files:
                fail(g, f"record 'files' has no entry for {rel}")
        for rel, recorded in sorted(files.items()):
            path = target / rel
            if not path.exists():
                fail(g, f"record lists {rel} but it is not on disk")
                continue
            if path.is_symlink():
                continue  # a symlink has no content of its own to fingerprint
            actual = digest(path)
            if actual != recorded:
                fail(g, f"{rel}: recorded {recorded[:20]}… != on-disk {actual[:20]}…")
                return  # one example is enough; don't bury the report


def check_future_schema_refused() -> None:
    """AC-3 — an installer meeting a record written by a newer installer changes
    nothing, fails, and says so."""
    g = "check_future_schema_refused"
    with sandbox() as (tmp, target, cache):
        src = make_source(tmp)
        first = run_setup(src, target, "--copy", cache=cache)
        if first.returncode != 0:
            fail(g, f"initial install exited {first.returncode}: {first.stderr.strip()[:400]}")
            return
        rec_path = target / RECORD_NAME
        if not rec_path.exists():
            fail(g, f"initial install wrote no {RECORD_NAME}; cannot test the refusal")
            return
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        rec["schema"] = 99
        rec_path.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        before = snapshot(target)
        proc = run_setup(src, target, "--update", cache=cache)
        after = snapshot(target)

        if proc.returncode == 0:
            fail(g, "installer accepted a record with schema 99 (exited 0)")
        combined = (proc.stdout + proc.stderr).lower()
        if "newer" not in combined:
            fail(g, "failure message never says the record came from a newer installer: "
                    f"{(proc.stdout + proc.stderr).strip()[:300]!r}")
        if before != after:
            changed = sorted(set(before) ^ set(after)) or [
                k for k in before if after.get(k) != before[k]
            ]
            fail(g, f"files changed despite the refusal: {changed[:5]}")


# --- Check registry ----------------------------------------------------------
# Keyed by the group name used in a plan's Criterion Bindings table, so
# `python3 scripts/test_installer.py --check <name>` runs exactly one bound group.

CHECKS: "dict[str, Callable[[], None]]" = {
    "check_fresh_install_writes_record": check_fresh_install_writes_record,
    "check_record_hashes_match_disk":    check_record_hashes_match_disk,
    "check_future_schema_refused":       check_future_schema_refused,
}


def _report(single) -> None:
    if failures:
        label = f"[{single}]" if single else ""
        print(f"\ntest_installer.py {label}: {len(failures)} failure(s)\n")
        print("\n".join(failures))
    else:
        if single:
            print(f"test_installer.py [{single}]: OK")
        else:
            print(f"test_installer.py: OK — {len(CHECKS)} group(s)")
    sys.exit(1 if failures else 0)


def main() -> None:
    if "--list-checks" in sys.argv:
        for name in CHECKS:
            print(name)
        sys.exit(0)

    if shutil.which("git") is None:
        print("ERROR: git is required to run installer tests")
        sys.exit(1)

    if "--check" in sys.argv:
        i = sys.argv.index("--check")
        if i + 1 >= len(sys.argv):
            print("ERROR: --check requires a group name — see --list-checks")
            sys.exit(1)
        name = sys.argv[i + 1]
        if name not in CHECKS:
            print(f"ERROR: unknown group '{name}' — see --list-checks")
            sys.exit(1)
        CHECKS[name]()
        _report(name)

    for fn in CHECKS.values():
        fn()
    _report(None)


if __name__ == "__main__":
    main()
