#!/usr/bin/env python3
"""
extractor.py — Extract SHOULD/MUST statements from conventions into statements.json.

The Codex model (see conventions/standards-governance.md): convention docs stay
human-readable prose, but their normative requirements carry RFC 2119 keywords
in bold (**MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**). This script parses
every conventions/*.md file that opts in via YAML front matter and writes
standards/statements.json — the machine-readable registry that /check_standards
and the commands it is wired into query at runtime.

How a convention opts in — front matter with all three keys:

    ---
    domain: review           # free-form grouping (review, workflow, planning, …)
    status: enforced         # enforced (MUST violations block) | approved (findings only)
    sdlc_stage: review       # planning | implementation | review | all
    ---

A convention without front matter is skipped: it contributes no statements and
is not an error. This is what lets standards roll out incrementally.

Extraction rule: within an opted-in file, every sentence containing a bold
RFC 2119 keyword becomes one statement. Level is MUST if the sentence carries
**MUST** or **MUST NOT**, otherwise SHOULD. The slug is derived from the
statement text itself (level + first significant words after the keyword), so
it survives edits elsewhere in the doc; editing a statement's own wording
changes its slug, which is the intended signal that the standard changed.

Determinism: output is stable for unchanged input. `extracted_at` is preserved
from the existing statements.json when the statement set is unchanged, so CI
can regenerate and `git diff --exit-code standards/statements.json`.

Usage:
  python3 standards/extractor.py            # rewrite standards/statements.json
  python3 standards/extractor.py --check    # exit 1 if statements.json is stale

Requires: python3 + PyYAML (same prerequisites as setup.sh — no new deps).
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: python3 -m pip install pyyaml")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
CONVENTIONS_DIR = ROOT / "conventions"
OUTPUT = ROOT / "standards" / "statements.json"
SCHEMA_VERSION = "1.0"

VALID_STATUSES = {"enforced", "approved"}
VALID_STAGES = {"planning", "implementation", "review", "all"}
FRONT_MATTER_KEYS = ("domain", "status", "sdlc_stage")

# Bold RFC 2119 keywords, longest-first so MUST NOT wins over MUST.
KEYWORD_PAT = re.compile(r"\*\*(MUST NOT|SHOULD NOT|MUST|SHOULD)\*\*")

# Words that carry no routing signal in a slug.
SLUG_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "in", "on", "at", "by", "with",
    "from", "as", "is", "are", "be", "been", "it", "its", "to", "for",
    "that", "this", "these", "those", "when", "where", "which", "who",
    "their", "them", "they", "than", "then", "so", "any", "all", "one",
}
SLUG_PRE_WORDS = 2                                       # subject words before the keyword
SLUG_POST_WORDS = 5                                      # predicate words after it


def parse_front_matter(text: str):
    """Return (front_matter_dict | None, body). None when the file has no
    front matter block or it is not a mapping."""
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return None, text
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None, m.group(2)
    return (fm, m.group(2)) if isinstance(fm, dict) else (None, m.group(2))


def clean(sentence: str) -> str:
    """Strip markdown decoration but keep the bold keyword casing."""
    s = sentence
    s = re.sub(r"^[\s>*-]+", "", s)                      # list/blockquote markers
    s = KEYWORD_PAT.sub(lambda m: m.group(1), s)         # unbold the keyword
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)             # other bold
    s = re.sub(r"\*([^*]+)\*", r"\1", s)                 # italics
    s = re.sub(r"`([^`]*)`", r"\1", s)                   # inline code
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)       # links -> text
    s = s.replace("**", "")                              # stray bold markers left
    return re.sub(r"\s+", " ", s).strip().rstrip(":")    # by sentence splitting


def sentences(line: str):
    """Split a markdown line into sentences (rough but deterministic)."""
    return [p for p in re.split(r"(?<=[.!?])\s+", line) if p.strip()]


def make_slug(text: str, level_phrase: str) -> str:
    """level + subject words before the keyword + predicate words after it,
    so 'Agent filenames MUST use kebab-case' and 'Skill directories MUST use
    kebab-case' produce distinct, readable slugs."""
    lp = level_phrase.lower().replace(" ", "-")          # must | must-not | should | should-not
    idx = text.find(level_phrase)
    head, tail = (text[:idx], text[idx + len(level_phrase):]) if idx >= 0 else ("", text)

    def significant(chunk: str):
        words = re.sub(r"[^a-z0-9\s-]", "", chunk.lower()).split()
        return [w for w in words if w not in SLUG_STOPWORDS]

    pre = significant(head)[-SLUG_PRE_WORDS:]
    post = significant(tail)[:SLUG_POST_WORDS]
    parts = [lp] + pre + post
    return "-".join(parts) if (pre or post) else lp


def extract_file(path: Path):
    """Yield statement dicts from one opted-in convention file."""
    fm, body = parse_front_matter(path.read_text(encoding="utf-8"))
    if fm is None or not all(k in fm for k in FRONT_MATTER_KEYS):
        return
    status, stage = str(fm["status"]), str(fm["sdlc_stage"])
    if status not in VALID_STATUSES:
        raise SystemExit(f"ERROR {path.relative_to(ROOT)}: status '{status}' "
                         f"not in {sorted(VALID_STATUSES)}")
    if stage not in VALID_STAGES:
        raise SystemExit(f"ERROR {path.relative_to(ROOT)}: sdlc_stage '{stage}' "
                         f"not in {sorted(VALID_STAGES)}")

    in_code = False
    for raw_line in body.splitlines():
        if raw_line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code or not KEYWORD_PAT.search(raw_line):
            continue
        for sent in sentences(raw_line):
            m = KEYWORD_PAT.search(sent)
            if not m:
                continue
            level_phrase = m.group(1)                    # e.g. "MUST NOT"
            level = "MUST" if level_phrase.startswith("MUST") else "SHOULD"
            text = clean(sent)
            yield {
                "slug": make_slug(text, level_phrase),
                "source": str(path.relative_to(ROOT)),
                "domain": str(fm["domain"]),
                "sdlc_stage": stage,
                "level": level,
                "text": text,
                "status": status,
            }


def dedupe_slugs(statements):
    """Repeated slugs get a deterministic -2, -3 … suffix in file order."""
    seen = {}
    for st in statements:
        n = seen.get(st["slug"], 0) + 1
        seen[st["slug"]] = n
        if n > 1:
            st["slug"] = f"{st['slug']}-{n}"
    return statements


def build():
    statements = []
    for path in sorted(CONVENTIONS_DIR.glob("*.md")):
        statements.extend(extract_file(path))
    return dedupe_slugs(statements)


def render(statements) -> str:
    extracted_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if OUTPUT.exists():
        try:
            old = json.loads(OUTPUT.read_text(encoding="utf-8"))
            if old.get("statements") == statements:      # unchanged -> stable output
                extracted_at = old.get("extracted_at", extracted_at)
        except (json.JSONDecodeError, OSError):
            pass
    doc = {"version": SCHEMA_VERSION, "extracted_at": extracted_at,
           "statements": statements}
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def main():
    out = render(build())
    if "--check" in sys.argv:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != out:
            print("STALE: standards/statements.json does not match conventions/ — "
                  "run: python3 standards/extractor.py")
            sys.exit(1)
        print(f"OK: standards/statements.json is current "
              f"({len(json.loads(out)['statements'])} statements)")
        return
    OUTPUT.write_text(out, encoding="utf-8")
    stmts = json.loads(out)["statements"]
    musts = sum(1 for s in stmts if s["level"] == "MUST")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {len(stmts)} statements "
          f"({musts} MUST, {len(stmts) - musts} SHOULD) "
          f"from {len({s['source'] for s in stmts})} conventions")


if __name__ == "__main__":
    main()
