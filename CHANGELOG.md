# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-24

### Added
- Initial release extracted from dj-haile/skills-app
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
- Removed all HumanLayer dependencies
- Inlined worktree creation logic (no external script dependency)
