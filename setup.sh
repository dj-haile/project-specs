#!/usr/bin/env bash

# setup.sh — Install project-specs framework into a project
# Usage:
#   ./setup.sh /path/to/project              # Default: copy mode
#   ./setup.sh /path/to/project --link       # Symlink (updates propagate from source)
#   ./setup.sh /path/to/project --copy       # Copy (independent snapshot)
#   ./setup.sh /path/to/project --update     # Update existing installation
#   ./setup.sh --help                        # Show this help

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
  ./setup.sh /path/to/project              Default: copy mode
  ./setup.sh /path/to/project --link       Symlink (updates propagate from source)
  ./setup.sh /path/to/project --copy       Copy (independent snapshot)
  ./setup.sh /path/to/project --update     Update existing installation
  ./setup.sh --help                        Show this help

MODES:
  copy (default)  — Copy agents/, commands/, skills/ to .claude/
                    Updates from source will not propagate
  link            — Symlink agents/, commands/ to .claude/
                    Updates from source propagate automatically
  update          — Update existing installation (overwrite safely)

OUTPUT:
  Creates .claude/ directory with:
    .claude/agents/              Agent definitions
    .claude/commands/            Command definitions
    .claude/skills/              Project-specific skills (empty)
    specs.config.yaml            Configuration file
    pr_description.md            PR template

  Optionally creates thoughts/ directory structure for collaboration.

EXAMPLES:
  ./setup.sh ~/my-project
  ./setup.sh ~/my-project --link
  ./setup.sh ~/my-project --update
EOF
  exit 0
}

# Print colored status message
print_status() {
  echo -e "${BLUE}▶${NC} $1"
}

print_success() {
  echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
  echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
  echo -e "${RED}✗${NC} $1"
}

# Validate required commands
check_required_command() {
  if ! command -v "$1" &> /dev/null; then
    print_error "Required command not found: $1"
    exit 1
  fi
}

# Parse arguments
if [[ $# -eq 0 || "$1" == "--help" || "$1" == "-h" ]]; then
  show_help
fi

TARGET_PATH="$1"
MODE="${2:-copy}"

# Validate mode
if [[ ! "$MODE" =~ ^(--copy|--link|--update|copy|link|update)$ ]]; then
  print_error "Invalid mode: $MODE"
  echo "Valid modes: --copy, --link, --update"
  exit 1
fi

# Normalize mode (remove leading dashes)
MODE="${MODE#--}"

# Validate target path exists
if [[ ! -d "$TARGET_PATH" ]]; then
  print_error "Target path does not exist: $TARGET_PATH"
  exit 1
fi

# Resolve to absolute path
TARGET_PATH="$(cd "$TARGET_PATH" && pwd)"

print_status "Installing project-specs into $TARGET_PATH"
print_status "Mode: $MODE"
print_status "Source: $SCRIPT_DIR"

# Check required commands
check_required_command mkdir
check_required_command cp
check_required_command ln

# Check if .claude/ already exists
CLAUDE_DIR="$TARGET_PATH/.claude"
if [[ -d "$CLAUDE_DIR" ]]; then
  if [[ "$MODE" == "update" ]]; then
    print_warning ".claude/ already exists, updating..."
  else
    print_warning ".claude/ already exists"
    read -p "Continue and overwrite? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      print_status "Cancelled"
      exit 0
    fi
  fi
fi

# Create .claude directory structure
print_status "Creating .claude directory structure..."
mkdir -p "$CLAUDE_DIR"
mkdir -p "$CLAUDE_DIR/skills"

# Copy or symlink agents/
if [[ -d "$SCRIPT_DIR/agents" ]]; then
  if [[ -e "$CLAUDE_DIR/agents" ]]; then
    rm -rf "$CLAUDE_DIR/agents"
  fi

  if [[ "$MODE" == "link" ]]; then
    ln -s "$SCRIPT_DIR/agents" "$CLAUDE_DIR/agents"
    print_success "Symlinked agents/ → .claude/agents/"
  else
    cp -r "$SCRIPT_DIR/agents" "$CLAUDE_DIR/agents"
    print_success "Copied agents/ → .claude/agents/"
  fi
else
  print_warning "agents/ not found in source"
fi

# Copy or symlink commands/
if [[ -d "$SCRIPT_DIR/commands" ]]; then
  if [[ -e "$CLAUDE_DIR/commands" ]]; then
    rm -rf "$CLAUDE_DIR/commands"
  fi

  if [[ "$MODE" == "link" ]]; then
    ln -s "$SCRIPT_DIR/commands" "$CLAUDE_DIR/commands"
    print_success "Symlinked commands/ → .claude/commands/"
  else
    cp -r "$SCRIPT_DIR/commands" "$CLAUDE_DIR/commands"
    print_success "Copied commands/ → .claude/commands/"
  fi
else
  print_warning "commands/ not found in source"
fi

# Copy specs.config.yaml if not present
if [[ -f "$SCRIPT_DIR/specs.config.example.yaml" ]]; then
  if [[ ! -f "$TARGET_PATH/specs.config.yaml" ]]; then
    cp "$SCRIPT_DIR/specs.config.example.yaml" "$TARGET_PATH/specs.config.yaml"
    print_success "Created specs.config.yaml at project root"
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

  # Copy PR description template into thoughts if it exists
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
echo "Installed to:"
echo "  $CLAUDE_DIR/"
echo
echo "Next steps:"
echo "  1. Review and customize: $TARGET_PATH/specs.config.yaml"
echo "  2. Create your first skill: $CLAUDE_DIR/skills/my-skill/SKILL.md"
echo "  3. Configure agents in your project's specs.config.yaml"
echo
echo "Documentation:"
echo "  • Skill template: $SCRIPT_DIR/skills/_template/SKILL.md"
echo "  • PR template: $TARGET_PATH/pr_description.md"
if [[ -d "$THOUGHTS_DIR" ]]; then
  echo "  • Thoughts: $THOUGHTS_DIR/"
fi
echo
