# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-28

### Added
- `SKILL.md`: the shrink procedure (measure, audit, rewrite by eleven rules, verify) with constraints kept verbatim and rare detail moved to `references/`.
- `scripts/shrink.py`: `report` (lines, words, chars, tokens), `audit` (constraints, duplicates, near-duplicates, contradictions, narration, long code blocks, long sections, long tables, empty sections, repeated headings) and `compare` (before/after table, references total, constraint preservation check, `--strict`).
- Token counting via Anthropic `count_tokens` when `ANTHROPIC_API_KEY` is set, otherwise a labelled local estimate.
- Two worked examples (`examples/claude-md`, `examples/skill-md`) with committed audit and compare outputs, checked byte-for-byte by the tests.
- Adapters for Claude Code (`.claude-plugin/plugin.json`), Cursor (`.cursor/rules/skill-shrinker.mdc`), Codex (`codex/INSTRUCTIONS.md`) and generic agents (`AGENTS.md`).
- References: `references/playbook.md`, `references/token-estimate.md`.
