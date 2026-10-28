<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="skill-shrinker by UniqAI" src="assets/banner.svg" width="1280" height="320">
</picture>

[![License: MIT](https://img.shields.io/badge/license-MIT-d1fe17?style=flat-square&labelColor=0d0f12)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d1fe17?style=flat-square&labelColor=0d0f12)](#install)
[![Cursor](https://img.shields.io/badge/Cursor-rules-d1fe17?style=flat-square&labelColor=0d0f12)](#install)
[![Codex](https://img.shields.io/badge/Codex-AGENTS.md-d1fe17?style=flat-square&labelColor=0d0f12)](#install)
[![Made by UniqAI](https://img.shields.io/badge/made_by-UniqAI-fdfc07?style=flat-square&labelColor=0d0f12)](https://uniqai.app/?utm_source=github&utm_medium=readme&utm_campaign=skill-shrinker)

# skill-shrinker: compress SKILL.md, AGENTS.md and Cursor rules

**Shrink any SKILL.md or agent instruction file: measures size, moves long material to references, keeps the triggers intact.**

[Quickstart](#quickstart) · [How it works](#how-it-works) · [Examples](#examples) · [Install](#install) · [FAQ](#faq)

</div>

English · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

skill-shrinker compresses `CLAUDE.md`, `AGENTS.md`, `SKILL.md` and `.cursor/rules` files so Claude Code, Cursor and Codex load fewer tokens per turn. It is a skill (the rewrite procedure) plus one dependency-free Python script that finds duplicate rules, contradictions, narration, long examples and dead sections, reports tokens before and after, and checks that every MUST / NEVER / ALWAYS / DO NOT sentence survived the rewrite. Every instruction stays; the padding goes.

| **Audit with line numbers** | **Rewrite by rule, not by taste** | **Prove nothing was lost** |
|:---|:---|:---|
| Duplicates, near-duplicates, contradictions, filler phrases, code blocks over 15 lines, sections over 40 lines, empty sections. | Eleven ordered rules: constraints verbatim, merge overlaps, narration out, one example per concept, rare detail into `references/`. | `compare` prints the before/after table and lists every constraint sentence as kept, moved to references, or lost. `--strict` fails CI on a loss. |

## Quickstart

```bash
git clone https://github.com/uniqaiapp/skill-shrinker ~/.claude/skills/skill-shrinker
python3 ~/.claude/skills/skill-shrinker/scripts/shrink.py audit CLAUDE.md
```

You get a list of findings with line numbers and a size line. Then in Claude Code: `/skill-shrinker CLAUDE.md` (or just "this CLAUDE.md is too long") and the skill rewrites it next to the original, runs `compare`, and reports what moved, what was removed and what contradicts what.

## Demo

<img alt="skill-shrinker demo: audit of a 188-line CLAUDE.md, then compare before and after" src="assets/demo.svg" width="820">

The transcript is a shortened run of the commands in [`examples/README.md`](examples/README.md) on `examples/claude-md/`.

## How it works

1. **Measure.** `shrink.py report FILE` prints lines, words, chars and tokens. Tokens are exact (Anthropic `count_tokens`, model named in the header) when `ANTHROPIC_API_KEY` is set, otherwise a local estimate that is labelled as such. Nothing leaves the machine unless the key is set; `--tokens estimate` forces offline.
2. **Audit.** `shrink.py audit FILE` works on lines and sentences: exact duplicates after normalisation, near-duplicates by word overlap, contradictions ("always X" against "never X" on the same words), a list of narration phrases, long code blocks, long sections, long tables, empty sections, repeated headings, and the constraint sentences that must survive.
3. **Rewrite.** The agent (or you) applies the rules in [`SKILL.md`](SKILL.md): constraints byte-identical, duplicates out, overlaps merged, contradictions reported rather than silently resolved, narration deleted, prose turned into imperatives, one example per concept, setup and troubleshooting moved to `references/` with a one-line pointer, frontmatter and trigger phrases untouched.
4. **Verify.** `shrink.py compare BEFORE AFTER` prints the table, adds up the referenced files so the saving is honest about where the bytes went, and checks every constraint. Lost ones are printed with `LOST:`; `--strict` exits 2.

On the included sample (`examples/claude-md`, estimated tokens, command in [`examples/README.md`](examples/README.md)):

|  | before/CLAUDE.md | after/CLAUDE.md | change |
|:--|--:|--:|--:|
| lines | 188 | 54 | -71% |
| words | 1,345 | 486 | -64% |
| chars | 8,413 | 3,169 | -62% |
| tokens (estimate) | 2,468 | 979 | -60% |

The two reference files that absorbed the setup script and the handler example add up to 998 estimated tokens, so the whole set is 20% smaller than the original and the part loaded on every turn is 60% smaller. 23 constraint sentences in, 21 kept verbatim, 1 only in references, 1 lost on purpose (the losing side of a tabs-vs-spaces contradiction). These numbers are what `scripts/shrink.py` prints on the files in `examples/`; the tests fail if they drift.

```
scripts/shrink.py   report | audit | compare      Python 3.9+, stdlib only
SKILL.md            the procedure and the eleven rewrite rules
references/         playbook with before/after snippets, token estimate notes
examples/           two before/after pairs with committed outputs
```

## Examples

<details>
<summary><b>A rule buried in narration: before → after</b></summary>

**Before**

```text
Obviously errors should be handled. Wrap external calls (Stripe, social APIs) in `try/catch` and convert
failures into the `AppError` class from `apps/web/lib/errors.ts`. Never swallow an error silently: either
rethrow, or log it with `logger.error` and return a typed failure.
```

**After**

```text
- Errors: wrap external calls (Stripe, social APIs) in `try/catch`, convert to `AppError`
  (`apps/web/lib/errors.ts`). Never swallow an error silently: either rethrow, or log it with
  `logger.error` and return a typed failure.
```

The constraint sentence is byte-identical; `compare` finds it. The narration ("Obviously ... should be handled") is gone.

</details>

<details>
<summary><b>A contradiction, reported not guessed</b></summary>

```text
CONTRADICTIONS               1
  L39 vs L185
      - Always use tabs for indentation.
      - Never use tabs for indentation.
```

The skill does not pick a side. It lists the pair and asks; in an unattended run it keeps the one supported by the surrounding evidence and `compare` shows the other as `LOST:` so the decision is on record.

</details>

<details>
<summary><b>Overlapping triggers in a SKILL.md</b></summary>

**Before**

```text
- The user asks what changed between two tags.
- The user wants to know what shipped since the last release.
- The user asks what changed between two tags or two commits.
```

**After**

```text
- What changed between two tags or commits, or since the last release.
```

Union of the trigger words preserved, two lines fewer. Full pair: [`examples/skill-md/`](examples/skill-md/).

</details>

## Install

Works with every agent that reads instruction files. Pick yours. Requirements: Python 3.9+. No packages to install.

<details open>
<summary><b>Claude Code</b> (as a skill)</summary>

```bash
git clone https://github.com/uniqaiapp/skill-shrinker ~/.claude/skills/skill-shrinker
```
Then in Claude Code type `/skill-shrinker` or just describe the task; the skill triggers on its description.
Project-local instead of global: clone into `.claude/skills/skill-shrinker` inside your project.

Agent Skills directory: `npx skills add uniqaiapp/skill-shrinker`.

</details>

<details>
<summary><b>Claude Code</b> (as a plugin, once the uniqaiapp marketplace is published)</summary>

```
/plugin marketplace add uniqaiapp/skills
/plugin install skill-shrinker@uniqaiapp
```

</details>

<details>
<summary><b>Cursor</b></summary>

Copy [`SKILL.md`](SKILL.md), `scripts/` and [`.cursor/rules/skill-shrinker.mdc`](.cursor/rules/skill-shrinker.mdc) into your project. The rule file embeds the skill.

</details>

<details>
<summary><b>Codex / any agent that reads AGENTS.md</b></summary>

Copy `SKILL.md` and `scripts/` into `.agents/skills/skill-shrinker/` and add the snippet from [`codex/INSTRUCTIONS.md`](codex/INSTRUCTIONS.md) to your `AGENTS.md`.

</details>

<details>
<summary><b>Without an agent</b></summary>

Every command runs standalone: `python3 scripts/shrink.py --help`. The rules in `SKILL.md` read fine as a checklist for a human editor.

</details>

## FAQ

<details>
<summary><b>Does it edit my file automatically?</b></summary>

The script never writes to your files; it prints. The skill writes the rewrite to a new file next to the original (for example `CLAUDE.shrunk.md`) unless you ask for in-place, so you always have a diff.

</details>

<details>
<summary><b>How accurate is the token number?</b></summary>

With `ANTHROPIC_API_KEY` set it is the exact count from Anthropic's `count_tokens` for the model named in the output (default `claude-opus-5-5`, override with `SHRINK_MODEL`). Without a key it is a documented heuristic ([`references/token-estimate.md`](references/token-estimate.md)), it is not calibrated against any tokenizer, so treat absolute values as rough, compare only numbers produced the same way, and expect larger error on code and non-Latin text. Every table says `estimate` when that is what it is.

</details>

<details>
<summary><b>Will it change what my instructions mean?</b></summary>

That is what the constraint check is for. Every sentence with MUST, NEVER, ALWAYS, DO NOT and similar words is matched between the original and the rewrite after stripping filler; shortening one counts as losing it. Soft rules without those words are not protected by the script, so read the diff. The skill tells the agent to list every removed line that was not an exact duplicate.

</details>

<details>
<summary><b>Why not just delete the file and start over?</b></summary>

Sometimes that is right, and the audit helps there too: the constraint list is the part you must carry over. Most files are not that bad; they have a core of real rules wrapped in explanations and examples that were useful once. Moving the explanations to `references/` keeps them for the day they are needed again, at zero cost on every other turn.

</details>

<details>
<summary><b>Does it work on non-English files?</b></summary>

Size and duplicate detection work on any language. The narration phrase list and the constraint keywords are English, so Russian or German rules are neither flagged nor protected. Pull requests adding phrase lists are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).

</details>

## Related

- [token-diet](https://github.com/uniqaiapp/token-diet): cut prompt and context tokens without losing meaning, measurable rules, a stdlib estimator, and before/after examples. skill-shrinker is the same idea applied to the instruction files themselves.
- [model-router](https://github.com/uniqaiapp/model-router): pick the cheapest model that can do the job, a rule table and a stdlib script that routes tasks by type, length and risk.
- [deslop-ru](https://github.com/uniqaiapp/deslop-ru): strip AI-sounding filler from Russian text, a skill plus a stdlib script that flags and rewrites the usual tells.

## Contributing

Issues and pull requests are welcome. Keep changes small and include a before/after example in the PR description.
See [CONTRIBUTING.md](CONTRIBUTING.md) for the local checks (`python3 tests/run.py`, no dependencies).

## License

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub>Made by <a href="https://uniqai.app/?utm_source=github&utm_medium=readme&utm_campaign=skill-shrinker">UniqAI</a> — Kling 3.0, Veo 3, Flux, Nano Banana and GPT-5/Claude/Gemini/Grok in one app. We wrote this to keep our own skills short.</sub>

</div>
