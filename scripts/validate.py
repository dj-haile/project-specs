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
  7. Pairing gate  — the acceptance-criteria pairing gate's own structural
                     rules: the gate token reaches the behavioral sections,
                     its normative text lives in exactly one file, and the
                     core commands stay inside their line budget

Every check is a named entry in CHECKS and is individually runnable, so a
single acceptance criterion can be bound to exactly one of them.

Requires: python3 + PyYAML (same prerequisites as setup.sh — no new deps).

Exit codes: 0 = all clear, 1 = one or more errors.
Usage:
  python3 scripts/validate.py [--quiet]          # every check, registry order
  python3 scripts/validate.py --list-checks      # names, one per line
  python3 scripts/validate.py --check <name>     # exactly one check
"""

import re
import sys
from pathlib import Path
from typing import Callable

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

# --- Acceptance-criteria pairing gate (conventions/criterion-binding.md) ---
# The four core commands that carry the gate's obligations.
CORE_COMMANDS = (
    "commands/core/spec.md",
    "commands/core/create_plan.md",
    "commands/core/implement_plan.md",
    "commands/core/validate_plan.md",
)
GATE_TOKEN = "pairing gate"          # the gate's canonical marker
GATE_SECTIONS = ("Common Shortcuts to Avoid", "Red Flags", "Verification")
GATE_SOURCE = "conventions/criterion-binding.md"   # the single normative source
SIZE_BUDGET = {                      # measured as `wc -l`
    "commands/core/spec.md": 300,
    "commands/core/create_plan.md": 500,
    "commands/core/implement_plan.md": 300,
    "commands/core/validate_plan.md": 300,
}
DUP_MIN_WORDS = 25                   # verbatim-paragraph threshold

errors = []
warnings = []
_checked_files = 0                   # set by _run_agent_or_command, used in the report


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


def _section_body(text: str, section: str):
    """Return the body under the first heading whose text contains `section`,
    up to the next heading of the same or higher level. None if the heading is
    absent."""
    m = re.search(rf"^(#+) .*{re.escape(section)}.*$", text, re.M)
    if not m:
        return None
    level = len(m.group(1))
    rest = text[m.end():]
    nxt = re.search(rf"^#{{1,{level}}} ", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def _paragraphs(text: str):
    """Blank-line-separated blocks, stripped, non-empty."""
    for block in re.split(r"\n[ \t]*\n", text):
        block = block.strip()
        if block:
            yield block


def check_gate_sections() -> None:
    """For each of the four core commands, GATE_TOKEN must appear at least once
    inside each of GATE_SECTIONS. The behavioral sections are where an agent
    looks for the shortcut it must not take, so a gate the sections never name
    is a gate no agent reads."""
    for rel in CORE_COMMANDS:
        path = ROOT / rel
        if not path.exists():
            err(rel, "core command file is missing")
            continue
        text = path.read_text(encoding="utf-8")
        for section in GATE_SECTIONS:
            body = _section_body(text, section)
            if body is None:
                err(rel, f"missing required section: '{section}' — nowhere to carry "
                         f"the '{GATE_TOKEN}' obligation")
            elif GATE_TOKEN not in body.lower():
                err(rel, f"section '{section}' never mentions the '{GATE_TOKEN}' "
                         f"obligation — see {GATE_SOURCE}")


def check_gate_single_source() -> None:
    """GATE_SOURCE must exist; each core command must carry a resolvable
    relative link to it; and no gate-defining paragraph of >= DUP_MIN_WORDS
    words may appear byte-identically in more than one file of
    {commands/core/*.md} U {GATE_SOURCE}. One rule, one home, linked from
    everywhere else.

    "Gate-defining" is scoped to paragraphs containing GATE_TOKEN. Unrelated
    boilerplate already shared between commands predates this rule and is not
    what the single-source rule is about; scoping keeps the check on the
    normative text it exists to police."""
    src = ROOT / GATE_SOURCE
    if not src.exists():
        err(GATE_SOURCE, "the pairing gate's single normative source does not exist")
    else:
        resolved_src = src.resolve()
        for rel in CORE_COMMANDS:
            path = ROOT / rel
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            linked = False
            for m in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", text):
                target = m.group(1).split("#")[0].strip()
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                if (path.parent / target).resolve() == resolved_src:
                    linked = True
                    break
            if not linked:
                err(rel, f"no resolvable relative link to {GATE_SOURCE} — the gate's "
                         f"rules must be referenced, never restated")

    dup_files = sorted((ROOT / "commands" / "core").glob("*.md"))
    if src.exists():
        dup_files.append(src)
    seen = {}
    for f in dup_files:
        rel = str(f.relative_to(ROOT))
        for para in _paragraphs(f.read_text(encoding="utf-8")):
            if GATE_TOKEN not in para.lower():
                continue
            if len(para.split()) < DUP_MIN_WORDS:
                continue
            seen.setdefault(para, set()).add(rel)
    for para, locs in seen.items():
        if len(locs) > 1:
            head = para.split("\n")[0][:60]
            where = ", ".join(sorted(locs))
            err(sorted(locs)[0], f"paragraph of >= {DUP_MIN_WORDS} words repeated "
                                 f"verbatim in {where}: '{head}…'")


def check_command_size_budget() -> None:
    """Every path in SIZE_BUDGET must stay at or under its line ceiling,
    measured the way `wc -l` measures it (newline count)."""
    for rel, budget in SIZE_BUDGET.items():
        path = ROOT / rel
        if not path.exists():
            err(rel, "file carries a size budget but does not exist")
            continue
        lines = path.read_text(encoding="utf-8").count("\n")
        if lines > budget:
            err(rel, f"{lines} lines exceeds the {budget}-line ceiling — extract "
                     f"body text to a convention or reference file "
                     f"(conventions/three-layer-architecture.md:182-185)")


# --- Check registry ---------------------------------------------------------
# Keyed by the group name used in a plan's Criterion Bindings table, so
# `python3 scripts/validate.py --check <name>` runs exactly one bound group.

def _md_files():
    return sorted(
        list((ROOT / "commands").rglob("*.md"))
        + list((ROOT / "agents").glob("*.md"))
    )


def _run_agent_or_command() -> None:
    global _checked_files
    files = _md_files()
    _checked_files = len(files)
    for f in files:
        check_agent_or_command(f)


def _run_yaml_configs() -> None:
    example = ROOT / "specs.config.example.yaml"
    if example.exists():
        check_yaml_file(example, set())  # example may comment out keys; parse only
    for f in sorted((ROOT / "examples").rglob("specs.config.yaml")):
        check_yaml_file(f, REQUIRED_CONFIG_KEYS)
    for f in sorted((ROOT / "providers").rglob("manifest.yaml")):
        check_yaml_file(f, REQUIRED_MANIFEST_KEYS)


def _run_skills() -> None:
    # Hand-authored templates + generated skills/.curated — must carry the
    # community name+description shape, or be explicitly marked internal.
    for f in sorted((ROOT / "skills").rglob("SKILL.md")):
        check_skill(f)


def _run_links() -> None:
    # Cross-file links in top-level docs, conventions, and commands
    link_files = (
        [ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "INSTRUCTIONS.md"]
        + sorted((ROOT / "conventions").glob("*.md"))
        + _md_files()
    )
    for f in link_files:
        if f.exists():
            check_links(f)


CHECKS: "dict[str, Callable[[], None]]" = {
    "check_agent_or_command":    _run_agent_or_command,
    "check_yaml_configs":        _run_yaml_configs,
    "check_skills":              _run_skills,
    "check_links":               _run_links,
    "check_gate_sections":       check_gate_sections,
    "check_gate_single_source":  check_gate_single_source,
    "check_command_size_budget": check_command_size_budget,
}


def _report(single, quiet: bool) -> None:
    if errors:
        if single:
            print(f"\nvalidate.py [{single}]: {len(errors)} error(s)\n")
        else:
            print(f"\nvalidate.py: {len(errors)} error(s) across {_checked_files} agent/command files\n")
        print("\n".join(errors))
    if warnings and not quiet:
        print(f"\n{len(warnings)} warning(s):\n")
        print("\n".join(warnings))
    if not errors:
        if single:
            print(f"validate.py [{single}]: OK")
        else:
            print(f"validate.py: OK — {_checked_files} agent/command files, configs, manifests, skills, and links all valid")
    sys.exit(1 if errors else 0)


def main():
    quiet = "--quiet" in sys.argv

    if "--list-checks" in sys.argv:
        for name in CHECKS:
            print(name)
        sys.exit(0)

    if "--check" in sys.argv:
        i = sys.argv.index("--check")
        if i + 1 >= len(sys.argv):
            print("ERROR: --check requires a check name — see --list-checks")
            sys.exit(1)
        name = sys.argv[i + 1]
        if name not in CHECKS:
            print(f"ERROR: unknown check '{name}' — see --list-checks")
            sys.exit(1)
        CHECKS[name]()
        _report(name, quiet)

    for fn in CHECKS.values():
        fn()
    _report(None, quiet)


if __name__ == "__main__":
    main()
