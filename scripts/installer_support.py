#!/usr/bin/env python3
"""
installer_support.py — the parts of setup.sh that shell does badly.

setup.sh keeps the flow: argument parsing, provider manifests, provider
branching, and output. This module owns the install record — reading it,
writing it, and hashing the files it describes.

Why here and not in the installer itself: SHA-256 and JSON in shell would mean
branching on `sha256sum` (Linux) versus `shasum -a 256` (macOS) and hand-rolling
JSON quoting. Python's hashlib and json behave identically on both, and setup.sh
already shells out to python3 to read provider manifests, so this adds no
dependency the installer did not already have.

Subcommands:
  write-record   --target DIR --source URL --ref REF --track BRANCH
                 --commit SHA --provider NAME --mode MODE [--pinned]
                 [--path REL ...]
                 Walk each --path under the target, fingerprint every regular
                 file, and write the record. Directories are walked; symlinks
                 are recorded without a fingerprint.

  read-record    --target DIR
                 Print the record as JSON. Exit 2 when there is no record.

  assert-schema  --target DIR
                 Exit 0 when the record is absent or readable by this version.
                 Exit 3 when it was written by a newer installer.

  record-field   --target DIR --field NAME
                 Print one top-level field, for shell to read. Booleans print
                 as true/false. Exit 2 when there is no record.

Exit codes: 0 = ok, 2 = no record, 3 = record from a newer installer,
1 = usage or I/O error.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = 1
RECORD_NAME = ".project-specs.json"

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NO_RECORD = 2
EXIT_FUTURE_SCHEMA = 3


def record_path(target: Path) -> Path:
    return target / RECORD_NAME


def file_hash(path: Path) -> str:
    """Content fingerprint of one file, as "sha256:<hex>"."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def read_record(target: Path):
    """The record as a dict, or None when the target has no record."""
    path = record_path(target)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"ERROR: {path} is not valid JSON: {e}")
    if not isinstance(data, dict):
        raise SystemExit(f"ERROR: {path} must contain a JSON object")
    return data


def assert_schema_supported(record) -> None:
    """Refuse a record this installer cannot safely rewrite.

    A newer installer may record fields this one would silently drop on the next
    write, so the safe move is to stop rather than downgrade the record.
    """
    if record is None:
        return
    schema = record.get("schema")
    if not isinstance(schema, int):
        raise SystemExit(
            f"ERROR: {RECORD_NAME} has no usable 'schema' field — refusing to act on it"
        )
    if schema > SCHEMA:
        print(
            f"ERROR: {RECORD_NAME} declares schema {schema}, but this installer "
            f"understands up to {SCHEMA}. The install was made by a newer "
            f"installer — update project-specs itself before running this one.",
            file=sys.stderr,
        )
        sys.exit(EXIT_FUTURE_SCHEMA)


def collect_files(target: Path, rel_paths) -> "dict[str, str]":
    """Fingerprint every regular file under each given path.

    `rel_paths` are relative to the target root and may be files or directories.
    A symlink is recorded with an empty fingerprint: its content belongs to the
    source, not the target, so there is nothing here to protect or compare.
    """
    files: "dict[str, str]" = {}
    for rel in rel_paths:
        rel = rel.strip().lstrip("/")
        if not rel:
            continue
        base = target / rel
        if base.is_symlink():
            files[rel] = ""
            continue
        if base.is_file():
            files[rel] = file_hash(base)
            continue
        if not base.is_dir():
            continue  # the installer skipped it (missing source, provider opt-out)
        for dirpath, dirnames, filenames in os.walk(base):
            here = Path(dirpath)
            # Record a symlinked directory itself and do not descend into it.
            kept = []
            for d in sorted(dirnames):
                sub = here / d
                if sub.is_symlink():
                    files[str(sub.relative_to(target))] = ""
                else:
                    kept.append(d)
            dirnames[:] = kept
            for name in sorted(filenames):
                p = here / name
                key = str(p.relative_to(target))
                files[key] = "" if p.is_symlink() else file_hash(p)
    return files


def write_record(target: Path, *, source: str, ref: str, track: str, commit: str,
                 provider: str, mode: str, pinned: bool,
                 files: "dict[str, str]") -> None:
    """Write the record. Keys are sorted so two records diff readably."""
    doc = {
        "schema": SCHEMA,
        "source": source,
        "ref": ref,
        "track": track,
        "commit": commit,
        "pinned": bool(pinned),
        "provider": provider,
        "mode": mode,
        "installed_at": datetime.now(timezone.utc)
                        .isoformat(timespec="seconds").replace("+00:00", "Z"),
        "files": files,
    }
    record_path(target).write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


# --- CLI ---------------------------------------------------------------------

def cmd_write_record(args) -> int:
    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"ERROR: target is not a directory: {target}", file=sys.stderr)
        return EXIT_ERROR
    files = collect_files(target, args.path or [])
    write_record(
        target, source=args.source, ref=args.ref, track=args.track,
        commit=args.commit, provider=args.provider, mode=args.mode,
        pinned=args.pinned, files=files,
    )
    print(len(files))
    return EXIT_OK


def cmd_read_record(args) -> int:
    rec = read_record(Path(args.target).resolve())
    if rec is None:
        return EXIT_NO_RECORD
    json.dump(rec, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return EXIT_OK


def cmd_record_field(args) -> int:
    rec = read_record(Path(args.target).resolve())
    if rec is None:
        return EXIT_NO_RECORD
    value = rec.get(args.field, "")
    if isinstance(value, bool):
        print("true" if value else "false")
    elif isinstance(value, (dict, list)):
        print(json.dumps(value, sort_keys=True))
    else:
        print(value)
    return EXIT_OK


def cmd_assert_schema(args) -> int:
    assert_schema_supported(read_record(Path(args.target).resolve()))
    return EXIT_OK


def main() -> int:
    parser = argparse.ArgumentParser(prog="installer_support.py", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("write-record")
    w.add_argument("--target", required=True)
    w.add_argument("--source", default="")
    w.add_argument("--ref", default="")
    w.add_argument("--track", default="")
    w.add_argument("--commit", default="")
    w.add_argument("--provider", required=True)
    w.add_argument("--mode", required=True)
    w.add_argument("--pinned", action="store_true")
    w.add_argument("--path", action="append", default=[])
    w.set_defaults(func=cmd_write_record)

    r = sub.add_parser("read-record")
    r.add_argument("--target", required=True)
    r.set_defaults(func=cmd_read_record)

    f = sub.add_parser("record-field")
    f.add_argument("--target", required=True)
    f.add_argument("--field", required=True)
    f.set_defaults(func=cmd_record_field)

    a = sub.add_parser("assert-schema")
    a.add_argument("--target", required=True)
    a.set_defaults(func=cmd_assert_schema)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
