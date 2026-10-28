---
name: skill-shrinker
description: Shrinks CLAUDE.md, AGENTS.md, SKILL.md and .cursor/rules files so they cost fewer tokens on every turn without losing a single instruction. Measures size (chars, words, tokens), flags duplicate, overlapping and contradictory rules, narration, oversized examples and dead sections, then rewrites with MUST/NEVER constraints kept verbatim and rare detail moved to references/. Use when the user says a CLAUDE.md, AGENTS.md, SKILL.md, cursor rule or system prompt is too long, asks to shrink, shorten, compress, trim, dedupe, tidy or audit an instruction file, asks how many tokens a skill costs, or wants progressive disclosure for a skill. Not for shortening prose, docs or READMEs written for humans, and not for minifying code.
license: MIT
metadata:
  version: 0.1.0
  author: UniqAI
  homepage: https://github.com/uniqaiapp/skill-shrinker
---

# skill-shrinker

Agent instruction files are loaded on every turn, so every padding line is paid for on every request. This skill shrinks `CLAUDE.md`, `AGENTS.md`, `SKILL.md`, `.cursor/rules/*.mdc` and similar files with a fixed procedure: measure, audit, rewrite by rule, verify that no instruction was lost. The most common trigger is "this CLAUDE.md is too long".

## When to use

- A `CLAUDE.md`, `AGENTS.md`, `SKILL.md` or cursor rule has grown past a screen and nobody remembers why.
- The user asks to shrink, compress, trim, dedupe, tidy, audit or "clean up" an instruction file or system prompt.
- The user asks how many tokens a skill or instruction file costs, or how much a rewrite saved.
- A skill should load less by default and keep detail in `references/` (progressive disclosure).
- Before publishing a skill, to check it for duplicate or contradictory rules.

## When NOT to use

- Prose for humans (README, docs, blog posts): different goals, use an editor.
- Code: this is not a minifier and never touches code semantics.
- Files under about 40 lines: the audit will find little; just read them.
- Rewriting what the instructions *mean*. The skill changes form, not policy. If two rules contradict each other, it reports that; the user decides which one survives.

## How it works

Run everything from the directory that holds the target file, or pass paths. All scripts are Python 3.9+ standard library.

1. **Measure the baseline.**
   `python3 scripts/shrink.py report CLAUDE.md`
   Prints lines, words, chars and tokens. Tokens are exact (Anthropic `count_tokens`) when `ANTHROPIC_API_KEY` is set, otherwise a local estimate; the output says which. Keep this output for the final comparison.

2. **Audit.**
   `python3 scripts/shrink.py audit CLAUDE.md`
   Prints, with line numbers: constraint sentences to keep verbatim; exact duplicate lines; near-duplicates; contradictions (same subject, opposite polarity); narration and filler phrases; code blocks over 15 lines; sections over 40 content lines; tables over 12 rows; empty sections; repeated headings. Thresholds: `--max-block`, `--max-section`. `--json` for machine use.

3. **Rewrite, applying the rules below in order.** Write the result to a new file next to the original (for example `CLAUDE.shrunk.md`) so the user can diff, or edit in place only when asked.

   1. **Constraints stay verbatim.** Every sentence containing MUST, MUST NOT, NEVER, ALWAYS, DO NOT, DON'T, SHALL, REQUIRED, FORBIDDEN keeps its exact wording. Move it, group it, but do not paraphrase it. The compare step checks this.
   2. **Delete exact duplicates**; keep the copy that sits in the most specific section.
   3. **Merge near-duplicates and overlapping rules** into one line that carries the union of the conditions. "Prefer named exports" and "Use named exports, not default" become one bullet.
   4. **Report contradictions, do not resolve them silently.** List each pair with line numbers and ask the user which one wins, or state the choice explicitly in the summary if the user asked for an unattended run.
   5. **Remove narration.** Lines that describe the document ("in this section we will", "as you can see", "it is important to note") carry no instruction. Delete the phrase; keep any instruction that was hiding behind it.
   6. **Prose to imperatives.** A paragraph that mixes rules and explanation becomes bullets of the form `verb + object + condition`. Drop "you should", "please", "make sure to".
   7. **One example per concept, the shortest one that still works.** Extra examples, full handler listings, long transcripts go to `references/<topic>.md` with a one-line pointer in the main file.
   8. **Move rare detail out.** Setup from scratch, troubleshooting, environment variable tables, long option lists, prompt libraries: `references/<topic>.md`, linked from the place where the agent would need it. The main file keeps only what is needed on a typical turn.
   9. **Delete empty and placeholder sections** and repeated headings. A heading with no content is a promise the file does not keep.
   10. **Keep the frontmatter and the triggers.** `name`, `description` and the "When to use" bullets are how the skill gets selected; shorten the description only if it is over the host's limit, and never drop trigger phrases from it.
   11. **Do not touch** code blocks that are kept, URLs, file paths, command lines, version numbers, or anything inside backticks.

4. **Verify.**
   `python3 scripts/shrink.py compare CLAUDE.md CLAUDE.shrunk.md`
   Prints a before/after table (lines, words, chars, tokens) plus the totals of the referenced files, and checks every constraint sentence from the original: kept verbatim, only in references, or lost. A lost constraint is a bug in the rewrite unless the user chose to drop it (for example one side of a contradiction). `--strict` exits 2 on any lost constraint; use it in CI. `--md` prints a Markdown table for the pull request.

5. **Report to the user.** Give the compare table, the list of moved sections with their new paths, every removed line that was not an exact duplicate, and every open contradiction. Never present an estimate as an exact count: the output labels tokens as `estimate` or `exact, <model>`; carry the label into the summary.

## Inputs / outputs

| Input | Output |
|---|---|
| One Markdown instruction file (any name, optional YAML frontmatter) | `report`: size table (text, `--md`, `--json`) |
| Same | `audit`: findings with line numbers (text or `--json`) |
| Original and rewritten file | `compare`: before/after table, references total, constraint check; exit 2 with `--strict` on a lost constraint |

Environment: `ANTHROPIC_API_KEY` enables exact token counts; `SHRINK_MODEL` picks the model for counting (default `claude-opus-5-5`). Nothing is sent anywhere unless the key is set and `--tokens` is `auto` or `api`.

## Examples

`examples/claude-md/`: a 188-line project `CLAUDE.md` with two duplicates, one contradiction, narration, a 29-line setup script and a 14-row env table. The shrunk version is 54 lines plus two reference files.
`examples/skill-md/`: a 107-line `SKILL.md` with a duplicated rule, overlapping triggers, two long example blocks and an empty section, shrunk to 45 lines plus one reference file.

Reproduce: `python3 scripts/shrink.py audit examples/claude-md/before/CLAUDE.md --tokens estimate` and `python3 scripts/shrink.py compare examples/claude-md/before/CLAUDE.md examples/claude-md/after/CLAUDE.md --tokens estimate --md`. The committed outputs in `examples/` are checked byte-for-byte by `tests/`.

## Limits

- Heuristics work on lines and sentences. A rule split over two paragraphs, or restated with different vocabulary, is not caught as a duplicate; read the file as well.
- Contradiction detection matches "always X" against "never X" on the same words. "Use tabs" versus "indent with two spaces" is not detected.
- The constraint check compares normalised sentences. Shortening a constraint sentence counts as losing it; that is intended, keep them verbatim.
- The token estimate is a documented heuristic (`references/token-estimate.md`), it is not calibrated against any tokenizer, so treat absolute values as rough and compare only before/after numbers produced the same way; the error is larger on code and non-Latin text. Use `--tokens api` for numbers you publish.
- English phrase lists. Narration in other languages is not flagged; constraints in other languages are not protected.
- Markdown only. Does not parse YAML beyond the frontmatter boundary, HTML comments, or MDX.

## References

- `references/playbook.md`: the rewrite rules with before/after snippets and the order to apply them.
- `references/token-estimate.md`: how the estimate is computed, how far off to expect it, how to get exact counts.
