---
# SKILL.md Frontmatter — Required fields
# This YAML block defines metadata about the skill that Claude Code and other tools use.

name: my-skill-name              # kebab-case, unique within this project
                                 # Used for: skill invocation, references, logging
                                 # Must not contain spaces or special characters

description: |                   # Brief description of what this skill does.
  This appears in skill listings and helps agents decide when to use it.
  Keep it to 1-3 sentences.
  Explain the "what" and the "when", not the "why".

version: 1.0.0                   # Semantic versioning (major.minor.patch)
                                 # Bump when: features (minor), breaking changes (major)

author: Your Name                # Who created or maintains this skill

tags: [domain, capability]       # Searchable tags for discovery
                                 # Examples: [code-analysis, testing, documentation]

# Optional fields below — include only if relevant to your skill

model: sonnet                     # Default Claude model for this skill
                                 # Options: opus, sonnet, haiku
                                 # Can be overridden at invocation time

tools:                            # Tools this skill needs access to
  - Read                          # Read files from the filesystem
  - Grep                          # Search file contents with regex
  - Glob                          # Find files by pattern matching
  - Bash                          # Execute shell commands
  - WebFetch                      # Fetch and analyze web content
  # Add only the tools your skill actually needs

triggers:                         # Auto-suggestion triggers
                                 # When these conditions are true, Claude might suggest this skill
  keywords:                       # Trigger if user mentions these words
    - relevant
    - terms
    - keywords

  file_patterns:                  # Trigger if these files are in scope
    - "**/*.ext"
    - "src/**/*.ts"

# END Frontmatter — Regular Markdown begins below
---

# [Skill Name]

## Purpose

What problem does this skill solve? When should it be invoked?

Example:
- "Use this skill when you need to analyze a codebase for patterns"
- "Invoked by: other skills that need code structure analysis"
- "User-facing: Yes (can be called directly)"

## Prerequisites

What must be true for this skill to work?

Examples:
- Required MCP connections (e.g., "Requires GitHub API access")
- File structures (e.g., "Project must have src/ and tests/ directories")
- Environment setup (e.g., "Node.js 18+ must be installed")
- Permissions (e.g., "Read access to codebase required")

If there are no prerequisites, write "None — this skill is self-contained."

## Process

Step-by-step instructions for the AI to follow. Be precise and actionable.

### Step 1: [Name of First Step]

Detailed instructions for what to do, what to check, and how to decide what to do next.

Example:
```
1. Use Glob to find all files matching pattern **/*.ts
2. For each file:
   a. Read first 50 lines
   b. Check for patterns: import, export, interface
   c. Accumulate metadata: file path, exported names, imports
3. If total files > 100, warn user about large scope
```

### Step 2: [Name of Second Step]

Include decision trees, error handling, and fallbacks:

Example:
```
IF no files found:
  → Return "No matching files in scope"
ELSE IF files found:
  → Parse file list
  → If parsing fails, try alternate approach
  → Accumulate results
```

### Step 3: [Name of Third Step]

Continue until the skill's goal is achieved.

## Output Format

What should the skill produce? Describe format, location, and structure.

Examples:
- "Returns a JSON object with keys: [files, imports, exports, errors]"
- "Writes analysis.md to project root"
- "Prints colored summary to stdout, saves detailed log to project root"
- "Returns array of objects: [{path, matches, context}]"

## Examples

Show example invocations and expected results. This helps users understand when to use the skill.

### Example 1: Typical Use Case

**Input:**
```
Analyze TypeScript files for unused imports
```

**Process:**
The skill finds all .ts files, extracts imports, checks usage...

**Output:**
```
{
  "filesAnalyzed": 42,
  "unusedImports": 12,
  "issues": [
    {"file": "src/api.ts", "import": "axios", "reason": "imported but never used"}
  ]
}
```

### Example 2: Edge Case

**Input:**
```
Analyze Python project (user mistakenly uses TypeScript skill)
```

**Output:**
```
Error: No .ts files found. Did you mean to analyze a Python project?
```

## Constraints

Limitations, things NOT to do, edge cases to handle.

Examples:
- "Do NOT modify files; this skill is read-only"
- "Do NOT make external API calls; this runs entirely locally"
- "Limited to projects with <50K files for performance"
- "Requires stable filesystem; skips symlinks to avoid loops"
- "Do NOT invoke other skills that would cause circular dependency"
- "Edge case: Projects with mixed encoding (UTF-8, Latin-1) may fail"

## Notes for Skill Authors

- **Keep it focused**: Each skill should do one thing well
- **Make it discoverable**: Use clear names, descriptions, and tags
- **Include safety guardrails**: Warn about limits, failures, edge cases
- **Test in isolation**: Verify the skill works without other context
- **Document assumptions**: What must be true about the project structure?
- **Handle errors gracefully**: Don't crash; explain what went wrong and why
