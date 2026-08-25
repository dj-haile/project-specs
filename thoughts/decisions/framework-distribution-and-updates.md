# ADR-001: Keeping an installed project-specs up to date in a consumer repo

**Status:** Proposed
**Date:** 2026-08-24
**Deciders:** Dj Haile (framework owner)
**Reference install:** `~/projects/agent-readiness-cli`

## Context

`setup.sh` installs the framework into a target repo by copying files:

| Source | Destination in target repo | Mode |
|---|---|---|
| `agents/` | `.claude/agents/` | copy, or symlink with `--link` |
| `commands/` | `.claude/commands/` | copy, or symlink with `--link` |
| `conventions/` | `.claude/conventions/` | always copy |
| `standards/extractor.py`, `standards/statements.json` | `standards/` | always copy |
| `specs.config.example.yaml` | `specs.config.yaml` | copy once, never overwritten |
| `templates/pr_description.md` | `pr_description.md` | overwritten on every run |

In `agent-readiness-cli`, every one of those paths is listed in `.gitignore`. The
framework is local developer tooling there. It never enters that repo's history,
so a collaborator who clones `agent-readiness-cli` gets none of it.

Five gaps make updates hard today:

1. **No record of what is installed.** Nothing writes the upstream commit SHA, the
   source URL, or the install date. A developer cannot tell whether the copy in
   `.claude/` is current without diffing it against a clone by hand.
2. **`--update` does not fetch.** It re-copies whatever is on disk at `SCRIPT_DIR`.
   If the local clone is three weeks stale, the "update" installs stale files.
3. **`--link` covers half the framework.** `install_dir_plain` (setup.sh:218) honours
   link mode, but only `agents/` and `commands/` go through it. `conventions/` and
   `standards/` are always `cp -r`, so a symlinked install still goes stale on the
   convention docs and the statements registry that `/check_standards` reads.
4. **The installer needs a local clone.** There is no way to install or update
   straight from `git@github.com:dj-haile/project-specs.git`.
5. **Updates clobber local edits.** `pr_description.md` is overwritten on every run.
   `conventions/` and `standards/` are `rm -rf`'d and re-copied, so a project-local
   convention or a project-local statement is destroyed without a warning.

There is no release process: the repo has no git tags, and `CHANGELOG.md` keeps
everything under `[Unreleased]`. A related channel already exists — the read-only
agents are published as community skills (`npx skills add dj-haile/project-specs`)
— but it carries only those seven agents, not the commands, conventions, or
standards registry.

**Constraints that shape the answer:**

- Three providers (claude, codex, cursor). Codex and Cursor need a format
  transform at install time, so they cannot be symlinked.
- Consumer repos deliberately keep framework files out of their git history.
- The framework is markdown plus two small Python scripts. No build step, no
  runtime dependency beyond `python3` and PyYAML.
- One maintainer, a handful of consumer repos, other people starting to use it.

## Decision

Add version tracking and a self-fetching updater to `setup.sh`, and fix `--link`
so it covers the whole framework.

Concretely:

1. Write an install stamp at the consumer root on every install.
2. Teach `--update` to fetch upstream itself, so the developer does not need to
   know where the clone lives or remember to pull it.
3. Add `--check` to report whether an install is behind, and by which changelog
   entries.
4. Add `--ref=<tag|branch|sha>` so a consumer repo can pin a version.
5. Protect locally-modified files during an update.
6. Extend `--link` to `conventions/` and `standards/` for `--provider=claude`.

## Options Considered

### Option A: Git submodule at `.project-specs/`, generate into `.claude/`

| Dimension | Assessment |
|---|---|
| Complexity | Medium |
| Update effort | `git submodule update --remote` + re-run install |
| Pinning | Strong — the parent repo records a SHA |
| Provider coverage | All three (install step still runs the transform) |
| Team familiarity | Low — submodules are widely disliked |

**Pros:** Git does the version tracking. The pinned SHA is visible in `git log`.
Collaborators get the same version.
**Cons:** Requires committing `.gitmodules` and a gitlink into consumer repos that
currently keep the framework out of their history entirely. Every collaborator
must run `git submodule update --init`, and forgetting it produces an empty
directory with a confusing error. Still needs an install step on top, so it does
not remove `setup.sh`, only adds a layer beneath it.

### Option B: Git subtree vendored into the consumer repo

| Dimension | Assessment |
|---|---|
| Complexity | Medium |
| Update effort | `git subtree pull --prefix=...` |
| Pinning | Implicit — whatever was last pulled |
| Provider coverage | All three |
| Team familiarity | Low |

**Pros:** No extra clone step for collaborators. Everything is in the repo.
**Cons:** Puts ~60 framework files into the consumer's history and diffs, which
contradicts the current `.gitignore` decision. Local edits turn into real merge
conflicts on every pull. Reverses cleanly only with care.

### Option C: Symlink everything to one shared clone (extend `--link`)

| Dimension | Assessment |
|---|---|
| Complexity | Low |
| Update effort | `git -C ~/projects/project-specs pull` — every linked repo updates at once |
| Pinning | None — all repos move together |
| Provider coverage | Claude only |
| Team familiarity | High |

**Pros:** Smallest change. One pull updates every project on the machine. Matches
how the maintainer already works, with all repos under `~/projects/`.
**Cons:** No pinning, so a breaking upstream change hits every project on the same
pull. Symlinks break if the clone moves or is renamed. Useless to anyone who does
not have the clone, and useless in CI or a container. Codex and Cursor cannot use
it, because their install needs a format transform.

### Option D: Versioned installer with an install stamp and a self-fetching update

| Dimension | Assessment |
|---|---|
| Complexity | Medium — ~120 lines of bash and python in `setup.sh` |
| Update effort | one command inside the consumer repo |
| Pinning | Explicit, per consumer repo, via the stamp |
| Provider coverage | All three |
| Team familiarity | High — it is the tool they already run |

**Pros:** Works for every provider, because the transform re-runs on each update.
Works for someone who has never cloned the repo. Each consumer repo pins its own
version, so upgrades are opt-in per project. Answers "am I out of date?" without a
manual diff. Keeps framework files out of the consumer's git history.
**Cons:** Still a copy, so the installer has to detect and protect locally-edited
files rather than relying on git to merge them. Adds one more file at the consumer
root. The updater needs a cache directory and network access.

### Option E: Publish as an installable package (pipx / npx)

| Dimension | Assessment |
|---|---|
| Complexity | High |
| Update effort | `pipx upgrade project-specs` |
| Pinning | Semver |
| Provider coverage | All three |
| Team familiarity | High for consumers, new work for the maintainer |

**Pros:** The best experience for other people. Standard versioning and standard
upgrade commands. Complements the existing `npx skills add` channel.
**Cons:** Needs a release process the repo does not have yet — no tags, no cut
versions, everything sits under `[Unreleased]`. Premature while the framework is
still changing weekly.

## Trade-off Analysis

The real choice is between **git doing the versioning** (A, B) and **the installer
doing the versioning** (D).

Git-based options are cheaper to build but fight the existing design. Consumer
repos gitignore the framework on purpose, and both A and B require putting
framework state back into the consumer's history. They also cannot serve Codex or
Cursor without an install step on top, so neither one replaces `setup.sh`.

Option C is genuinely useful and nearly free, but only on the maintainer's own
machine and only for Claude. Treat it as a convenience mode, not the answer.

Option D costs more to build, but it is the only option that satisfies all four
constraints at once: multi-provider, no framework files in consumer history, works
without a local clone, and pins per project. It also builds the exact metadata that
Option E would need later — a source URL, a ref, and a commit SHA are the same
things a package version records.

Option E is the right long-term answer once other teams depend on the framework.
It needs a release process first: cut a `v0.1.0` tag, move `[Unreleased]` entries
under it, and keep tagging. Do that groundwork now, and E becomes a small step
later rather than a rewrite.

**Recommendation: D as the mechanism, C as a convenience flag, E as the follow-on.**

## Consequences

**Easier:**
- A developer runs one command inside the consumer repo to get the latest, with no
  knowledge of where the framework clone lives.
- `--check` answers "is this install stale, and what changed?" from `CHANGELOG.md`.
- Each consumer repo pins its own version, so upgrading `agent-readiness-cli` does
  not disturb any other project.
- Installing on a fresh machine no longer needs a manual `git clone` first.

**Harder:**
- `setup.sh` grows a network path, a cache directory, and file-hash bookkeeping.
  It needs tests, and CI needs a case that runs the updater against a local fixture
  repo rather than the network.
- The stamp becomes a real interface. Changing its shape breaks existing installs,
  so it needs a `schema` field from day one.

**To revisit:**
- Once three or more people outside this machine use the framework, reconsider
  Option E and publish a package.
- If consumer repos ever start committing the framework rather than ignoring it,
  Option B becomes viable and the stamp becomes redundant.

## Design sketch

**Install stamp** — `.project-specs.json` at the consumer root, gitignored alongside
the rest of the install:

```json
{
  "schema": 1,
  "source": "git@github.com:dj-haile/project-specs.git",
  "ref": "main",
  "commit": "20a0e94...",
  "provider": "claude",
  "mode": "copy",
  "installed_at": "2026-08-24T09:12:00Z",
  "files": {
    ".claude/conventions/naming-conventions.md": "sha256:9f2c...",
    "standards/statements.json": "sha256:41ab...",
    "pr_description.md": "sha256:7d10..."
  }
}
```

The `files` map records the hash the installer wrote. On update, `setup.sh`
re-hashes each file. If the current hash differs from the recorded one, the
developer edited it — the installer skips that file and lists it under
"kept your local changes" at the end. That removes the `pr_description.md`
clobbering and protects project-local conventions.

**New flags:**

| Flag | Behaviour |
|---|---|
| `--from=<git-url>` | Clone or fetch into `~/.cache/project-specs/<ref>` and install from there. No prior clone needed. |
| `--ref=<tag\|branch\|sha>` | Which upstream ref to install or update to. Defaults to the stamp's `ref`, else `main`. |
| `--update` (changed) | Read the stamp, fetch the recorded source at the recorded ref, re-install, rewrite the stamp. Falls back to the current behaviour when there is no stamp. |
| `--check` | Compare the stamp's commit to upstream. Print the commit count behind and the `CHANGELOG.md` entries added since. Exit 1 when behind, so CI can gate on it. |
| `--link` (extended) | For `--provider=claude`, symlink `conventions/` and `standards/` as well as `agents/` and `commands/`. |

**Discoverability:** add `commands/core/specs_update.md` so `/specs_update` runs the
check and the update from inside an agent session, and document both in `README.md`,
which currently says nothing about updating an existing install.

## Action Items

1. [ ] Cut `v0.1.0`: move `CHANGELOG.md`'s `[Unreleased]` entries under a version heading and tag the repo. Pinning by tag needs tags to exist.
2. [ ] Write the install stamp (`.project-specs.json`, schema 1) at the end of every `setup.sh` run, including per-file hashes.
3. [ ] Add `--from=<git-url>` with a `~/.cache/project-specs/<ref>` clone cache.
4. [ ] Rewrite `--update` to read the stamp, fetch, re-install, and rewrite the stamp.
5. [ ] Add local-edit protection: skip files whose hash no longer matches the stamp, and report them.
6. [ ] Add `--check` with changelog diff output and a non-zero exit when behind.
7. [ ] Extend `--link` to `conventions/` and `standards/` for the claude provider.
8. [ ] Add `commands/core/specs_update.md` and an "Updating an install" section to `README.md`.
9. [ ] Add a CI job that installs into a fixture repo, commits an upstream change, runs `--update`, and asserts the change landed and a locally-edited file survived.
10. [ ] Add the stamp path to the recommended `.gitignore` block in the docs.

## Interim answer (works today, no code changes)

Until the above lands, this two-part command updates an existing install:

```bash
git -C ~/projects/project-specs pull && \
  ~/projects/project-specs/setup.sh ~/projects/agent-readiness-cli --update --yes
```

`--update --yes` keeps `specs.config.yaml` and skips the `thoughts/` prompt. It
does overwrite `pr_description.md`, `.claude/conventions/`, and `standards/`, so
check for local edits to those before running it.
