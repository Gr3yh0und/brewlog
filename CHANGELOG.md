# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning follows [SemVer](https://semver.org/).

## [Unreleased]

No `/deploy` skill exists for this repo yet (bespoke FTP deploy path, `WEBAPP_PROJECT_STANDARD.md`
§9), so nothing here has been tagged or versioned — hand-maintained until it does.

### Added
- Onboarded onto `WEBAPP_PROJECT_STANDARD.md`: `homelab.yml`, `VERSION`, this changelog,
  `deploy.config.example`, `.claude/skills/{deploy,rollback}`, Dependabot.
- `deploy/rollback.py`: snapshots the exact bytes of every deploy before upload, keeps the last 5,
  `--rollback[=N]` re-uploads a snapshot verbatim.

### Fixed
- `deploy/rollback.py`: a pruned bare release name could be reused by a later deploy and get
  mispruned in turn — in the worst case, deleted in the same call that created it. Release
  directories now carry a monotonic sequence number that's never reused.

### Changed
- CI actions bumped to their latest majors (`actions/checkout` 4→7, `actions/setup-python` 5→7).

## [1.0.0] - 2026-06-24

Initial public release: a static web frontend for a Kleiner Brauhelfer 2 home brewery database.

### Added
- Beer catalog with filtering by status/style, radar charts, KPIs, and dark mode.
- Detail pages with full recipe breakdown: grain bill, hops, mash plan, fermentation timeline.
- BeerJSON + BeerXML export from the KBH2 SQLite database.
- Printable DIN A4 SVG bottle labels with QR codes, radar charts, and brewery logo.
- Optional brew-day and fermentation charts from InfluxDB (iSpindel + MQTT kettle sensors).
- Multilingual UI (DE, EN, FR, IT, ES, NL, DA, CS).
- FTP deploy scripts (`deploy/deploy.sh`, `deploy/deploy.ps1`).
- Sample data generator for previewing the site without a real KBH2 database.
- CI running the test suite on every push/PR.
