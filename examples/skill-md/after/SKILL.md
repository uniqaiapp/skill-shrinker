---
name: release-notes
description: Writes release notes from merged pull requests. Use when the user asks for release notes, a changelog entry, or "what shipped".
---

# Release notes writer

Collect merged pull requests between two tags, group them by label, write a Markdown section for `CHANGELOG.md` or a GitHub release. Needs `gh` authenticated (`gh auth status`).

## When to use

- Release notes or a changelog entry for a version.
- What changed between two tags or commits, or since the last release.

## When not to use

- Do not use this skill to write commit messages. Use the commit-message skill instead.
- Do not use this skill for internal sprint reports; it only looks at merged pull requests.

## Steps

1. Previous tag: `git describe --tags --abbrev=0 HEAD^`, unless the user gave a range.
2. Merged PRs in range: `gh pr list --state merged --search "merged:>=<date-of-previous-tag>" --json number,title,labels,author,url --limit 200`.
3. Group by label: `feat` (Added), `fix` (Fixed), `perf` (Performance), `docs` (Documentation), `chore`/`ci` (Internal). Unlabelled go to "Other"; ask the user before publishing if that group is not empty. Several labels: first in the order feat, fix, perf, docs, chore.
4. One bullet per PR: imperative verb ("Add", "Fix", "Remove"), under 100 characters, PR number at the end as a link. Never mention the author by name; the team does not do that in public notes.
5. ALWAYS put breaking changes first, in their own "Breaking" section, even if there is only one.
6. Present the draft. Do not create the GitHub release yourself; the user publishes.

## Format

- `## [1.4.0] - 2026-03-02`, then `### Breaking`, `### Added`, `### Fixed`, `### Performance`, `### Documentation`, `### Internal`; omit empty sections.
- Do not include pull requests that only bump dependencies unless the user asks.
- Keep the whole section under 60 lines; if it is longer, collapse "Internal" into one line with a count.
- Full example: [references/example-output.md](references/example-output.md).

## Edge cases

- No previous tag: start at the first commit and say so in the notes.
- If `gh` is not authenticated, stop and tell the user; do not try to log in.
- More than 200 PRs: ask whether to split the release.
- Notes in another language: bullets in that language, headings in English.

## Related

commit-message (commit message for staged changes), pr-description (PR description from a diff).
