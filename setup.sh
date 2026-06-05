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

EXAMPLES:
  ./setup.sh ~/my-project
  ./setup.sh ~/my-project --provider=cursor
  ./setup.sh ~/my-project --provider=codex --update
  ./setup.sh ~/my-project --link
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

# --- Argument parsing --------------------------------------------------------
if [[ $# -eq 0 || "$1" == "--help" || "$1" == "-h" ]]; then
  show_help
fi

TARGET_PATH=""
MODE="copy"
PROVIDER="claude"

for arg in "$@"; do
  case "$arg" in
    --help|-h)        show_help ;;
    --copy)           MODE="copy" ;;
    --link)           MODE="link" ;;
    --update)         MODE="update" ;;
    --provider=*)     PROVIDER="${arg#--provider=}" ;;
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

# Validate provider + load manifest
MANIFEST="$SCRIPT_DIR/providers/$PROVIDER/manifest.yaml"
if [[ ! -f "$MANIFEST" ]]; then
  print_error "Unknown provider: $PROVIDER"
  echo "Available providers:"
  for d in "$SCRIPT_DIR"/providers/*/; do
    [[ -f "$d/manifest.yaml" ]] && echo "  - $(basename "$d")"
  done
  exit 1
fi

# Check required commands (python3 needed for manifest parsing)
check_required_command mkdir
check_required_command cp
check_required_command ln
check_required_command python3

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
print_status "Source: $SCRIPT_DIR"

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
    read -p "Continue and overwrite? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      print_status "Cancelled"
      exit 0
    fi
  fi
fi

# Create install directory
print_status "Creating $BASE_DIR/ directory structure..."
mkdir -p "$INSTALL_DIR"

# --- Install helpers ---------------------------------------------------------

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
    cp -r "$src" "$dest"
    print_success "Copied $label → $BASE_DIR/$dest_rel/"
  fi
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
}

# --- Install agents + commands per transform type ----------------------------
if [[ "$TRANSFORM" == "skill+toml" ]]; then
  # Codex: commands become skills, agents become TOML
  install_commands_as_skills "$SCRIPT_DIR/commands" "$SKILLS_SUBDIR"
  install_agents_as_toml     "$SCRIPT_DIR/agents"   "$AGENTS_SUBDIR"
else
  # Claude / Cursor: straight copy
  install_dir_plain "$SCRIPT_DIR/agents"   "$AGENTS_SUBDIR"   "agents/"
  install_dir_plain "$SCRIPT_DIR/commands" "$COMMANDS_SUBDIR" "commands/"
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
if [[ -d "$SCRIPT_DIR/conventions" ]]; then
  if [[ "$TRANSFORM" == "skill+toml" ]]; then
    # Skills install under $TARGET_PATH/$SKILLS_SUBDIR/<name>/SKILL.md
    # ../../conventions from there → $TARGET_PATH/$(dirname SKILLS_SUBDIR)/conventions
    CONV_DEST="$TARGET_PATH/$(dirname "$SKILLS_SUBDIR")/conventions"
  else
    CONV_DEST="$INSTALL_DIR/conventions"
  fi
  rm -rf "$CONV_DEST"
  mkdir -p "$(dirname "$CONV_DEST")"
  cp -r "$SCRIPT_DIR/conventions" "$CONV_DEST"
  print_success "Installed convention docs → ${CONV_DEST#$TARGET_PATH/}/"
fi

# --- Provider-specific artifacts --------------------------------------------

# Root instructions file (e.g. Codex/Cursor AGENTS.md)
if [[ -n "$ROOT_INSTRUCTIONS" ]]; then
  ROOT_FILE="$TARGET_PATH/$ROOT_INSTRUCTIONS"
  if [[ ! -f "$ROOT_FILE" ]]; then
    if [[ -f "$SCRIPT_DIR/AGENTS.md" ]]; then
      cp "$SCRIPT_DIR/AGENTS.md" "$ROOT_FILE"
      print_success "Created $ROOT_INSTRUCTIONS at project root"
    else
      cat > "$ROOT_FILE" <<EOF
# Project Instructions

This project uses the project-specs framework (provider: $PROVIDER).
See specs.config.yaml for configuration and the installed commands/agents.
EOF
      print_success "Created $ROOT_INSTRUCTIONS stub at project root"
    fi
  else
    print_warning "$ROOT_INSTRUCTIONS already exists, skipping"
  fi
fi

# Settings/permissions template (Claude only, currently)
if [[ -n "$SETTINGS_TEMPLATE" ]]; then
  SRC_SETTINGS="$SCRIPT_DIR/.claude/$SETTINGS_TEMPLATE"
  if [[ -f "$SRC_SETTINGS" && ! -f "$INSTALL_DIR/$SETTINGS_TEMPLATE" ]]; then
    cp "$SRC_SETTINGS" "$INSTALL_DIR/$SETTINGS_TEMPLATE"
    print_success "Copied $SETTINGS_TEMPLATE → $BASE_DIR/"
  fi
fi

# Copy specs.config.yaml if not present
if [[ -f "$SCRIPT_DIR/specs.config.example.yaml" ]]; then
  if [[ ! -f "$TARGET_PATH/specs.config.yaml" ]]; then
    cp "$SCRIPT_DIR/specs.config.example.yaml" "$TARGET_PATH/specs.config.yaml"
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
else
  print_warning "specs.config.example.yaml not found in source"
fi

# Copy PR description template
if [[ -f "$SCRIPT_DIR/templates/pr_description.md" ]]; then
  cp "$SCRIPT_DIR/templates/pr_description.md" "$TARGET_PATH/pr_description.md"
  print_success "Copied pr_description.md to project root"
else
  print_warning "templates/pr_description.md not found in source"
fi

# Optional: Create thoughts/ directory structure
THOUGHTS_DIR=""
print_status "Create thoughts/ directory structure for collaboration?"
read -p "Create thoughts/ (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  THOUGHTS_DIR="$TARGET_PATH/thoughts/shared"
  mkdir -p "$THOUGHTS_DIR/plans"
  mkdir -p "$THOUGHTS_DIR/tickets"
  mkdir -p "$THOUGHTS_DIR/handoffs"
  mkdir -p "$THOUGHTS_DIR/prs"
  mkdir -p "$THOUGHTS_DIR/research"

  if [[ -f "$SCRIPT_DIR/templates/pr_description.md" ]]; then
    cp "$SCRIPT_DIR/templates/pr_description.md" "$THOUGHTS_DIR/pr_description.md"
  fi
  print_success "Created thoughts/ directory structure"
else
  print_status "Skipped thoughts/ directory"
fi

# Print summary
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
echo "  • Skill template: $SCRIPT_DIR/skills/_template/SKILL.md"
echo "  • Provider portability: $SCRIPT_DIR/conventions/provider-portability.md"
echo "  • PR template: $TARGET_PATH/pr_description.md"
if [[ -n "$THOUGHTS_DIR" && -d "$THOUGHTS_DIR" ]]; then
  echo "  • Thoughts: $THOUGHTS_DIR/"
fi
echo
