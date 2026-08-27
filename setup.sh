#!/usr/bin/env bash

# setup.sh — Install project-specs framework into a project
# Usage:
#   ./setup.sh /path/to/project                          # Default: copy mode, provider=claude
#   ./setup.sh /path/to/project --link                   # Symlink (Claude only; updates propagate)
#   ./setup.sh /path/to/project --copy                   # Copy (independent snapshot)
#   ./setup.sh /path/to/project --update                 # Update existing installation
#   ./setup.sh /path/to/project --provider=codex         # Install for a specific provider
#   ./setup.sh /path/to/project --provider=cursor --copy # Flags combine in any order
#   ./setup.sh --help                                    # Show this help

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Determine source directory (where setup.sh lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Where the framework files are READ from. Same as SCRIPT_DIR for a local
# install; a fetched export once --from/--update fetches its own source.
SRC_DIR="$SCRIPT_DIR"

# Every path (relative to the target) the installer wrote this run. Feeds the
# install record so a later update knows what it put there.
RECORD_PATHS=()
RECORD_NAME=".project-specs.json"

# Paths an update left alone because the developer had edited them.
KEPT_PATHS=()

# Show help text
show_help() {
  cat << 'EOF'
setup.sh — Install project-specs framework into any project

USAGE:
  ./setup.sh /path/to/project                    Default: copy mode, provider=claude
  ./setup.sh /path/to/project --link             Symlink (Claude only; updates propagate)
  ./setup.sh /path/to/project --copy             Copy (independent snapshot)
  ./setup.sh /path/to/project --update           Update existing installation
  ./setup.sh /path/to/project --provider=NAME    Install for a provider (claude|codex|cursor)
  ./setup.sh /path/to/project --from=GIT_URL     Fetch the framework from a git repo (no local clone needed)
  ./setup.sh /path/to/project --ref=NAME         Install a branch, tag, or revision (default: the source's HEAD branch)
  ./setup.sh /path/to/project --check            Report whether the install is behind, then stop (exit 1 when behind)
  ./setup.sh /path/to/project --yes              Non-interactive: overwrite if exists, skip optional prompts (CI)
  ./setup.sh --help                              Show this help

PROVIDERS:
  claude (default) — Installs markdown commands/agents to .claude/ (straight copy).
  codex            — Transforms commands into Skills (.agents/skills/<name>/SKILL.md),
                     agents into TOML (.codex/agents/), and writes AGENTS.md.
  cursor           — Installs markdown commands/agents/skills to .cursor/ (straight copy).

  Provider details (install paths, model tiers, capabilities) come from
  providers/<provider>/manifest.yaml. Default provider is "claude" so existing
  Claude Code installs are unaffected unless you pass --provider explicitly.

MODES:
  copy (default)  — Copy source into the provider's install dir (independent snapshot).
  link            — Symlink source (claude only; non-claude providers ignore --link
                    because they require a format transform that can't be symlinked).
  update          — Update existing installation (overwrite safely).

SOURCE:
  With no --from, the framework is read from the directory this script lives in.
  With --from, it is fetched into a local cache (SPECS_CACHE, or
  $XDG_CACHE_HOME/project-specs) and one revision is exported for the install.
  A --ref naming a branch tracks that branch; a tag or a revision pins the
  install, and the record says so.

EXAMPLES:
  ./setup.sh ~/my-project
  ./setup.sh ~/my-project --provider=cursor
  ./setup.sh ~/my-project --provider=codex --update
  ./setup.sh ~/my-project --link
  ./setup.sh ~/my-project --from=https://github.com/dj-haile/project-specs
  ./setup.sh ~/my-project --from=https://github.com/dj-haile/project-specs --ref=v1.0.0
  ./setup.sh ~/my-project --check
  ./setup.sh ~/my-project --update
EOF
  exit 0
}

# Print colored status message
print_status()  { echo -e "${BLUE}▶${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error()   { echo -e "${RED}✗${NC} $1"; }

# Validate required commands
check_required_command() {
  if ! command -v "$1" &> /dev/null; then
    print_error "Required command not found: $1"
    exit 1
  fi
}

# --- Minimal manifest reader -------------------------------------------------
# We use python3 (ubiquitous on macOS/Linux) rather than yq so the installer
# carries no extra dependency. manifest_get <file> <dotted.key> -> stdout.
# Returns empty string for null/missing keys.
manifest_get() {
  local file="$1" key="$2"
  python3 - "$file" "$key" <<'PY'
import sys
try:
    import yaml
except ImportError:
    sys.stderr.write("PyYAML is required to read provider manifests. "
                     "Install with: python3 -m pip install pyyaml\n")
    sys.exit(3)
data = yaml.safe_load(open(sys.argv[1])) or {}
cur = data
for part in sys.argv[2].split('.'):
    if isinstance(cur, dict) and part in cur:
        cur = cur[part]
    else:
        cur = None
        break
if cur is None:
    print("")
elif isinstance(cur, bool):
    print("true" if cur else "false")
else:
    print(cur)
PY
}

# --- Fetching a source ------------------------------------------------------
# With --from, the framework is fetched into a local mirror clone and exactly one
# revision is exported for this install. A mirror plus an export is used rather
# than a checkout because two projects can pin different revisions of the same
# source; a shared cache that checked refs in and out would fight itself.

EXPORT_DIR=""      # temp dir holding the exported revision; removed on exit

cleanup_export() {
  [[ -n "$EXPORT_DIR" && -d "$EXPORT_DIR" ]] && rm -rf "$EXPORT_DIR"
  return 0
}
trap cleanup_export EXIT

# Where a given source URL is mirrored. Keyed by a hash of the URL so two
# sources never share a directory and no URL character reaches the filesystem.
cache_dir_for() {
  local url="$1"
  local base="${SPECS_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/project-specs}"
  local key
  key="$(printf '%s' "$url" | python3 -c \
    'import hashlib,sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest()[:16])')"
  printf '%s/%s.git' "$base" "$key"
}

# Fetch $1 at ref $2, export it, and set SRC_DIR plus the REC_* record fields.
# Make sure the mirror for $1 exists and is current. Sets MIRROR on success.
# Separate from fetch_source because the staleness check needs the refs without
# exporting a tree.
fetch_mirror() {
  local url="$1"
  check_required_command git
  MIRROR="$(cache_dir_for "$url")"
  mkdir -p "$(dirname "$MIRROR")"
  if [[ -d "$MIRROR" ]]; then
    print_status "Refreshing cached source: $MIRROR"
    if ! git -C "$MIRROR" fetch --prune --quiet 2>/dev/null; then
      print_error "Could not fetch from $url"
      return 1
    fi
  else
    print_status "Fetching source into cache: $MIRROR"
    if ! git clone --mirror --quiet "$url" "$MIRROR" 2>/dev/null; then
      print_error "Could not clone $url"
      rm -rf "$MIRROR"
      return 1
    fi
  fi
  return 0
}

fetch_source() {
  local url="$1" ref="$2"
  check_required_command tar

  fetch_mirror "$url" || return 1
  local mirror="$MIRROR"

  # The source's own default branch, used as the tracking branch for a pin.
  local default_branch
  default_branch="$(git -C "$mirror" symbolic-ref --short HEAD 2>/dev/null || true)"
  [[ -z "$ref" ]] && ref="$default_branch"
  if [[ -z "$ref" ]]; then
    print_error "Could not determine a default branch for $url — pass --ref"
    return 1
  fi

  local commit
  if ! commit="$(git -C "$mirror" rev-parse --verify --quiet "${ref}^{commit}")"; then
    print_error "Reference not found in $url: $ref"
    return 1
  fi

  # A branch moves, so it is tracked. A tag or a raw revision does not, so the
  # install is pinned and staleness is measured against the default branch.
  if git -C "$mirror" show-ref --verify --quiet "refs/heads/$ref"; then
    REC_PINNED=false
    REC_TRACK="$ref"
  else
    REC_PINNED=true
    REC_TRACK="$default_branch"
  fi

  EXPORT_DIR="$(mktemp -d)"
  if ! git -C "$mirror" archive "$commit" | tar -x -C "$EXPORT_DIR"; then
    print_error "Could not export $ref ($commit) from $url"
    return 1
  fi

  SRC_DIR="$EXPORT_DIR"
  REC_SOURCE="$url"
  REC_REF="$ref"
  REC_COMMIT="$commit"
  print_success "Using $ref ($(printf '%.10s' "$commit")) from $url"
  return 0
}

# Decide where framework files are read from, and describe that source for the
# record. Runs before anything is written to the target.
resolve_source() {
  REC_SOURCE=""; REC_REF=""; REC_TRACK=""; REC_COMMIT=""; REC_PINNED=false

  # An update with no --from re-fetches whatever the record says it came from,
  # so a developer never has to remember where the framework lives. --ref given
  # here overrides the recorded reference and moves the install to it.
  local url="$SOURCE_URL" ref="$REQ_REF"
  if [[ -z "$url" && "$MODE" == "update" ]]; then
    url="$(record_field source)"
    if [[ -z "$ref" ]]; then
      ref="$(record_field ref)"
      if [[ "$(record_field pinned)" == "true" ]]; then
        # A pin is held until the developer names a different reference.
        ref="$(record_field commit)"
        print_status "Install is pinned to $(record_field ref); staying there"
      fi
    fi
  fi

  if [[ -n "$url" ]]; then
    fetch_source "$url" "$ref" || exit 1
    # A pinned install keeps the reference name the developer originally chose;
    # fetch_source resolved a bare revision and cannot know that name.
    if [[ -z "$SOURCE_URL" && -z "$REQ_REF" && "$MODE" == "update" \
          && "$(record_field pinned)" == "true" ]]; then
      REC_REF="$(record_field ref)"
      REC_PINNED=true
      REC_TRACK="$(record_field track)"
    fi
  else
    SRC_DIR="$SCRIPT_DIR"
    resolve_record_metadata
  fi
}

# --- Staleness report --------------------------------------------------------
# Reads the record, refreshes the cache, and says whether the installed revision
# is behind the branch it tracks. Writes nothing to the target. Exit 1 when a
# newer revision exists, so CI can gate on it.

cmd_check() {
  local rec_source rec_commit rec_ref rec_track rec_pinned
  rec_source="$(record_field source)"
  rec_commit="$(record_field commit)"
  rec_ref="$(record_field ref)"
  rec_track="$(record_field track)"
  rec_pinned="$(record_field pinned)"

  if [[ ! -f "$TARGET_PATH/$RECORD_NAME" ]]; then
    print_error "No $RECORD_NAME in $TARGET_PATH — nothing to compare against."
    echo "Run an install or an update first; it writes the record this reads."
    exit 1
  fi
  if [[ -z "$rec_source" || -z "$rec_commit" ]]; then
    print_error "$RECORD_NAME does not say where this install came from."
    exit 1
  fi
  [[ -z "$rec_track" ]] && rec_track="$rec_ref"

  fetch_mirror "$rec_source" || exit 1

  local head
  if ! head="$(git -C "$MIRROR" rev-parse --verify --quiet "${rec_track}^{commit}")"; then
    print_error "Tracked reference not found in $rec_source: $rec_track"
    exit 1
  fi

  local behind
  behind="$(git -C "$MIRROR" rev-list --count "${rec_commit}..${head}" 2>/dev/null || echo "")"
  if [[ -z "$behind" ]]; then
    print_error "Cannot compare $rec_commit against $rec_track — the installed revision is not in $rec_source."
    exit 1
  fi

  echo
  echo "Installed: $(printf '%.10s' "$rec_commit") ($rec_ref)"
  echo "Tracking:  $rec_track in $rec_source"

  if [[ "$behind" -eq 0 ]]; then
    print_success "This install is current."
    exit 0
  fi

  if [[ "$rec_pinned" == "true" ]]; then
    print_warning "This install is pinned to $rec_ref and stays there."
    print_warning "$rec_track is $behind revision(s) ahead, at $(printf '%.10s' "$head")."
    echo "To move it: re-run with --update --ref=<name>"
  else
    print_warning "This install is behind by $behind revision(s)."
    print_warning "Newest on $rec_track: $(printf '%.10s' "$head")"
    echo "To update: re-run with --update"
  fi

  local entries
  entries="$(python3 "$SUPPORT" changelog --mirror "$MIRROR" --old "$rec_commit" --new "$head" 2>/dev/null || true)"
  if [[ -n "$entries" ]]; then
    echo
    echo "Change log entries added since this install:"
    echo "$entries" | sed 's/^/  /'
  fi
  exit 1
}

# --- Install record ----------------------------------------------------------
# The record lives at <target>/.project-specs.json and says what was installed
# from where. scripts/installer_support.py owns its format; this file only
# gathers the inputs. See conventions/... via README "Updating an install".

SUPPORT="$SCRIPT_DIR/scripts/installer_support.py"

# Read one top-level field out of the target's record. Empty when absent.
record_field() {
  [[ -f "$SUPPORT" ]] || return 0
  [[ -f "$TARGET_PATH/$RECORD_NAME" ]] || return 0
  python3 "$SUPPORT" record-field --target "$TARGET_PATH" --field "$1" 2>/dev/null || true
}

# Stop before writing anything if the target holds a record from a newer
# installer — rewriting it here would silently drop fields we don't know about.
assert_record_readable() {
  [[ -f "$SUPPORT" ]] || return 0
  [[ -f "$TARGET_PATH/$RECORD_NAME" ]] || return 0
  if ! python3 "$SUPPORT" assert-schema --target "$TARGET_PATH"; then
    exit 1
  fi
}

# Describe the source this run installed from: its revision, its origin URL, and
# the branch it was on. Empty fields when the source is not a git working copy.
resolve_record_metadata() {
  if git -C "$SRC_DIR" rev-parse --git-dir >/dev/null 2>&1; then
    REC_COMMIT="$(git -C "$SRC_DIR" rev-parse HEAD 2>/dev/null || true)"
    REC_SOURCE="$(git -C "$SRC_DIR" remote get-url origin 2>/dev/null || true)"
    REC_REF="$(git -C "$SRC_DIR" symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
    REC_TRACK="$REC_REF"
  fi
  [[ -z "$REC_SOURCE" ]] && REC_SOURCE="$SRC_DIR"
  return 0
}

write_install_record() {
  if [[ ! -f "$SUPPORT" ]]; then
    print_warning "scripts/installer_support.py not found in source; no install record written"
    return 0
  fi
  local path_args=() p
  for p in "${RECORD_PATHS[@]}"; do path_args+=(--path "$p"); done
  # PROTECTED was read before the first write, which is the only point at which
  # "edited since the last install" can still be told apart from "just updated".
  local kept_args=()
  if [[ ${#PROTECTED[@]} -gt 0 ]]; then
    for p in "${PROTECTED[@]}"; do kept_args+=(--kept "$p"); done
  fi
  local pin_args=()
  [[ "$REC_PINNED" == true ]] && pin_args+=(--pinned)
  local out
  if out=$(python3 "$SUPPORT" write-record \
             --target "$TARGET_PATH" \
             --source "$REC_SOURCE" --ref "$REC_REF" --track "$REC_TRACK" \
             --commit "$REC_COMMIT" --provider "$PROVIDER" --mode "$MODE" \
             "${pin_args[@]}" "${kept_args[@]}" "${path_args[@]}" 2>&1); then
    print_success "Recorded install in $RECORD_NAME ($out files)"
  else
    print_warning "Could not write $RECORD_NAME: $out"
  fi
}

# --- Argument parsing --------------------------------------------------------
if [[ $# -eq 0 || "$1" == "--help" || "$1" == "-h" ]]; then
  show_help
fi

TARGET_PATH=""
MODE="copy"
PROVIDER="claude"
ASSUME_YES=false
CHECK_ONLY=false   # --check: report staleness and exit, writing nothing
SOURCE_URL=""      # --from: fetch the framework from here instead of SCRIPT_DIR
REQ_REF=""         # --ref: which branch, tag, or revision to install

for arg in "$@"; do
  case "$arg" in
    --help|-h)        show_help ;;
    --copy)           MODE="copy" ;;
    --link)           MODE="link" ;;
    --update)         MODE="update" ;;
    --check)          CHECK_ONLY=true ;;
    --yes|-y)         ASSUME_YES=true ;;
    --provider=*)     PROVIDER="${arg#--provider=}" ;;
    --from=*)         SOURCE_URL="${arg#--from=}" ;;
    --ref=*)          REQ_REF="${arg#--ref=}" ;;
    --*)              print_error "Unknown flag: $arg"; exit 1 ;;
    *)
      if [[ -z "$TARGET_PATH" ]]; then
        TARGET_PATH="$arg"
      else
        print_error "Unexpected argument: $arg"; exit 1
      fi
      ;;
  esac
done

if [[ -z "$TARGET_PATH" ]]; then
  print_error "No target path provided."
  echo "Run ./setup.sh --help for usage."
  exit 1
fi

# Validate target path exists
if [[ ! -d "$TARGET_PATH" ]]; then
  print_error "Target path does not exist: $TARGET_PATH"
  exit 1
fi
TARGET_PATH="$(cd "$TARGET_PATH" && pwd)"

# Check required commands (python3 needed for manifest parsing)
check_required_command mkdir
check_required_command cp
check_required_command ln
check_required_command python3

# Refuse a target recorded by a newer installer before fetching or writing.
assert_record_readable

# An install predating the record has no fingerprints to compare against, so
# this run cannot tell an edited file from an untouched one.
if [[ "$MODE" == "update" && "$CHECK_ONLY" == false && ! -f "$TARGET_PATH/$RECORD_NAME" ]]; then
  print_warning "No $RECORD_NAME in $TARGET_PATH — edited-file protection is unavailable for this run"
  print_warning "This run writes one, so the next update can protect your edits"
fi

# Report staleness and stop. Runs before anything is fetched for install or
# written, so a check can never modify the target.
if [[ "$CHECK_ONLY" == true ]]; then
  cmd_check
fi

# Decide where framework files are read from. Everything below reads SRC_DIR,
# which is this script's own directory unless --from fetched a source.
resolve_source

# Validate provider + load manifest (from the resolved source)
MANIFEST="$SRC_DIR/providers/$PROVIDER/manifest.yaml"
if [[ ! -f "$MANIFEST" ]]; then
  print_error "Unknown provider: $PROVIDER"
  echo "Available providers:"
  for d in "$SRC_DIR"/providers/*/; do
    [[ -f "$d/manifest.yaml" ]] && echo "  - $(basename "$d")"
  done
  exit 1
fi

# Resolve manifest values
BASE_DIR="$(manifest_get "$MANIFEST" install.base_dir)"
AGENTS_SUBDIR="$(manifest_get "$MANIFEST" install.agents_subdir)"
COMMANDS_SUBDIR="$(manifest_get "$MANIFEST" install.commands_subdir)"
SKILLS_SUBDIR="$(manifest_get "$MANIFEST" install.skills_subdir)"
COMMANDS_DEST="$(manifest_get "$MANIFEST" install.commands_dest)"
ROOT_INSTRUCTIONS="$(manifest_get "$MANIFEST" install.root_instructions)"
SETTINGS_TEMPLATE="$(manifest_get "$MANIFEST" install.settings_template)"
TRANSFORM="$(manifest_get "$MANIFEST" install.transform)"
DISPLAY_NAME="$(manifest_get "$MANIFEST" display_name)"

INSTALL_DIR="$TARGET_PATH/$BASE_DIR"

print_status "Installing project-specs into $TARGET_PATH"
print_status "Provider: $DISPLAY_NAME ($PROVIDER)"
print_status "Mode: $MODE | Transform: $TRANSFORM"
print_status "Source: $SRC_DIR"

# Non-claude providers can't be symlinked when a transform is required
if [[ "$MODE" == "link" && "$TRANSFORM" != "copy" ]]; then
  print_warning "Provider '$PROVIDER' requires a format transform; --link is not supported. Using copy."
  MODE="copy"
fi

# Check if install dir already exists
if [[ -d "$INSTALL_DIR" ]]; then
  if [[ "$MODE" == "update" ]]; then
    print_warning "$BASE_DIR/ already exists, updating..."
  else
    print_warning "$BASE_DIR/ already exists"
    if [[ "$ASSUME_YES" == true ]]; then
      REPLY="y"
    else
      read -p "Continue and overwrite? (y/N) " -n 1 -r
      echo
    fi
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      print_status "Cancelled"
      exit 0
    fi
  fi
fi

# Which installed files the developer has changed since the last install. Read
# once, before anything is written, so every install site sees the same answer.
PROTECTED=()
if [[ -f "$SUPPORT" && -f "$TARGET_PATH/$RECORD_NAME" ]]; then
  if ! PROTECTED_OUT="$(python3 "$SUPPORT" protected --target "$TARGET_PATH" 2>&1)"; then
    print_error "Could not determine which files you edited; refusing to overwrite blindly:"
    echo "$PROTECTED_OUT" | tail -5
    exit 1
  fi
  while IFS= read -r line; do
    [[ -n "$line" ]] && PROTECTED+=("$line")
  done <<< "$PROTECTED_OUT"
  if [[ ${#PROTECTED[@]} -gt 0 ]]; then
    print_status "${#PROTECTED[@]} file(s) edited since the last install will be kept"
  fi
fi

# Create install directory
print_status "Creating $BASE_DIR/ directory structure..."
mkdir -p "$INSTALL_DIR"

# --- Install helpers ---------------------------------------------------------

# Copy one directory into the target file by file, leaving edited files alone.
# A directory-at-a-time `cp -r` cannot make that decision, so the copy engine
# lives in installer_support.py and this reads back what it did.
sync_into() {
  local src="$1" dest="$2" out action rel
  # Captured rather than piped: inside a process substitution a crash in the
  # helper is invisible, and the installer would report success having copied
  # nothing.
  if ! out="$(python3 "$SUPPORT" sync --target "$TARGET_PATH" --src "$src" --dest "$dest" 2>&1)"; then
    print_error "Failed while installing $src:"
    echo "$out" | tail -5
    exit 1
  fi
  while IFS=$'\t' read -r action rel; do
    [[ "$action" == "kept" ]] && KEPT_PATHS+=("$rel")
  done <<< "$out"
  # The loop's final read hits EOF and returns non-zero; without this the
  # function's exit status would take `set -e` down with it.
  return 0
}

# Copy one file into the target unless the developer edited it.
sync_file_into() {
  local src="$1" dest="$2" rel="${2#$TARGET_PATH/}"
  if [[ ${#PROTECTED[@]} -gt 0 ]] && printf '%s\n' "${PROTECTED[@]}" | grep -Fxq "$rel"; then
    KEPT_PATHS+=("$rel")
    return 0
  fi
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
  return 0
}

# Plain copy/symlink of a source dir to a destination subdir under INSTALL_DIR.
install_dir_plain() {
  local src="$1" dest_rel="$2" label="$3"
  local dest="$INSTALL_DIR/$dest_rel"
  if [[ ! -d "$src" ]]; then
    print_warning "$label not found in source"
    return
  fi
  mkdir -p "$(dirname "$dest")"
  [[ -e "$dest" ]] && rm -rf "$dest"
  if [[ "$MODE" == "link" ]]; then
    ln -s "$src" "$dest"
    print_success "Symlinked $label → $BASE_DIR/$dest_rel/"
  else
    sync_into "$src" "$dest"
    print_success "Installed $label → $BASE_DIR/$dest_rel/"
  fi
  RECORD_PATHS+=("$BASE_DIR/$dest_rel")
}

# Transform each command markdown file into a Codex Skill folder:
#   commands/**/<name>.md  →  <skills_dir>/<name>/SKILL.md  (+ name/description frontmatter)
# Skills dir is relative to TARGET_PATH (Codex uses .agents/skills, not under .codex).
install_commands_as_skills() {
  local src="$1" skills_rel="$2"
  local skills_dir="$TARGET_PATH/$skills_rel"
  [[ -d "$src" ]] || { print_warning "commands/ not found in source"; return; }
  mkdir -p "$skills_dir"
  python3 - "$src" "$skills_dir" <<'PY'
import os, re, sys
src, out = sys.argv[1], sys.argv[2]
def split_front(text):
    # Returns (meta_dict, body_without_frontmatter)
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"\'')
    return meta, m.group(2).lstrip("\n")
count = 0
for root, _, files in os.walk(src):
    for fn in files:
        if not fn.endswith(".md"):
            continue
        path = os.path.join(root, fn)
        meta, body = split_front(open(path).read())
        base = os.path.splitext(fn)[0]
        name = meta.get("name") or base
        desc = meta.get("description") or f"{base} workflow"
        skill_dir = os.path.join(out, base)
        os.makedirs(skill_dir, exist_ok=True)
        front = f"---\nname: {name}\ndescription: \"{desc}\"\n---\n\n"
        with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
            f.write(front + body)
        count += 1
print(count)
PY
  print_success "Transformed commands → $skills_rel/<name>/SKILL.md (as Codex Skills)"
  RECORD_PATHS+=("$skills_rel")
}

# Transform each agent markdown file into a Codex TOML subagent def:
#   agents/<name>.md  →  <agents_dir>/<name>.toml
install_agents_as_toml() {
  local src="$1" agents_rel="$2"
  local agents_dir="$INSTALL_DIR/$agents_rel"
  [[ -d "$src" ]] || { print_warning "agents/ not found in source"; return; }
  mkdir -p "$agents_dir"
  python3 - "$src" "$agents_dir" <<'PY'
import os, re, sys
src, out = sys.argv[1], sys.argv[2]
def split_front(text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"\'')
    return meta, m.group(2)
def toml_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')
count = 0
for fn in os.listdir(src):
    if not fn.endswith(".md"):
        continue
    meta, body = split_front(open(os.path.join(src, fn)).read())
    base = os.path.splitext(fn)[0]
    name = meta.get("name", base)
    desc = meta.get("description", f"{base} agent")
    out_path = os.path.join(out, base + ".toml")
    with open(out_path, "w") as f:
        f.write(f'name = "{toml_escape(name)}"\n')
        f.write(f'description = "{toml_escape(desc)}"\n')
        f.write('developer_instructions = """\n')
        f.write(body.strip() + "\n")
        f.write('"""\n')
    count += 1
print(count)
PY
  print_success "Transformed agents → $agents_rel/<name>.toml (as Codex subagents)"
  RECORD_PATHS+=("$BASE_DIR/$agents_rel")
}

# --- Install agents + commands per transform type ----------------------------
if [[ "$TRANSFORM" == "skill+toml" ]]; then
  # Codex: commands become skills, agents become TOML
  install_commands_as_skills "$SRC_DIR/commands" "$SKILLS_SUBDIR"
  install_agents_as_toml     "$SRC_DIR/agents"   "$AGENTS_SUBDIR"
else
  # Claude / Cursor: straight copy
  install_dir_plain "$SRC_DIR/agents"   "$AGENTS_SUBDIR"   "agents/"
  install_dir_plain "$SRC_DIR/commands" "$COMMANDS_SUBDIR" "commands/"
fi

# Skills directory (project-specific skills live here for copy providers)
if [[ "$TRANSFORM" == "copy" && -n "$SKILLS_SUBDIR" ]]; then
  mkdir -p "$INSTALL_DIR/$SKILLS_SUBDIR"
fi

# --- Install convention docs the commands link to ----------------------------
# Commands reference ../../conventions/<doc>.md (relative to commands/<group>/).
# Those links only resolve if conventions/ is installed alongside the commands.
# For copy providers (Claude/Cursor) commands live at <base>/commands/<group>/,
# so ../../conventions resolves to <base>/conventions. For Codex, generated
# skills live at <skills_base>/<name>/SKILL.md, so ../../conventions resolves to
# <skills_base>/../conventions (i.e. alongside the skills root's parent).
if [[ -d "$SRC_DIR/conventions" ]]; then
  if [[ "$TRANSFORM" == "skill+toml" ]]; then
    # Skills install under $TARGET_PATH/$SKILLS_SUBDIR/<name>/SKILL.md
    # ../../conventions from there → $TARGET_PATH/$(dirname SKILLS_SUBDIR)/conventions
    CONV_DEST="$TARGET_PATH/$(dirname "$SKILLS_SUBDIR")/conventions"
  else
    CONV_DEST="$INSTALL_DIR/conventions"
  fi
  mkdir -p "$(dirname "$CONV_DEST")"
  sync_into "$SRC_DIR/conventions" "$CONV_DEST"
  print_success "Installed convention docs → ${CONV_DEST#$TARGET_PATH/}/"
  RECORD_PATHS+=("${CONV_DEST#$TARGET_PATH/}")
fi

# --- Install standards registry + extractor ----------------------------------
# Commands check artifacts against standards/statements.json (see
# conventions/standards-governance.md). Installed at the project root to match
# the default standards.statements_path in specs.config.yaml. Individual file
# copies (no rm -rf): the target may keep its own files in standards/.
if [[ -d "$SRC_DIR/standards" ]]; then
  STD_DEST="$TARGET_PATH/standards"
  mkdir -p "$STD_DEST"
  sync_file_into "$SRC_DIR/standards/extractor.py" "$STD_DEST/extractor.py"
  sync_file_into "$SRC_DIR/standards/statements.json" "$STD_DEST/statements.json"
  print_success "Installed standards registry → standards/"
  RECORD_PATHS+=("standards/extractor.py" "standards/statements.json")
fi

# --- Provider-specific artifacts --------------------------------------------

# Root instructions file (e.g. Codex/Cursor AGENTS.md)
if [[ -n "$ROOT_INSTRUCTIONS" ]]; then
  ROOT_FILE="$TARGET_PATH/$ROOT_INSTRUCTIONS"
  if [[ ! -f "$ROOT_FILE" ]]; then
    if [[ -f "$SRC_DIR/AGENTS.md" ]]; then
      cp "$SRC_DIR/AGENTS.md" "$ROOT_FILE"
      print_success "Created $ROOT_INSTRUCTIONS at project root"
    else
      cat > "$ROOT_FILE" <<EOF
# Project Instructions

This project uses the project-specs framework (provider: $PROVIDER).
See specs.config.yaml for configuration and the installed commands/agents.
EOF
      print_success "Created $ROOT_INSTRUCTIONS stub at project root"
    fi
    RECORD_PATHS+=("$ROOT_INSTRUCTIONS")
  else
    print_warning "$ROOT_INSTRUCTIONS already exists, skipping"
    RECORD_PATHS+=("$ROOT_INSTRUCTIONS")
  fi
fi

# Settings/permissions template (Claude only, currently)
if [[ -n "$SETTINGS_TEMPLATE" ]]; then
  SRC_SETTINGS="$SRC_DIR/.claude/$SETTINGS_TEMPLATE"
  if [[ -f "$SRC_SETTINGS" && ! -f "$INSTALL_DIR/$SETTINGS_TEMPLATE" ]]; then
    cp "$SRC_SETTINGS" "$INSTALL_DIR/$SETTINGS_TEMPLATE"
    print_success "Copied $SETTINGS_TEMPLATE → $BASE_DIR/"
  fi
  [[ -f "$INSTALL_DIR/$SETTINGS_TEMPLATE" ]] && RECORD_PATHS+=("$BASE_DIR/$SETTINGS_TEMPLATE")
fi

# Copy specs.config.yaml if not present
if [[ -f "$SRC_DIR/specs.config.example.yaml" ]]; then
  if [[ ! -f "$TARGET_PATH/specs.config.yaml" ]]; then
    cp "$SRC_DIR/specs.config.example.yaml" "$TARGET_PATH/specs.config.yaml"
    # Set the provider in the freshly-copied config to match this install
    python3 - "$TARGET_PATH/specs.config.yaml" "$PROVIDER" <<'PY'
import re, sys
path, provider = sys.argv[1], sys.argv[2]
text = open(path).read()
new = re.sub(r'^provider:\s*"[^"]*"', f'provider: "{provider}"', text, count=1, flags=re.M)
open(path, "w").write(new)
PY
    print_success "Created specs.config.yaml at project root (provider: $PROVIDER)"
  else
    print_warning "specs.config.yaml already exists at project root, skipping"
  fi
  RECORD_PATHS+=("specs.config.yaml")
else
  print_warning "specs.config.example.yaml not found in source"
fi

# Copy PR description template
if [[ -f "$SRC_DIR/templates/pr_description.md" ]]; then
  sync_file_into "$SRC_DIR/templates/pr_description.md" "$TARGET_PATH/pr_description.md"
  print_success "Installed pr_description.md at project root"
  RECORD_PATHS+=("pr_description.md")
else
  print_warning "templates/pr_description.md not found in source"
fi

# Optional: Create thoughts/ directory structure
THOUGHTS_DIR=""
print_status "Create thoughts/ directory structure for collaboration?"
if [[ "$ASSUME_YES" == true ]]; then
  REPLY="n"
  print_status "(--yes: skipping thoughts/ creation; enable later in specs.config.yaml)"
else
  read -p "Create thoughts/ (y/N) " -n 1 -r
  echo
fi
if [[ $REPLY =~ ^[Yy]$ ]]; then
  THOUGHTS_DIR="$TARGET_PATH/thoughts/shared"
  mkdir -p "$THOUGHTS_DIR/plans"
  mkdir -p "$THOUGHTS_DIR/tickets"
  mkdir -p "$THOUGHTS_DIR/handoffs"
  mkdir -p "$THOUGHTS_DIR/prs"
  mkdir -p "$THOUGHTS_DIR/research"

  if [[ -f "$SRC_DIR/templates/pr_description.md" ]]; then
    cp "$SRC_DIR/templates/pr_description.md" "$THOUGHTS_DIR/pr_description.md"
  fi
  print_success "Created thoughts/ directory structure"
else
  print_status "Skipped thoughts/ directory"
fi

# Record what this run installed, so an update knows what it can replace.
write_install_record

# Print summary
if [[ ${#KEPT_PATHS[@]} -gt 0 ]]; then
  echo
  print_warning "Kept your local changes (not overwritten):"
  printf '  • %s\n' "${KEPT_PATHS[@]}" | sort -u
fi

echo
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Installation Complete${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo
echo "Provider: $DISPLAY_NAME ($PROVIDER)"
echo "Installed to:"
echo "  $INSTALL_DIR/"
if [[ -n "$ROOT_INSTRUCTIONS" ]]; then
  echo "  $TARGET_PATH/$ROOT_INSTRUCTIONS"
fi
echo
echo "Next steps:"
echo "  1. Review and customize: $TARGET_PATH/specs.config.yaml"
echo "  2. Add project-specific skills under the provider's skills directory"
echo "  3. Confirm your provider discovers the installed files"
echo
echo "Documentation:"
# With --from, SRC_DIR is a temp export removed when this script exits, so
# pointing at it would hand the reader a path that no longer exists.
if [[ -n "$EXPORT_DIR" ]]; then
  echo "  • Framework source: $REC_SOURCE ($REC_REF)"
else
  echo "  • Skill template: $SRC_DIR/skills/_template/SKILL.md"
fi
if [[ -n "${CONV_DEST:-}" && -f "$CONV_DEST/provider-portability.md" ]]; then
  echo "  • Provider portability: ${CONV_DEST#$TARGET_PATH/}/provider-portability.md"
fi
echo "  • PR template: $TARGET_PATH/pr_description.md"
if [[ -n "$THOUGHTS_DIR" && -d "$THOUGHTS_DIR" ]]; then
  echo "  • Thoughts: $THOUGHTS_DIR/"
fi
echo
