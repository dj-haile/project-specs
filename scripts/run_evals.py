#!/usr/bin/env python3
"""
run_evals.py — Routing evals for the project-specs framework.

A command/agent is only useful if the right user phrasing actually reaches it.
Descriptions are the routing surface: the model (or a future router) picks a
command by matching the user's words against frontmatter `description` text.
This script is a deterministic, CI-safe proxy for that match, so a description
edit that quietly breaks routing is caught at PR time instead of in the field.

What it does:
  1. Builds a stemmed TF-IDF index over every command/agent frontmatter
     (name + description), across a single unified ranking space so a prompt
     competes against ALL commands and agents at once — the realistic setting.
  2. Runs curated cases (evals/cases/<command>.json):
       - positive prompts must rank their command within top_k
       - negative prompts must NOT rank the command #1; if an `owner` is given,
         the owner must outrank the command (the prompt belongs to the owner)
  3. Flags near-duplicate descriptions: any two whose TF-IDF cosine exceeds
     COLLISION_THRESHOLD are reported as a routing hazard.
  4. Requires every core routed command to own a case file with at least one
     positive and one negative case, so a core command cannot ship unrouted.

A failure here almost always means "fix the description," not "fix the eval" —
see evals/README.md.

Every check is a named entry in CHECKS and is individually runnable, so a
single acceptance criterion can be bound to exactly one of them.

Requires: python3 + PyYAML (same prerequisites as setup.sh — no new deps).
No Node, no network, no randomness — fully deterministic.

Exit codes: 0 = all clear, 1 = one or more failures.
Usage:
  python3 scripts/run_evals.py [--quiet]                      # every check
  python3 scripts/run_evals.py --list-checks                  # names, one per line
  python3 scripts/run_evals.py --check <name>                 # exactly one check
  python3 scripts/run_evals.py --explain "your prompt here"   # debug: show ranking
"""

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: python3 -m pip install pyyaml")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT / "evals" / "cases"

# Two descriptions whose cosine similarity meets or exceeds this are treated as
# colliding — too alike to route between reliably. Tuned so genuinely distinct
# neighbors (create_plan vs ticket_plan) pass while true duplicates fail.
COLLISION_THRESHOLD = 0.72

# The core commands the framework routes to by name. Each must own a case file.
CORE_ROUTED = {"spec", "create_plan", "implement_plan", "validate_plan"}

# Words too common to carry routing signal. Kept small and generic on purpose;
# domain words like "plan", "ticket", "codebase" are NOT stopwords — they route.
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "for", "to",
    "of", "in", "on", "at", "by", "with", "from", "as", "is", "are", "be",
    "this", "that", "these", "those", "it", "its", "you", "your", "we", "our",
    "i", "me", "my", "can", "will", "would", "should", "could", "do", "does",
    "not", "no", "yes", "so", "than", "into", "out", "up", "down", "over",
    "want", "need", "please", "help", "use", "using", "used", "get", "got",
    "some", "any", "all", "more", "most", "when", "how", "what", "which",
    "about", "before", "after", "through", "via", "per", "one",
}


def stem(word: str) -> str:
    """A small, deterministic suffix stemmer. Not Porter-complete — just enough
    to fold plural/tense/derivation variants so corpus and query tokens meet
    (plans/planning/planned -> plan). Identical rules apply to both sides, so
    absolute correctness matters less than consistency."""
    w = word.lower()
    # Ordered longest-first so "implementation" -> "implement" before "-s" fires.
    for suf, repl in (
        ("ization", "ize"), ("ational", "ate"), ("iveness", "ive"),
        ("fulness", "ful"), ("ousness", "ous"), ("ation", ""), ("ments", ""),
        ("ment", ""), ("ness", ""), ("tion", "t"), ("sion", "s"),
        ("ing", ""), ("ies", "y"), ("ied", "y"), ("ive", ""), ("ful", ""),
        ("ers", ""), ("ing", ""), ("ed", ""), ("ly", ""), ("er", ""),
        ("es", ""), ("s", ""),
    ):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            w = w[: len(w) - len(suf)] + repl
            break
    # Collapse a trailing doubled consonant left by -ing/-ed (plann -> plan).
    if len(w) >= 4 and w[-1] == w[-2] and w[-1] not in "aeiou":
        w = w[:-1]
    return w


def tokenize(text: str) -> list:
    """Lowercase, split on non-alphanumerics, drop stopwords/shorties, stem."""
    raw = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [stem(t) for t in raw if t not in STOPWORDS and len(t) > 1]


def parse_frontmatter(path: Path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None
    return fm if isinstance(fm, dict) else None


class Index:
    """A tiny TF-IDF index: one document per command/agent."""

    def __init__(self):
        self.names = []          # doc id -> name
        self.kinds = {}          # name -> "command" | "agent"
        self.docs = {}           # name -> list[token]
        self.idf = {}            # token -> idf
        self.vecs = {}           # name -> {token: weight} (L2-normalized)

    def add(self, name: str, kind: str, text: str):
        self.names.append(name)
        self.kinds[name] = kind
        self.docs[name] = tokenize(text)

    def build(self):
        n = len(self.docs)
        df = Counter()
        for tokens in self.docs.values():
            for t in set(tokens):
                df[t] += 1
        # Smoothed idf; +1 so a term in every doc still has weight > 0.
        self.idf = {t: math.log((n + 1) / (d + 1)) + 1.0 for t, d in df.items()}
        for name, tokens in self.docs.items():
            self.vecs[name] = self._vectorize(tokens)

    def _vectorize(self, tokens: list) -> dict:
        tf = Counter(tokens)
        vec = {t: c * self.idf.get(t, 0.0) for t, c in tf.items()}
        norm = math.sqrt(sum(v * v for v in vec.values()))
        if norm > 0:
            vec = {t: v / norm for t, v in vec.items()}
        return vec

    def rank(self, prompt: str) -> list:
        """Return [(name, score), ...] sorted by descending cosine similarity.
        Ties break alphabetically by name for determinism."""
        q = self._vectorize(tokenize(prompt))
        scored = []
        for name, vec in self.vecs.items():
            # Cosine == dot product (both vectors are L2-normalized).
            common = set(q) & set(vec)
            score = sum(q[t] * vec[t] for t in common)
            scored.append((name, score))
        scored.sort(key=lambda x: (-x[1], x[0]))
        return scored

    def cosine(self, a: str, b: str) -> float:
        va, vb = self.vecs[a], self.vecs[b]
        return sum(va[t] * vb[t] for t in set(va) & set(vb))


def build_index() -> Index:
    idx = Index()
    files = sorted(
        list((ROOT / "commands").rglob("*.md")) + list((ROOT / "agents").glob("*.md"))
    )
    for f in files:
        fm = parse_frontmatter(f)
        if not fm:
            continue
        name = fm.get("name") or f.stem
        desc = str(fm.get("description", ""))
        kind = "agent" if f.parent.name == "agents" else "command"
        # Name tokens carry routing signal; include the split name ONCE so it
        # contributes without swamping the description (a name like
        # "codebase-pattern-finder" must not let "finder" outweigh what the
        # description actually says the agent does).
        idx.add(name, kind, f"{name.replace('_', ' ').replace('-', ' ')} {desc}")
    idx.build()
    return idx


def rank_position(ranking: list, name: str):
    for i, (n, _score) in enumerate(ranking):
        if n == name:
            return i  # 0-based
    return None


def run_cases(idx: Index):
    failures, passes = [], 0
    if not CASES_DIR.exists():
        return failures, passes, 0
    case_files = sorted(CASES_DIR.glob("*.json"))
    for cf in case_files:
        try:
            case = json.loads(cf.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            failures.append(f"  FAIL  {cf.relative_to(ROOT)}: invalid JSON: {e}")
            continue
        target = case.get("command")
        rel = cf.relative_to(ROOT)
        if not target or target not in idx.vecs:
            failures.append(f"  FAIL  {rel}: unknown command/agent '{target}'")
            continue
        trigger = case.get("trigger", {})

        for pos in trigger.get("positive", []):
            prompt = pos["prompt"]
            top_k = pos.get("top_k", 1)
            ranking = idx.rank(prompt)
            pos_idx = rank_position(ranking, target)
            if pos_idx is None or pos_idx >= top_k:
                got = ", ".join(f"{n}({s:.2f})" for n, s in ranking[:3])
                at = "unranked" if pos_idx is None else f"#{pos_idx + 1}"
                failures.append(
                    f"  FAIL  [{target}] positive not in top-{top_k} ({at}): "
                    f"\"{prompt}\"\n         top3: {got}"
                )
            else:
                passes += 1

        for neg in trigger.get("negative", []):
            prompt = neg["prompt"]
            owner = neg.get("owner")
            ranking = idx.rank(prompt)
            top_name = ranking[0][0] if ranking else None
            tgt_idx = rank_position(ranking, target)
            owner_idx = rank_position(ranking, owner) if owner else None
            problem = None
            if top_name == target:
                problem = f"ranks #1 but should not"
            elif owner and (owner_idx is None or (tgt_idx is not None and tgt_idx < owner_idx)):
                oat = "unranked" if owner_idx is None else f"#{owner_idx + 1}"
                tat = "unranked" if tgt_idx is None else f"#{tgt_idx + 1}"
                problem = f"outranks owner '{owner}' ({target} {tat} vs {owner} {oat})"
            if problem:
                got = ", ".join(f"{n}({s:.2f})" for n, s in ranking[:3])
                failures.append(
                    f"  FAIL  [{target}] negative {problem}: "
                    f"\"{prompt}\"\n         top3: {got}"
                )
            else:
                passes += 1
    return failures, passes, len(case_files)


def check_collisions(idx: Index):
    """Report any pair of descriptions too similar to route between."""
    failures = []
    names = idx.names
    pairs = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            c = idx.cosine(names[i], names[j])
            if c >= COLLISION_THRESHOLD:
                pairs.append((c, names[i], names[j]))
    pairs.sort(reverse=True)
    for c, a, b in pairs:
        failures.append(
            f"  FAIL  description collision ({c:.2f} ≥ {COLLISION_THRESHOLD}): "
            f"'{a}' vs '{b}' — differentiate their descriptions"
        )
    return failures


def check_core_command_coverage(idx=None):
    """Every name in CORE_ROUTED must have evals/cases/<name>.json carrying at
    least one positive and at least one negative case. A core command with no
    case file has no evidence that anyone's phrasing reaches it."""
    failures = []
    for name in sorted(CORE_ROUTED):
        rel = f"evals/cases/{name}.json"
        cf = CASES_DIR / f"{name}.json"
        if not cf.exists():
            failures.append(
                f"  FAIL  {rel}: missing — every core routed command needs a case file"
            )
            continue
        try:
            case = json.loads(cf.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            failures.append(f"  FAIL  {rel}: invalid JSON: {e}")
            continue
        trigger = case.get("trigger") or {}
        if not trigger.get("positive"):
            failures.append(f"  FAIL  {rel}: no positive case")
        if not trigger.get("negative"):
            failures.append(f"  FAIL  {rel}: no negative case")
    return failures


# --- Check registry ---------------------------------------------------------
# Keyed by the group name used in a plan's Criterion Bindings table, so
# `python3 scripts/run_evals.py --check <name>` runs exactly one bound group.

_stats = {"passes": 0, "case_files": 0}


def _run_cases(idx: Index):
    """run_cases with the registry's uniform (idx) -> failures signature; the
    counts it also returns are stashed for the summary line."""
    failures, passes, n_files = run_cases(idx)
    _stats["passes"] = passes
    _stats["case_files"] = n_files
    return failures


CHECKS = {
    "check_cases":                 _run_cases,
    "check_collisions":            check_collisions,
    "check_core_command_coverage": check_core_command_coverage,
}


def explain(idx: Index, prompt: str):
    print(f"\nRanking for: \"{prompt}\"\n")
    for i, (name, score) in enumerate(idx.rank(prompt)[:10]):
        print(f"  {i + 1:2d}. {score:5.3f}  {name} ({idx.kinds[name]})")
    print()


def main():
    quiet = "--quiet" in sys.argv

    if "--list-checks" in sys.argv:
        for name in CHECKS:
            print(name)
        sys.exit(0)

    idx = build_index()

    if "--explain" in sys.argv:
        i = sys.argv.index("--explain")
        if i + 1 < len(sys.argv):
            explain(idx, sys.argv[i + 1])
            return
        print("ERROR: --explain requires a prompt argument")
        sys.exit(1)

    if "--check" in sys.argv:
        i = sys.argv.index("--check")
        if i + 1 >= len(sys.argv):
            print("ERROR: --check requires a check name — see --list-checks")
            sys.exit(1)
        name = sys.argv[i + 1]
        if name not in CHECKS:
            print(f"ERROR: unknown check '{name}' — see --list-checks")
            sys.exit(1)
        failures = CHECKS[name](idx)
        if failures:
            print(f"\nrun_evals.py [{name}]: {len(failures)} failure(s)\n")
            print("\n".join(failures))
            print()
        elif not quiet:
            print(f"run_evals.py [{name}]: OK")
        sys.exit(1 if failures else 0)

    failures = []
    for fn in CHECKS.values():
        failures += fn(idx)
    passes, n_files = _stats["passes"], _stats["case_files"]

    if failures:
        print(f"\nrun_evals.py: {len(failures)} failure(s) "
              f"({passes} case assertion(s) passed across {n_files} case file(s))\n")
        print("\n".join(failures))
        print()
    elif not quiet:
        print(f"run_evals.py: OK — {passes} routing assertion(s) across "
              f"{n_files} case file(s) passed; no description collisions "
              f"(threshold {COLLISION_THRESHOLD})")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
