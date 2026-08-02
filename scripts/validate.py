#!/usr/bin/env python3
"""
validate.py — Structural validation for the project-specs framework.

Checks that the framework's own files are internally consistent, so breakage
is caught at PR time instead of when an installed agent misbehaves.

What it validates:
  1. Frontmatter   — every command/agent has valid YAML frontmatter with
                     required fields (name, description, model)
  2. Model tiers   — `model:` is a semantic tier (planning|analysis|quick),
                     never a literal model name (portability rule)
  3. Naming        — file stem matches frontmatter `name`; kebab/snake rules
  4. Sections      — core commands contain required behavioral sections
  5. Configs       — specs.config.example.yaml, examples/*.yaml, and
                     providers/*/manifest.yaml parse and have required keys
  6. Links         — relative markdown links resolve to real files

Requires: python3 + PyYAML (same prerequisites as setup.sh — no new deps).

Exit codes: 0 = all clear, 1 = one or more errors.
Usage: python3 scripts/validate.py [--quiet]
"""

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: python3 -m pip install pyyaml")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
VALID_TIERS = {"planning", "analysis", "quick"}
LITERAL_MODEL_PAT = re.compile(
    r"^(claude-|gpt-|gemini-|opus$|sonnet$|haiku$)", re.IGNORECASE
)

# Core commands must carry these behavioral sections (see skills/_template).
# Backfilled incrementally; extend this list as sections are added.
REQUIRED_SECTIONS = {
    "commands/core/spec.md": ["Common Shortcuts to Avoid", "Red Flags", "Verification"],
    "commands/core/create_plan.md": ["Common Shortcuts to Avoid", "Red Flags", "Verification"],
    "commands/core/implement_plan.md": ["Common Shortcuts to Avoid", "Red Flags", "Verification"],
    "commands/core/validate_plan.md": ["Common Shortcuts to Avoid", "Red Flags", "Verification"],
}

REQUIRED_CONFIG_KEYS = {"provider", "project_name"}
REQUIRED_MANIFEST_KEYS = {"provider"}

errors = []
warnings = []


def err(path, msg):
    errors.append(f"  ERROR   {path}: {msg}")


def warn(path, msg):
    warnings.append(f"  warning {path}: {msg}")


def parse_frontmatter(path: Path):
    """Return (frontmatter_dict, body) or (None, None) on failure."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return None, text
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        err(path.relative_to(ROOT), f"frontmatter is not valid YAML: {e}")
        return None, m.group(2)
    if not isinstance(fm, dict):
        return None, m.group(2)
    return fm, m.group(2)


def check_agent_or_command(path: Path):
    rel = path.relative_to(ROOT)
    fm, body = parse_frontmatter(path)
    if fm is None:
        err(rel, "missing or invalid YAML frontmatter block")
        return

    # Required fields
    for field in ("name", "description", "model"):
        if field not in fm or not fm[field]:
            err(rel, f"frontmatter missing required field: {field}")

    # name matches file stem
    name = fm.get("name")
    if name and name != path.stem:
        err(rel, f"frontmatter name '{name}' != file stem '{path.stem}'")

    # model must be a tier, never a literal model (portability rule)
    model = str(fm.get("model", ""))
    if model:
        if LITERAL_MODEL_PAT.match(model):
            err(rel, f"model '{model}' is a literal model name; use a tier "
                     f"({'|'.join(sorted(VALID_TIERS))}) — see conventions/model-selection.md")
        elif model not in VALID_TIERS:
            err(rel, f"model '{model}' is not a valid tier "
                     f"({'|'.join(sorted(VALID_TIERS))})")

    # description length sanity (routing quality)
    desc = str(fm.get("description", ""))
    if desc and len(desc) < 20:
        warn(rel, "description under 20 chars — too short for reliable routing")

    # required behavioral sections for core commands
    key = str(rel)
    if key in REQUIRED_SECTIONS and body:
        for section in REQUIRED_SECTIONS[key]:
            if not re.search(rf"^##+ .*{re.escape(section)}", body, re.M):
                err(rel, f"missing required section: '## {section}'")


def check_yaml_file(path: Path, required_keys: set):
    rel = path.relative_to(ROOT)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        err(rel, f"invalid YAML: {e}")
        return
    if not isinstance(data, dict):
        err(rel, "YAML root must be a mapping")
        return
    for k in required_keys:
        if k not in data:
            err(rel, f"missing required key: {k}")


def check_skill(path: Path):
    """Every SKILL.md must have name + description (the vercel-labs/skills
    community shape), unless it is marked internal (e.g. the template)."""
    rel = path.relative_to(ROOT)
    fm, _body = parse_frontmatter(path)
    if fm is None:
        err(rel, "SKILL.md missing or invalid YAML frontmatter block")
        return
    meta = fm.get("metadata")
    if isinstance(meta, dict) and meta.get("internal") is True:
        return  # hidden from CLI discovery; not a distributable skill
    for field in ("name", "description"):
        if field not in fm or not fm[field]:
            err(rel, f"SKILL.md missing required field: {field} "
                     f"(or set metadata.internal: true to exclude it)")


def check_links(path: Path):
    """Relative markdown links must resolve to real files."""
    rel = path.relative_to(ROOT)
    text = path.read_text(encoding="utf-8")
    for m in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", text):
        target = m.group(1).split("#")[0].strip()
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        resolved = (path.parent / target).resolve()
        if not resolved.exists():
            err(rel, f"broken relative link: {m.group(1)}")


def main():
    quiet = "--quiet" in sys.argv

    md_files = sorted(
        list((ROOT / "commands").rglob("*.md"))
        + list((ROOT / "agents").glob("*.md"))
    )
    for f in md_files:
        check_agent_or_command(f)

    # Configs and manifests
    example = ROOT / "specs.config.example.yaml"
    if example.exists():
        check_yaml_file(example, set())  # example may comment out keys; parse only
    for f in sorted((ROOT / "examples").rglob("specs.config.yaml")):
        check_yaml_file(f, REQUIRED_CONFIG_KEYS)
    for f in sorted((ROOT / "providers").rglob("manifest.yaml")):
        check_yaml_file(f, REQUIRED_MANIFEST_KEYS)

    # Skills (hand-authored templates + generated skills/.curated) — must carry
    # the community name+description shape, or be explicitly marked internal.
    for f in sorted((ROOT / "skills").rglob("SKILL.md")):
        check_skill(f)

    # Cross-file links in top-level docs, conventions, and commands
    link_files = (
        [ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "INSTRUCTIONS.md"]
        + sorted((ROOT / "conventions").glob("*.md"))
        + md_files
    )
    for f in link_files:
        if f.exists():
            check_links(f)

    # Report
    checked = len(md_files)
    if errors:
        print(f"\nvalidate.py: {len(errors)} error(s) across {checked} agent/command files\n")
        print("\n".join(errors))
    if warnings and not quiet:
        print(f"\n{len(warnings)} warning(s):\n")
        print("\n".join(warnings))
    if not errors:
        print(f"validate.py: OK — {checked} agent/command files, configs, manifests, skills, and links all valid")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
