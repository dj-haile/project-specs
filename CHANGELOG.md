# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Added
- **Anti-rationalization tables** ("Common Shortcuts to Avoid") in core commands: `create_plan`, `implement_plan`, `validate_plan`, and the new `spec` command. Pre-written rebuttals to common excuses agents use to skip workflow steps. Based on patterns from [Addy Osmani's Agent Skills research](https://addyosmani.com/blog/agent-skills/).
- **Spec command** (`commands/core/spec.md`): New `/spec` command that produces a requirements specification with acceptance criteria before `/create_plan`. Separates "what are we building" from "how are we building it."
- **Scope discipline** in `implement_plan.md`: Hard rule requiring the agent to STOP and present deviations before modifying any file not listed in the plan.
- **Workflow router** in `AGENTS.md`: Decision tree and quick-reference table helping users and agents pick the right command sequence for any task type.
- **Progressive disclosure** guidance in `conventions/three-layer-architecture.md`: File structure and context-loading best practices to prevent attention degradation.
- **Spec-first workflow** pattern in `conventions/workflow-patterns.md`: New workflow pattern showing `/spec` → `/create_plan` → `/implement_plan` flow.
- **Usage guide** (`examples/usage-guide.md`): Comprehensive guide with concrete examples for all new features.
- Spec-awareness in `create_plan.md`: Plan command now checks for and references existing spec documents.

### Changed
- **Verification hardening** in `implement_plan.md`: Removed the "skip pause for consecutive phases" escape hatch. Verification between phases is now non-negotiable — the agent must present results and wait for human confirmation after every phase.

## [1.0.0] - 2026-03-24

### Added
- Initial release of reusable Claude Code spec framework
- 6 reusable agents (codebase-analyzer, codebase-locator, codebase-pattern-finder, thoughts-analyzer, thoughts-locator, web-search-researcher)
- 11 core commands (create_plan, iterate_plan, research_codebase, implement_plan, validate_plan, commit, describe_pr, debug, create_handoff, resume_handoff, local_review)
- 7 integration commands (ticket_plan, ticket_research, ticket_impl, ticket_oneshot, ticket_manage, founder_mode, create_worktree)
- specs.config.yaml configuration system
- setup.sh installer with --link, --copy, and --update modes
- Skill template with annotated SKILL.md
- 5 conventions documents
- 3 example configurations (api-service, frontend-app, data-pipeline)
- PR description template

### Changed
- Consolidated 3-variant commands (create_plan, iterate_plan, research_codebase) into single config-driven files
- Parameterized Linear-specific commands into generic ticket_* commands
- Removed all external process manager dependencies
- Inlined worktree creation logic (no external script dependency)
