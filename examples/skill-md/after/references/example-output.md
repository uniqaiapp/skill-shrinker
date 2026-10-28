# Example output

Load this when unsure about the exact shape. A mid-sized release:

```markdown
## [1.4.0] - 2026-03-02

### Breaking
- Drop Node 16 support; the minimum is now Node 18 ([#412](https://github.com/example/app/pull/412))

### Added
- Add CSV export to the reports page ([#398](https://github.com/example/app/pull/398))
- Add `--dry-run` flag to the deploy command ([#402](https://github.com/example/app/pull/402))

### Fixed
- Fix crash when the workspace name contains an emoji ([#399](https://github.com/example/app/pull/399))
- Fix timezone offset in the scheduler for half-hour zones ([#401](https://github.com/example/app/pull/401))

### Performance
- Cache the workspace list for 60 seconds ([#400](https://github.com/example/app/pull/400))

### Documentation
- Document the webhook retry policy ([#408](https://github.com/example/app/pull/408))

### Internal
- 7 internal changes (CI, dependencies, refactors)
```

A patch release keeps only the sections that have entries:

```markdown
## [1.4.1] - 2026-03-09

### Fixed
- Fix the CSV export encoding on Windows ([#415](https://github.com/example/app/pull/415))
```
