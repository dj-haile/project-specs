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


def make_bare_installer(root: Path, src: Path, name: str = "bare") -> Path:
    """A directory holding ONLY the installer and its support scripts.

    Nothing else from the framework is present, so an install run from here can
    only succeed if the content came from the fetched source — which is what
    "no pre-existing local clone" has to mean in a test.
    """
    bare = root / name
    (bare / "scripts").mkdir(parents=True)
    shutil.copy2(src / "setup.sh", bare / "setup.sh")
    for script in sorted((src / "scripts").glob("*.py")):
        shutil.copy2(script, bare / "scripts" / script.name)
    return bare


def file_url(path: Path) -> str:
    return "file://" + str(path)


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


# --- Groups: fetching from a source repository -------------------------------

def check_install_from_url_without_clone() -> None:
    """AC-4 — the installer installs from a source repository location with no
    pre-existing local clone, and records that location."""
    g = "check_install_from_url_without_clone"
    with sandbox() as (tmp, target, cache):
        src = make_source(tmp)
        head = git(src, "rev-parse", "HEAD").stdout.strip()
        bare = make_bare_installer(tmp, src)
        url = file_url(src)

        # Sanity: the bare installer really has no framework content of its own.
        if (bare / "commands").exists() or (bare / "conventions").exists():
            fail(g, "fixture is wrong: the bare installer carries framework content")
            return

        proc = run_setup(bare, target, f"--from={url}", "--copy", cache=cache)
        if proc.returncode != 0:
            fail(g, f"installer exited {proc.returncode}: "
                    f"{(proc.stdout + proc.stderr).strip()[-500:]}")
            return
        for rel in (".claude/commands/core/create_plan.md",
                    ".claude/conventions/criterion-binding.md",
                    "standards/statements.json"):
            if not (target / rel).exists():
                fail(g, f"{rel} was not installed — content did not come from the fetch")
        rec = read_record(target)
        if rec is None:
            fail(g, f"no {RECORD_NAME} written")
            return
        if rec.get("source") != url:
            fail(g, f"record source is {rec.get('source')!r}, expected {url!r}")
        if rec.get("commit") != head:
            fail(g, f"record commit {rec.get('commit')!r} != source HEAD {head!r}")


def check_install_named_reference() -> None:
    """AC-16 — a developer can install a named reference; the record states both
    the reference asked for and the revision it resolved to."""
    g = "check_install_named_reference"
    with sandbox() as (tmp, target, cache):
        src = make_source(tmp)
        pinned_rev = git(src, "rev-parse", "HEAD").stdout.strip()
        git(src, "tag", "v-test")
        marker = "\n<!-- only on main -->\n"
        main_rev = advance_source(
            src, "advance main",
            {"conventions/naming-conventions.md": marker},
        )
        if pinned_rev == main_rev:
            fail(g, "fixture is wrong: main did not advance past the tag")
            return
        bare = make_bare_installer(tmp, src)
        url = file_url(src)

        proc = run_setup(bare, target, f"--from={url}", "--ref=v-test", "--copy",
                         cache=cache)
        if proc.returncode != 0:
            fail(g, f"tag install exited {proc.returncode}: "
                    f"{(proc.stdout + proc.stderr).strip()[-500:]}")
            return
        rec = read_record(target)
        if rec is None:
            fail(g, f"no {RECORD_NAME} written")
            return
        if rec.get("ref") != "v-test":
            fail(g, f"record ref is {rec.get('ref')!r}, expected 'v-test'")
        if rec.get("commit") != pinned_rev:
            fail(g, f"record commit {rec.get('commit')!r} != the tag's revision "
                    f"{pinned_rev!r}")
        if rec.get("pinned") is not True:
            fail(g, f"record pinned is {rec.get('pinned')!r}; a tag is not a branch, "
                    f"so the install is pinned")
        installed = (target / ".claude/conventions/naming-conventions.md").read_text(
            encoding="utf-8")
        if "only on main" in installed:
            fail(g, "installed content carries a change made after the tag — the "
                    "reference was not honoured")

        # A branch name is not a pin, and resolves to that branch's head.
        target2 = tmp / "target-branch"
        target2.mkdir()
        proc2 = run_setup(bare, target2, f"--from={url}", "--ref=main", "--copy",
                          cache=cache)
        if proc2.returncode != 0:
            fail(g, f"branch install exited {proc2.returncode}: "
                    f"{(proc2.stdout + proc2.stderr).strip()[-500:]}")
            return
        rec2 = read_record(target2)
        if rec2 is None:
            fail(g, f"no {RECORD_NAME} written for the branch install")
            return
        if rec2.get("ref") != "main":
            fail(g, f"branch install ref is {rec2.get('ref')!r}, expected 'main'")
        if rec2.get("commit") != main_rev:
            fail(g, f"branch install commit {rec2.get('commit')!r} != main head "
                    f"{main_rev!r}")
        if rec2.get("pinned") is not False:
            fail(g, f"branch install pinned is {rec2.get('pinned')!r}; a branch is "
                    f"not a pin")


# --- Groups: updating ---------------------------------------------------------

def _install_then_advance(tmp, target, cache, ref=None):
    """Install from a file:// source, then move the source forward one commit.

    Returns (src, bare, url, first_rev, second_rev, marker).
    """
    src = make_source(tmp)
    first = git(src, "rev-parse", "HEAD").stdout.strip()
    git(src, "tag", "v-test")
    bare = make_bare_installer(tmp, src)
    url = file_url(src)
    args = [f"--from={url}", "--copy"]
    if ref:
        args.append(f"--ref={ref}")
    proc = run_setup(bare, target, *args, cache=cache)
    if proc.returncode != 0:
        return None, None, None, None, None, (proc.stdout + proc.stderr)
    marker = "\n<!-- landed after the install -->\n"
    second = advance_source(src, "upstream change",
                            {"conventions/naming-conventions.md": marker})
    return src, bare, url, first, second, None


def check_update_fetches_new_revision() -> None:
    """AC-5 — an update fetches the source before copying, so the installed
    files match the source's current revision, not a stale local copy."""
    g = "check_update_fetches_new_revision"
    with sandbox() as (tmp, target, cache):
        src, bare, url, first, second, err = _install_then_advance(tmp, target, cache)
        if err:
            fail(g, f"setup failed: {err.strip()[-400:]}")
            return
        # No --from: an update that does not fetch on its own would copy whatever
        # sits beside the installer, which here is nothing at all.
        proc = run_setup(bare, target, "--update", cache=cache)
        if proc.returncode != 0:
            fail(g, f"update exited {proc.returncode}: "
                    f"{(proc.stdout + proc.stderr).strip()[-500:]}")
            return
        rec = read_record(target)
        if rec is None or rec.get("commit") != second:
            fail(g, f"record commit is {rec and rec.get('commit')!r}, expected the "
                    f"advanced revision {second!r}")
        installed = (target / ".claude/conventions/naming-conventions.md").read_text(
            encoding="utf-8")
        if "landed after the install" not in installed:
            fail(g, "installed file does not carry the upstream change — the update "
                    "did not fetch before copying")


def check_update_without_source_argument() -> None:
    """AC-6 — an update run from inside the target with no source given uses the
    source recorded at install time."""
    g = "check_update_without_source_argument"
    with sandbox() as (tmp, target, cache):
        src, bare, url, first, second, err = _install_then_advance(tmp, target, cache)
        if err:
            fail(g, f"setup failed: {err.strip()[-400:]}")
            return
        proc = run_setup(bare, target, "--update", cache=cache)   # no --from
        if proc.returncode != 0:
            fail(g, f"update with no --from exited {proc.returncode}: "
                    f"{(proc.stdout + proc.stderr).strip()[-500:]}")
            return
        rec = read_record(target)
        if rec is None or rec.get("commit") != second:
            fail(g, f"record commit is {rec and rec.get('commit')!r}, expected "
                    f"{second!r} — the recorded source was not used")
        if rec and rec.get("source") != url:
            fail(g, f"record source changed to {rec.get('source')!r}, expected {url!r}")


def check_repeat_update_is_stable() -> None:
    """AC-7 — running the same update twice changes nothing the second time,
    apart from the recorded install time."""
    g = "check_repeat_update_is_stable"
    with sandbox() as (tmp, target, cache):
        src, bare, url, first, second, err = _install_then_advance(tmp, target, cache)
        if err:
            fail(g, f"setup failed: {err.strip()[-400:]}")
            return
        if run_setup(bare, target, "--update", cache=cache).returncode != 0:
            fail(g, "first update failed")
            return
        before_files = snapshot(target)
        before_rec = read_record(target)
        proc = run_setup(bare, target, "--update", cache=cache)
        if proc.returncode != 0:
            fail(g, f"second update exited {proc.returncode}: "
                    f"{(proc.stdout + proc.stderr).strip()[-400:]}")
            return
        after_rec = read_record(target)
        after_files = snapshot(target)

        # The record itself is expected to differ only in its timestamp.
        for k in sorted(set(before_rec) | set(after_rec)):
            if k == "installed_at":
                continue
            if before_rec.get(k) != after_rec.get(k):
                fail(g, f"record field {k!r} changed across an identical update")
        changed = [k for k in sorted(set(before_files) | set(after_files))
                   if k != RECORD_NAME and before_files.get(k) != after_files.get(k)]
        if changed:
            fail(g, f"files changed across an identical update: {changed[:5]}")


def check_failed_fetch_leaves_install_intact() -> None:
    """AC-8 — when the source cannot be reached, every installed file and the
    record keep their previous content, and the failure names the source."""
    g = "check_failed_fetch_leaves_install_intact"
    with sandbox() as (tmp, target, cache):
        src, bare, url, first, second, err = _install_then_advance(tmp, target, cache)
        if err:
            fail(g, f"setup failed: {err.strip()[-400:]}")
            return
        before = snapshot(target)
        shutil.rmtree(src)                       # the source is now unreachable
        proc = run_setup(bare, target, "--update", cache=cache)
        after = snapshot(target)

        if proc.returncode == 0:
            fail(g, "update reported success against an unreachable source")
        combined = proc.stdout + proc.stderr
        if str(src) not in combined and url not in combined:
            fail(g, f"failure never names the unreachable source: "
                    f"{combined.strip()[-300:]!r}")
        changed = [k for k in sorted(set(before) | set(after))
                   if before.get(k) != after.get(k)]
        if changed:
            fail(g, f"install was modified despite the failed fetch: {changed[:5]}")


def check_update_without_record_warns() -> None:
    """AC-12 — an update against an install made before records existed
    completes, writes a record, and says protection was unavailable."""
    g = "check_update_without_record_warns"
    with sandbox() as (tmp, target, cache):
        src = make_source(tmp)
        if run_setup(src, target, "--copy", cache=cache).returncode != 0:
            fail(g, "initial install failed")
            return
        (target / RECORD_NAME).unlink()          # an install from before records
        proc = run_setup(src, target, "--update", cache=cache)
        if proc.returncode != 0:
            fail(g, f"update exited {proc.returncode}: "
                    f"{(proc.stdout + proc.stderr).strip()[-400:]}")
            return
        if read_record(target) is None:
            fail(g, f"update wrote no {RECORD_NAME}")
        combined = (proc.stdout + proc.stderr).lower()
        if "protection" not in combined:
            fail(g, "update never says edited-file protection was unavailable: "
                    f"{(proc.stdout + proc.stderr).strip()[-300:]!r}")


def check_update_keeps_pin() -> None:
    """AC-17 — an update on a pinned install stays on its pinned revision and
    reports the pin."""
    g = "check_update_keeps_pin"
    with sandbox() as (tmp, target, cache):
        src, bare, url, first, second, err = _install_then_advance(
            tmp, target, cache, ref="v-test")
        if err:
            fail(g, f"setup failed: {err.strip()[-400:]}")
            return
        proc = run_setup(bare, target, "--update", cache=cache)
        if proc.returncode != 0:
            fail(g, f"update exited {proc.returncode}: "
                    f"{(proc.stdout + proc.stderr).strip()[-500:]}")
            return
        rec = read_record(target)
        if rec is None:
            fail(g, "no record after update")
            return
        if rec.get("commit") != first:
            fail(g, f"pinned install moved: commit is {rec.get('commit')!r}, "
                    f"expected the pinned revision {first!r}")
        if rec.get("pinned") is not True:
            fail(g, f"record pinned is {rec.get('pinned')!r} after updating a pin")
        installed = (target / ".claude/conventions/naming-conventions.md").read_text(
            encoding="utf-8")
        if "landed after the install" in installed:
            fail(g, "pinned install picked up a change made after the pin")
        if "pinned" not in (proc.stdout + proc.stderr).lower():
            fail(g, "update never reports that the install is pinned")


def check_update_moves_pin() -> None:
    """AC-18 — naming a different reference on an update moves the install to
    it, and the record says so."""
    g = "check_update_moves_pin"
    with sandbox() as (tmp, target, cache):
        src, bare, url, first, second, err = _install_then_advance(
            tmp, target, cache, ref="v-test")
        if err:
            fail(g, f"setup failed: {err.strip()[-400:]}")
            return
        proc = run_setup(bare, target, "--update", "--ref=main", cache=cache)
        if proc.returncode != 0:
            fail(g, f"update exited {proc.returncode}: "
                    f"{(proc.stdout + proc.stderr).strip()[-500:]}")
            return
        rec = read_record(target)
        if rec is None:
            fail(g, "no record after update")
            return
        if rec.get("ref") != "main":
            fail(g, f"record ref is {rec.get('ref')!r}, expected 'main'")
        if rec.get("commit") != second:
            fail(g, f"record commit is {rec.get('commit')!r}, expected main head "
                    f"{second!r}")
        if rec.get("pinned") is not False:
            fail(g, f"record pinned is {rec.get('pinned')!r} after moving to a branch")
        installed = (target / ".claude/conventions/naming-conventions.md").read_text(
            encoding="utf-8")
        if "landed after the install" not in installed:
            fail(g, "install did not move to the named branch's content")


# --- Groups: protecting the developer's edits --------------------------------
#
# check_update_keeps_edited_file is bound to AC-9.
#
# The two groups after it are REGRESSION TESTS bound to no acceptance criterion.
# Both passed before any of this work existed — the installer already replaced
# every file wholesale, and already wrote specs.config.yaml only when absent — so
# neither can carry the failing-first evidence the pairing gate requires. They
# guard what the per-file copy engine must not break. Retired as criteria under
# D-4 in the spec; kept here because a rewritten copy engine is exactly the kind
# of change that quietly breaks them.

EDITED_MARK = "\n<!-- edited by the developer -->\n"


def check_update_keeps_edited_file() -> None:
    """AC-9 — a file whose content no longer matches its recorded fingerprint is
    left alone by an update, and the installer says it kept it."""
    g = "check_update_keeps_edited_file"
    with sandbox() as (tmp, target, cache):
        src, bare, url, first, second, err = _install_then_advance(tmp, target, cache)
        if err:
            fail(g, f"setup failed: {err.strip()[-400:]}")
            return
        # Two files the installer would otherwise replace on every run.
        edited = {
            "pr_description.md": None,
            ".claude/conventions/naming-conventions.md": None,
        }
        for rel in edited:
            path = target / rel
            with path.open("a", encoding="utf-8") as fh:
                fh.write(EDITED_MARK)
            edited[rel] = path.read_text(encoding="utf-8")

        # Twice: the first update must keep the edit, and must not adopt the
        # edited content as the new baseline, or the second update overwrites it.
        for attempt in (1, 2):
            proc = run_setup(bare, target, "--update", cache=cache)
            if proc.returncode != 0:
                fail(g, f"update {attempt} exited {proc.returncode}: "
                        f"{(proc.stdout + proc.stderr).strip()[-500:]}")
                return
            combined = proc.stdout + proc.stderr
            for rel, expected in edited.items():
                actual = (target / rel).read_text(encoding="utf-8")
                if actual != expected:
                    fail(g, f"{rel} was overwritten on update {attempt} despite "
                            f"being edited")
                if rel not in combined:
                    fail(g, f"update {attempt} never names {rel} as kept")


def check_update_replaces_untouched_file() -> None:
    """Regression guard (no criterion) — a file still matching its recorded
    fingerprint is replaced with the source's version, so protection does not
    freeze the whole install."""
    g = "check_update_replaces_untouched_file"
    with sandbox() as (tmp, target, cache):
        src, bare, url, first, second, err = _install_then_advance(tmp, target, cache)
        if err:
            fail(g, f"setup failed: {err.strip()[-400:]}")
            return
        rel = ".claude/conventions/naming-conventions.md"   # changed upstream, untouched here
        before = (target / rel).read_text(encoding="utf-8")
        if "landed after the install" in before:
            fail(g, "fixture is wrong: the upstream change is already installed")
            return

        proc = run_setup(bare, target, "--update", cache=cache)
        if proc.returncode != 0:
            fail(g, f"update exited {proc.returncode}: "
                    f"{(proc.stdout + proc.stderr).strip()[-500:]}")
            return
        after = (target / rel).read_text(encoding="utf-8")
        if "landed after the install" not in after:
            fail(g, f"{rel} was not updated even though it was never edited")
        rec = read_record(target)
        if rec and rec["files"].get(rel) != digest(target / rel):
            fail(g, f"record fingerprint for {rel} does not match the file it wrote")


def check_update_preserves_project_config() -> None:
    """Regression guard (no criterion) — a customized project configuration file
    survives an update."""
    g = "check_update_preserves_project_config"
    with sandbox() as (tmp, target, cache):
        src, bare, url, first, second, err = _install_then_advance(tmp, target, cache)
        if err:
            fail(g, f"setup failed: {err.strip()[-400:]}")
            return
        cfg = target / "specs.config.yaml"
        customized = cfg.read_text(encoding="utf-8") + '\nproject_name: "my-own-project"\n'
        cfg.write_text(customized, encoding="utf-8")

        proc = run_setup(bare, target, "--update", cache=cache)
        if proc.returncode != 0:
            fail(g, f"update exited {proc.returncode}: "
                    f"{(proc.stdout + proc.stderr).strip()[-500:]}")
            return
        if cfg.read_text(encoding="utf-8") != customized:
            fail(g, "specs.config.yaml was overwritten by the update")


# --- Groups: reporting staleness ---------------------------------------------

def check_staleness_reports_distance() -> None:
    """AC-13 — the report says the install is behind and by how many revisions."""
    g = "check_staleness_reports_distance"
    with sandbox() as (tmp, target, cache):
        src, bare, url, first, second, err = _install_then_advance(tmp, target, cache)
        if err:
            fail(g, f"setup failed: {err.strip()[-400:]}")
            return
        advance_source(src, "second upstream change",
                       {"conventions/model-selection.md": "\n<!-- second -->\n"})

        proc = run_setup(bare, target, "--check", cache=cache)
        combined = proc.stdout + proc.stderr
        low = combined.lower()
        if "behind" not in low:
            fail(g, f"report never says the install is behind: {combined.strip()[-300:]!r}")
        if "2" not in combined:
            fail(g, f"report never names the number of revisions behind (2): "
                    f"{combined.strip()[-300:]!r}")


def check_staleness_lists_changelog_entries() -> None:
    """AC-14 — the report lists the change-log entries added since the install."""
    g = "check_staleness_lists_changelog_entries"
    with sandbox() as (tmp, target, cache):
        src, bare, url, first, second, err = _install_then_advance(tmp, target, cache)
        if err:
            fail(g, f"setup failed: {err.strip()[-400:]}")
            return
        entry = "- Added a widget that reticulates splines"
        advance_source(src, "changelog entry", {"CHANGELOG.md": f"\n{entry}\n"})

        proc = run_setup(bare, target, "--check", cache=cache)
        combined = proc.stdout + proc.stderr
        if "reticulates splines" not in combined:
            fail(g, "report does not include the change-log entry added since the "
                    f"install: {combined.strip()[-400:]!r}")


def check_staleness_exit_status() -> None:
    """AC-15 — behind exits non-zero; current exits zero and says so."""
    g = "check_staleness_exit_status"
    with sandbox() as (tmp, target, cache):
        src, bare, url, first, second, err = _install_then_advance(tmp, target, cache)
        if err:
            fail(g, f"setup failed: {err.strip()[-400:]}")
            return
        behind = run_setup(bare, target, "--check", cache=cache)
        if behind.returncode == 0:
            fail(g, "check exited 0 on an install that is behind")

        # Bring it up to date, then the same check must pass.
        if run_setup(bare, target, "--update", cache=cache).returncode != 0:
            fail(g, "update failed, cannot test the current case")
            return
        current = run_setup(bare, target, "--check", cache=cache)
        if current.returncode != 0:
            fail(g, f"check exited {current.returncode} on an up-to-date install: "
                    f"{(current.stdout + current.stderr).strip()[-300:]}")
        if "current" not in (current.stdout + current.stderr).lower():
            fail(g, "check never says the install is current: "
                    f"{(current.stdout + current.stderr).strip()[-300:]!r}")


def check_staleness_reports_on_pinned_install() -> None:
    """AC-17b — a pinned install is told a newer revision exists, and the check
    changes no installed file."""
    g = "check_staleness_reports_on_pinned_install"
    with sandbox() as (tmp, target, cache):
        src, bare, url, first, second, err = _install_then_advance(
            tmp, target, cache, ref="v-test")
        if err:
            fail(g, f"setup failed: {err.strip()[-400:]}")
            return
        before = snapshot(target)
        proc = run_setup(bare, target, "--check", cache=cache)
        after = snapshot(target)
        combined = proc.stdout + proc.stderr
        low = combined.lower()

        if "pinned" not in low:
            fail(g, f"report never says the install is pinned: {combined.strip()[-300:]!r}")
        if second[:10] not in combined and "behind" not in low:
            fail(g, "report never names the newer revision available on the tracked "
                    f"branch: {combined.strip()[-300:]!r}")
        changed = [k for k in sorted(set(before) | set(after))
                   if before.get(k) != after.get(k)]
        if changed:
            fail(g, f"the check modified the install: {changed[:5]}")


# --- Groups: link mode, the command, and the documentation --------------------

def doc_section(text: str, pattern: str):
    """The body under the first heading matching `pattern`, up to the next
    heading. Lines inside fenced code blocks are never treated as headings —
    a shell or gitignore comment starts with '#' too."""
    import re
    lines = text.splitlines()
    start = None
    fenced = False
    heads = []
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        if re.match(r"^#{1,6} ", line):
            heads.append(i)
            if start is None and re.search(pattern, line, re.I):
                start = i
    if start is None:
        return None
    after = [i for i in heads if i > start]
    end = after[0] if after else len(lines)
    return "\n".join(lines[start + 1:end])


def check_link_mode_covers_conventions_and_standards() -> None:
    """AC-19 — in link mode the convention documents and the standards registry
    follow the source, so a change upstream is visible without reinstalling."""
    g = "check_link_mode_covers_conventions_and_standards"
    with sandbox() as (tmp, target, cache):
        src = make_source(tmp)
        proc = run_setup(src, target, "--link", cache=cache)
        if proc.returncode != 0:
            fail(g, f"link install exited {proc.returncode}: "
                    f"{(proc.stdout + proc.stderr).strip()[-500:]}")
            return

        marker = "<!-- changed in the source after installing -->"
        (src / "conventions/naming-conventions.md").write_text(
            "# naming\n" + marker + "\n", encoding="utf-8")
        (src / "standards/statements.json").write_text(
            '{"statements": [], "note": "' + marker + '"}\n', encoding="utf-8")

        for rel in (".claude/conventions/naming-conventions.md",
                    "standards/statements.json"):
            path = target / rel
            if not path.exists():
                fail(g, f"{rel} is not installed at all")
                continue
            if marker not in path.read_text(encoding="utf-8"):
                fail(g, f"{rel} does not follow the source — link mode copied it "
                        f"instead of linking it")


def check_link_mode_refused_for_transform_provider() -> None:
    """AC-20 — a provider whose install converts formats cannot be linked; the
    installer says so and completes by copying."""
    g = "check_link_mode_refused_for_transform_provider"
    with sandbox() as (tmp, target, cache):
        src = make_source(tmp)
        proc = run_setup(src, target, "--link", "--provider=codex", cache=cache)
        if proc.returncode != 0:
            fail(g, f"install exited {proc.returncode}: "
                    f"{(proc.stdout + proc.stderr).strip()[-500:]}")
            return
        combined = (proc.stdout + proc.stderr).lower()
        if "link" not in combined or ("not supported" not in combined
                                      and "unavailable" not in combined):
            fail(g, "installer never says link mode is unavailable for this "
                    f"provider: {(proc.stdout + proc.stderr).strip()[-300:]!r}")
        links = [p for p in target.rglob("*") if p.is_symlink()]
        if links:
            fail(g, f"install created symlinks despite needing a format "
                    f"conversion: {[str(p.relative_to(target)) for p in links][:5]}")
        if not (target / "AGENTS.md").exists():
            fail(g, "the codex install did not complete by copying")


def check_update_command_exists_and_parses() -> None:
    """AC-21 — a command exists whose stated purpose is checking for and
    applying framework updates, carrying the frontmatter every command needs."""
    g = "check_update_command_exists_and_parses"
    import re
    try:
        import yaml
    except ImportError:
        fail(g, "PyYAML is required")
        return
    candidates = sorted((ROOT / "commands").rglob("*.md"))
    found = None
    for path in candidates:
        m = re.match(r"^---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
        if not m:
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            continue
        desc = str(fm.get("description", "")).lower()
        says_change = any(w in desc for w in ("update", "upgrade", "out of date"))
        says_target = any(w in desc for w in ("framework", "install", "project-specs"))
        if says_change and says_target:
            found = (path, fm)
            break
    if not found:
        fail(g, "no command describes checking for or applying framework updates")
        return
    path, fm = found
    rel = path.relative_to(ROOT)
    for field in ("name", "description", "model"):
        if not fm.get(field):
            fail(g, f"{rel}: frontmatter missing {field}")
    if fm.get("name") != path.stem:
        fail(g, f"{rel}: frontmatter name {fm.get('name')!r} != file stem "
                f"{path.stem!r}")
    if fm.get("model") not in {"planning", "analysis", "quick"}:
        fail(g, f"{rel}: model {fm.get('model')!r} is not a semantic tier")
    if not re.fullmatch(r"[a-z0-9]+(_[a-z0-9]+)*", path.stem):
        fail(g, f"{rel}: command filenames must be snake_case")


def check_readme_documents_updating() -> None:
    """AC-22 — the main documentation explains how to update an existing
    install, naming the check, the update, and how to pin."""
    g = "check_readme_documents_updating"
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    section = doc_section(text, r"Updating an install")
    if section is None:
        fail(g, "README has no section on updating an existing install")
        return
    for token, why in (("--check", "the staleness check"),
                       ("--update", "the update"),
                       ("--ref", "pinning a reference")):
        if token not in section:
            fail(g, f"the updating section never names {token} ({why})")


def check_documented_ignore_list_includes_record() -> None:
    """AC-23 — the documented list of paths a project should keep out of git
    includes the install record."""
    g = "check_documented_ignore_list_includes_record"
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    section = doc_section(text, r"gitignore|keep .*out of git|ignore")
    if section is None:
        fail(g, "README documents no list of paths to keep out of git")
        return
    if RECORD_NAME not in section:
        fail(g, f"the documented ignore list does not include {RECORD_NAME}")


def check_link_mode_refused_with_fetched_source() -> None:
    """Regression guard (no criterion) — link mode against a fetched source would
    point every symlink at a temporary export that is deleted when the installer
    exits, leaving the project full of dangling links."""
    g = "check_link_mode_refused_with_fetched_source"
    with sandbox() as (tmp, target, cache):
        src = make_source(tmp)
        bare = make_bare_installer(tmp, src)
        proc = run_setup(bare, target, f"--from={file_url(src)}", "--link", cache=cache)
        dangling = [p for p in target.rglob("*")
                    if p.is_symlink() and not p.resolve().exists()]
        if dangling:
            fail(g, f"install left dangling symlinks: "
                    f"{[str(p.relative_to(target)) for p in dangling][:5]}")
        combined = (proc.stdout + proc.stderr).lower()
        if proc.returncode == 0 and "link" not in combined:
            fail(g, "installer neither refused link mode nor explained the fallback")


def check_update_keeps_files_the_installer_never_wrote() -> None:
    """Regression guard (no criterion) — an update must not delete or overwrite a
    file the developer put inside an installed directory. Found by the
    adversarial pass over the plan: the prune step removed anything absent from
    the source, and install_dir_plain wiped whole directories before the
    per-file sync could protect them."""
    g = "check_update_keeps_files_the_installer_never_wrote"
    with sandbox() as (tmp, target, cache):
        src, bare, url, first, second, err = _install_then_advance(tmp, target, cache)
        if err:
            fail(g, f"setup failed: {err.strip()[-400:]}")
            return
        own = target / ".claude/commands/core/my_own_command.md"
        own.write_text("---\nname: my_own_command\ndescription: local\n"
                       "model: quick\n---\nProject-local workflow.\n",
                       encoding="utf-8")
        own_before = own.read_text(encoding="utf-8")

        # An edit to an installed command, which lives under the same directory.
        edited = target / ".claude/commands/core/commit.md"
        edited.write_text(edited.read_text(encoding="utf-8") + EDITED_MARK,
                          encoding="utf-8")
        edited_before = edited.read_text(encoding="utf-8")

        for attempt in (1, 2):
            proc = run_setup(bare, target, "--update", cache=cache)
            if proc.returncode != 0:
                fail(g, f"update {attempt} exited {proc.returncode}: "
                        f"{(proc.stdout + proc.stderr).strip()[-400:]}")
                return
            if not own.exists():
                fail(g, f"update {attempt} deleted a file the developer added")
                return
            if own.read_text(encoding="utf-8") != own_before:
                fail(g, f"update {attempt} overwrote a file the developer added")
            if edited.read_text(encoding="utf-8") != edited_before:
                fail(g, f"update {attempt} overwrote an edited command — "
                        f"protection does not reach .claude/commands/")


# --- Check registry ----------------------------------------------------------
# Keyed by the group name used in a plan's Criterion Bindings table, so
# `python3 scripts/test_installer.py --check <name>` runs exactly one bound group.

CHECKS: "dict[str, Callable[[], None]]" = {
    "check_fresh_install_writes_record": check_fresh_install_writes_record,
    "check_record_hashes_match_disk":    check_record_hashes_match_disk,
    "check_future_schema_refused":       check_future_schema_refused,
    "check_install_from_url_without_clone": check_install_from_url_without_clone,
    "check_install_named_reference":     check_install_named_reference,
    "check_update_fetches_new_revision": check_update_fetches_new_revision,
    "check_update_without_source_argument": check_update_without_source_argument,
    "check_repeat_update_is_stable":     check_repeat_update_is_stable,
    "check_failed_fetch_leaves_install_intact": check_failed_fetch_leaves_install_intact,
    "check_update_without_record_warns": check_update_without_record_warns,
    "check_update_keeps_pin":            check_update_keeps_pin,
    "check_update_moves_pin":            check_update_moves_pin,
    "check_update_keeps_edited_file":    check_update_keeps_edited_file,
    "check_update_replaces_untouched_file": check_update_replaces_untouched_file,
    "check_update_preserves_project_config": check_update_preserves_project_config,
    "check_staleness_reports_distance":  check_staleness_reports_distance,
    "check_staleness_lists_changelog_entries": check_staleness_lists_changelog_entries,
    "check_staleness_exit_status":       check_staleness_exit_status,
    "check_staleness_reports_on_pinned_install": check_staleness_reports_on_pinned_install,
    "check_link_mode_covers_conventions_and_standards": check_link_mode_covers_conventions_and_standards,
    "check_link_mode_refused_for_transform_provider": check_link_mode_refused_for_transform_provider,
    "check_update_command_exists_and_parses": check_update_command_exists_and_parses,
    "check_readme_documents_updating":   check_readme_documents_updating,
    "check_documented_ignore_list_includes_record": check_documented_ignore_list_includes_record,
    "check_link_mode_refused_with_fetched_source": check_link_mode_refused_with_fetched_source,
    "check_update_keeps_files_the_installer_never_wrote": check_update_keeps_files_the_installer_never_wrote,
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
