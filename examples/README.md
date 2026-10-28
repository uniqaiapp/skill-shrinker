# Examples

Two real-shaped instruction files, shrunk by the rules in `SKILL.md`. Every output file here is produced by the command next to it and checked byte-for-byte by `tests/test_scripts.py`, so the numbers in the main README are exactly what the script prints. All runs use `--tokens estimate` so they reproduce without a key; see `references/token-estimate.md` for what that means.

Run from the repository root.

## `claude-md/`: a project `CLAUDE.md`

A Next.js monorepo's `CLAUDE.md` that grew by accretion: two exact duplicates, one contradiction (tabs vs no tabs), sixteen narration lines, a 29-line setup script, a 14-row environment table, an empty "Deployment" section and a repeated heading.

| File | What it shows | Command |
|---|---|---|
| `before/CLAUDE.md` | the input, 188 lines | |
| `audit.txt` | every finding with line numbers | `python3 scripts/shrink.py audit examples/claude-md/before/CLAUDE.md --tokens estimate` |
| `after/CLAUDE.md` | the rewrite, 54 lines, every constraint verbatim | |
| `after/references/local-setup.md` | setup, env var names, troubleshooting (rule 8) | |
| `after/references/api-conventions.md` | the full handler example (rule 7) | |
| `compare.md` | before/after table and constraint check | `python3 scripts/shrink.py compare examples/claude-md/before/CLAUDE.md examples/claude-md/after/CLAUDE.md --tokens estimate --md` |

The compare output reports one constraint as **lost**: `Always use tabs for indentation.` That is the losing side of the contradiction, dropped on purpose because the file's own Prettier note says two spaces. `--strict` exits 2 on it, which is the point: the decision is visible, not silent. One constraint shows as **only in references** (the "restart the dev server" line, which moved to troubleshooting with its sentence intact).

## `skill-md/`: a `SKILL.md`

A release-notes skill with a duplicated rule, two overlapping trigger bullets, two long example blocks, an empty "Troubleshooting" section and five narration lines.

| File | What it shows | Command |
|---|---|---|
| `before/SKILL.md` | the input, 107 lines | |
| `audit.txt` | findings | `python3 scripts/shrink.py audit examples/skill-md/before/SKILL.md --tokens estimate` |
| `after/SKILL.md` | the rewrite, 45 lines, frontmatter and triggers intact | |
| `after/references/example-output.md` | the two example blocks, trimmed (rule 7) | |
| `compare.md` | table and constraint check: nothing lost | `python3 scripts/shrink.py compare examples/skill-md/before/SKILL.md examples/skill-md/after/SKILL.md --tokens estimate --md` |

## `report.txt`

All four files in one table:

```bash
python3 scripts/shrink.py report examples/claude-md/before/CLAUDE.md examples/claude-md/after/CLAUDE.md examples/skill-md/before/SKILL.md examples/skill-md/after/SKILL.md --tokens estimate
```

## Regenerating

After changing `scripts/shrink.py`, run the five commands above with `>` into the listed files, review the diff, and commit the script and the outputs together.
