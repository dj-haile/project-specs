#!/usr/bin/env python3
"""
build_skills.py — Generate community-shape Skills from project-specs agents.

Makes project-specs installable via the vercel-labs/skills CLI
(`npx skills add dj-haile/project-specs`), which discovers a skill as a
directory containing a `SKILL.md` with `name` + `description` frontmatter.

Scope: **agents only** (`agents/*.md`). The agents are read-only, self-contained
research specialists with no dependency on `specs.config.yaml`, the three-layer
model, or the `conventions/` tree — so they work as standalone skills in an
arbitrary agent tool. Commands are framework-coupled and deliberately NOT
exported here (see thoughts/shared/decisions/2026-08-01-skills-cli-distribution.md).

Output: `skills/.curated/<name>/SKILL.md` — a documented CLI discovery location,
visibly generated and separate from hand-authored `skills/`.

Transforms applied per agent:
  - frontmatter reduced to `name` + `description` (the community shape); the
    original `model` tier and `tools` list are preserved under `metadata:` for
    provenance, alongside `metadata.source` (the source file) so drift is
    traceable.
  - any relative markdown link in the body is rewritten to an absolute
    GitHub `blob/main` URL, so cross-references still resolve once the skill is
    installed away from this repo.

The generated files are committed. CI regenerates and `git diff --exit-code`s
them, so an agent edit that isn't reflected in the skills fails the build.

Requires: python3 + PyYAML (same prerequisites as setup.sh — no new deps).
Usage: python3 scripts/build_skills.py
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
AGENTS_DIR = ROOT / "agents"
OUT_DIR = ROOT / "skills" / ".curated"
REPO_BLOB = "https://github.com/dj-haile/project-specs/blob/main"

LINK_PAT = re.compile(r"(\[[^\]]*\])\(([^)]+)\)")


def parse_frontmatter(path: Path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return None, text
    fm = yaml.safe_load(m.group(1))
    return (fm if isinstance(fm, dict) else None), m.group(2)


def rewrite_links(body: str, src_path: Path) -> str:
    """Rewrite relative markdown links to absolute GitHub blob URLs so they
    resolve after the skill is installed outside this repo."""
    def repl(m):
        label, target = m.group(1), m.group(2)
        anchor = ""
        if "#" in target:
            target, anchor = target.split("#", 1)
            anchor = "#" + anchor
        target = target.strip()
        if not target or "://" in target or target.startswith("mailto:"):
            return m.group(0)
        resolved = (src_path.parent / target).resolve()
        try:
            rel = resolved.relative_to(ROOT)
        except ValueError:
            return m.group(0)  # escapes the repo; leave untouched
        return f"{label}({REPO_BLOB}/{rel.as_posix()}{anchor})"

    return LINK_PAT.sub(repl, body)


def yaml_str(s: str) -> str:
    # Quote defensively; escape embedded double-quotes.
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def build():
    if not AGENTS_DIR.is_dir():
        print("ERROR: agents/ not found")
        sys.exit(1)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    written = []
    for src in sorted(AGENTS_DIR.glob("*.md")):
        fm, body = parse_frontmatter(src)
        if not fm or not fm.get("name") or not fm.get("description"):
            print(f"  skip {src.name}: missing name/description")
            continue
        name = fm["name"]
        desc = fm["description"]
        rel_src = src.relative_to(ROOT).as_posix()
        new_body = rewrite_links(body.lstrip("\n"), src)

        front_lines = [
            "---",
            f"name: {name}",
            f"description: {yaml_str(desc)}",
            "metadata:",
            f"  source: {rel_src}",
        ]
        if fm.get("model"):
            front_lines.append(f"  model_tier: {fm['model']}")
        if fm.get("tools"):
            tools = fm["tools"]
            tools_str = tools if isinstance(tools, str) else ", ".join(map(str, tools))
            front_lines.append(f"  tools: {yaml_str(tools_str)}")
        front_lines.append("---\n\n")
        front = "\n".join(front_lines)

        skill_dir = OUT_DIR / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(front + new_body, encoding="utf-8")
        written.append(name)

    print(f"build_skills.py: wrote {len(written)} skill(s) to "
          f"{OUT_DIR.relative_to(ROOT)}/: {', '.join(written)}")


if __name__ == "__main__":
    build()
