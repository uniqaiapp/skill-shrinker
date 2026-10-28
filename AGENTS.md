# AGENTS.md

This repository is an agent skill plus a standalone script. The full instructions are in `SKILL.md`; read it first.

## Working in this repo
- Zero dependencies: Python 3.9+ standard library only. Do not add packages.
- Run tests: `python3 tests/run.py` (under 10 seconds, no network).
- The committed outputs in `examples/` are regenerated with the commands in `examples/README.md` and compared byte-for-byte by the tests. Change the script, regenerate, commit both.
- Keep `SKILL.md` under 500 lines; long material goes to `references/`. Run `python3 scripts/shrink.py audit SKILL.md` on this repo's own skill before a release.
- Author and maintainer is UniqAI <support@uniqai.app>; do not add personal names anywhere.

## Using this skill from another project
When the user asks to shrink, compress, trim, dedupe or audit a `CLAUDE.md`, `AGENTS.md`, `SKILL.md` or cursor rule, follow `SKILL.md` in this repository. Copy or clone the repo, then follow "Install" in `README.md`.
