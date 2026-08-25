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
    """AC-10 — a file still matching its recorded fingerprint is replaced with
    the source's version, so protection does not freeze the whole install."""
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
    """AC-11 — a customized project configuration file survives an update."""
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
