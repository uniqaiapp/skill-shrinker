---
name: release-notes
description: Writes release notes from merged pull requests. Use when the user asks for release notes, a changelog entry, or "what shipped".
---

# Release notes writer

Welcome to the release notes skill. In this document we will explain, step by step, how to produce release notes for a tagged version of a project from the pull requests merged since the previous tag. It is important to follow the steps in order. Let's begin.

## Overview

Basically, the skill does three things: it collects the merged pull requests between two tags, it groups them by type, and it writes a Markdown section that can be pasted into `CHANGELOG.md` or a GitHub release. As you can see, it is not complicated, but there are a few details that matter.

## When to use

- The user asks for release notes for a version.
- The user asks what changed between two tags.
- The user asks for a changelog entry.
- The user wants to know what shipped since the last release.
- The user asks what changed between two tags or two commits.

## When not to use

- Do not use this skill to write commit messages. Use the commit-message skill instead.
- Do not use this skill for internal sprint reports; it only looks at merged pull requests.

## Steps

Please note that all of the steps below assume `gh` is installed and authenticated. Make sure to check that first with `gh auth status`.

1. Find the previous tag: `git describe --tags --abbrev=0 HEAD^`. If the user gave an explicit range, use that instead.
2. List merged pull requests in the range: `gh pr list --state merged --search "merged:>=<date-of-previous-tag>" --json number,title,labels,author,url --limit 200`.
3. Group the pull requests by label: `feat` (Added), `fix` (Fixed), `perf` (Performance), `docs` (Documentation), `chore` and `ci` (Internal). Pull requests without a label go to "Other"; ask the user before publishing if that group is not empty.
4. Write one bullet per pull request: imperative sentence, under 100 characters, followed by the pull request number as a link. Never mention the author by name; the team does not do that in public notes.
5. ALWAYS put breaking changes first, in their own "Breaking" section, even if there is only one.
6. Present the draft to the user. Do not create the GitHub release yourself; the user publishes.

Remember that steps 1 and 2 are the only ones that touch the network. Everything after that is pure writing.

## Formatting rules

- Headings: `## [1.4.0] - 2026-03-02` then `### Breaking`, `### Added`, `### Fixed`, `### Performance`, `### Documentation`, `### Internal`.
- Bullets start with a verb in the imperative: "Add", "Fix", "Remove", not "Added" or "Adds".
- One bullet per pull request, under 100 characters, pull request number at the end as a link.
- Never mention the author by name.
- Do not include pull requests that only bump dependencies unless the user asks.
- Never mention the author by name.
- Keep the whole section under 60 lines; if it is longer, collapse "Internal" into one line with a count.

## Example output

Here is a complete example of what the output should look like for a mid-sized release. Feel free to use it as a template.

```markdown
## [1.4.0] - 2026-03-02

### Breaking
- Drop Node 16 support; the minimum is now Node 18 ([#412](https://github.com/example/app/pull/412))

### Added
- Add CSV export to the reports page ([#398](https://github.com/example/app/pull/398))
- Add `--dry-run` flag to the deploy command ([#402](https://github.com/example/app/pull/402))
- Add keyboard shortcuts for the editor ([#405](https://github.com/example/app/pull/405))
- Add Finnish translation ([#407](https://github.com/example/app/pull/407))

### Fixed
- Fix crash when the workspace name contains an emoji ([#399](https://github.com/example/app/pull/399))
- Fix timezone offset in the scheduler for half-hour zones ([#401](https://github.com/example/app/pull/401))
- Fix flaky retry on webhook delivery ([#404](https://github.com/example/app/pull/404))
- Fix broken link in the onboarding email ([#406](https://github.com/example/app/pull/406))
- Fix double submit on slow connections ([#409](https://github.com/example/app/pull/409))

### Performance
- Cache the workspace list for 60 seconds ([#400](https://github.com/example/app/pull/400))
- Batch the queue poll into one query ([#403](https://github.com/example/app/pull/403))

### Documentation
- Document the webhook retry policy ([#408](https://github.com/example/app/pull/408))

### Internal
- 7 internal changes (CI, dependencies, refactors)
```

And here is a second example, for a small patch release, so that you can see how the headings collapse when sections are empty:

```markdown
## [1.4.1] - 2026-03-09

### Fixed
- Fix the CSV export encoding on Windows ([#415](https://github.com/example/app/pull/415))
- Fix a typo in the settings page ([#416](https://github.com/example/app/pull/416))
```

## Edge cases

- If there is no previous tag, use the first commit as the start of the range and say so in the notes.
- If `gh` is not authenticated, stop and tell the user; do not try to log in.
- If the range contains more than 200 pull requests, ask the user whether to split the release.
- If a pull request has several labels, use the first one in the order feat, fix, perf, docs, chore.
- If the user asks for notes in another language, write the bullets in that language but keep the headings in English.

## Troubleshooting

## Related skills

- commit-message: writes a commit message for staged changes.
- pr-description: writes a pull request description from a diff.
