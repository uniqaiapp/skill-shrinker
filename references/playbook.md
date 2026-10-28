# Rewrite playbook

The eleven rules from `SKILL.md`, each with a before/after snippet. Apply them in this order: structural moves first (so line numbers from the audit stay useful for as long as possible), wording last.

## 1. Constraints stay verbatim

A constraint is any sentence with MUST, MUST NOT, NEVER, ALWAYS, DO NOT, DON'T, SHALL, REQUIRED, FORBIDDEN. Its wording is the contract. Move it, group it under a "Rules" heading, but do not reword it, and do not merge two constraints into one sentence.

Before:
```
Please remember that you MUST run `pnpm test` before every commit, it is really important.
```
After:
```
- You MUST run `pnpm test` before every commit.
```
The filler around the constraint goes; the constraint sentence itself is byte-identical. `compare` strips leading filler phrases ("remember that", "please note") before matching, so this edit passes.

## 2. Delete exact duplicates

The audit lists them with line numbers. Keep the copy in the most specific section (a rule about migrations belongs under "Database", not "Golden rules"). Delete the others, including copies that differ only in capitalisation, bullet style or backticks.

## 3. Merge near-duplicates and overlapping rules

Before:
```
- Prefer named exports over default exports.
- Use named exports; default exports make refactoring harder.
- Do not add default exports to new files.
```
After:
```
- Prefer named exports over default exports (easier refactoring); do not add default exports to new files.
```
If one of the lines is a constraint, keep that sentence verbatim and fold the others into it as a clause after a semicolon.

## 4. Report contradictions, do not resolve them silently

Before (lines 39 and 185 of the same file):
```
- Always use tabs for indentation.
- Never use tabs for indentation.
```
What to do: keep both out of the rewrite until the user answers, or, for an unattended run, keep the one that matches the surrounding evidence (a Prettier config with `useTabs: false` decides this one) and say so in the summary. `compare` will report the dropped one as LOST; that is the audit trail.

## 5. Remove narration

Narration describes the document instead of instructing. Delete the phrase and keep whatever instruction was attached.

Before:
```
In this section we will walk through the testing setup. It is worth noting that the e2e suite needs seed data.
```
After:
```
e2e needs seed data: `pnpm db:seed`.
```
Full phrase list: `FILLER` in `scripts/shrink.py`. Also delete: "Welcome", "Let's get started", "Happy coding", section intros that only restate the heading.

## 6. Prose to imperatives

Before:
```
We use TypeScript everywhere. It is important to keep the code strict, so strict mode is on and you should not add ts-ignore comments unless there is a comment explaining why.
```
After:
```
- TypeScript, `strict: true`. No `// @ts-ignore` without a comment saying why.
```
Pattern: `object/scope + rule + condition`. Drop "we", "you should", "please", "make sure to". Keep the condition; conditions are where the information is.

## 7. One example per concept, the shortest that works

Before: a 30-line full route handler in the main file.
After: the five lines that show the pattern (validate, call, shape the response), and a link: `Full handler: references/api-conventions.md`.

A second example of the same shape adds tokens and no information. If two examples differ in one detail, keep one and state the detail in a sentence.

## 8. Move rare detail out

Candidates, in order of how rarely an agent needs them on a normal turn:

| Content | Goes to |
|---|---|
| Setup from scratch, installing toolchains | `references/local-setup.md` |
| Troubleshooting lists ("if X fails, do Y") | same file, "Troubleshooting" section |
| Environment variable tables | same file, names only, never values |
| Long option or flag lists | `references/<tool>-options.md` |
| Prompt libraries, template collections | `references/prompts.md` |
| Historical decisions, "why we chose X" | `references/decisions.md` or an ADR folder |

Leave a one-line pointer in the place where the agent would look for it, with a relative link. `compare` follows those links to count the references and to find constraints that moved.

## 9. Delete empty and placeholder sections, repeated headings

A heading with nothing under it, "TBD", "coming soon", or a second "Setup" heading that says "see above". Delete; if the heading was a promise, note it in the summary so the user can decide whether to write that section.

## 10. Keep the frontmatter and the triggers

`name` and `description` are how a skill is selected; the "When to use" bullets are the long form of the same thing. Shorten the description only to meet a host limit, and never remove trigger phrases. Overlapping "When to use" bullets may be merged (rule 3), but the union of trigger words must be preserved.

Before:
```
- The user asks what changed between two tags.
- The user asks what changed between two tags or two commits.
```
After:
```
- What changed between two tags or commits, or since the last release.
```

## 11. Do not touch

Kept code blocks, URLs, file paths, command lines, version numbers, anything in backticks, and the exact text of error messages the agent is told to look for. Reformatting these changes behaviour.

## Order of work for a typical file

1. `report`, keep the numbers.
2. `audit`, read the whole file once with the findings open.
3. Rules 8, 7, 9 (move and delete big things) and write the reference files.
4. Rules 2, 3, 4 (dedupe, merge, list contradictions).
5. Rules 5, 6 (wording), checking rule 1 and 11 on every line.
6. `compare --strict`; fix every LOST line that was not a deliberate decision.
7. Summary to the user: the table, moved sections and paths, removed non-duplicate lines, open contradictions.
