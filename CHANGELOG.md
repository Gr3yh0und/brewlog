# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning follows [SemVer](https://semver.org/).

## [Unreleased]

## [1.0.3] — 2026-09-26

- (no notable changes recorded)

## [1.0.2] — 2026-09-26

- (no notable changes recorded)

## [1.0.1] — 2026-09-26

### Added
- Onboarded onto `WEBAPP_PROJECT_STANDARD.md`: `homelab.yml`, `VERSION`, this changelog,
  `deploy.config.example`, `.claude/skills/{deploy,rollback}`, Dependabot.
- `deploy/rollback.py`: snapshots the exact bytes of every deploy before upload, keeps the last 5,
  `--rollback[=N]` re-uploads a snapshot verbatim.
- `local` publish target (`deploy/deploy.sh`/`.ps1` `[local|public|both]`): publishes to
  `WWW_ROOT/brewlog/releases/<VERSION>/` and flips the `current` symlink
  (`WEBAPP_PROJECT_STANDARD.md` §14B). Target defaults to `public`, unchanged from before.
  `deploy/rollback.py publish-local`/`list-local`/`rollback-local[=N]` implement the mechanics;
  rollback flips `current` back, no re-copy.
- Wired to the shared `/deploy` skill: `deploy/build.sh` assembles `dist/`, `deploy.config` sets
  `local` + `public` targets (public reuses the FTP uploader).
- Secrets are read from `/etc/homelab/brewlog.env` when readable (override with `BREWLOG_ENV`),
  else the repo `.env`.
### Fixed
- `deploy/deploy.sh`: the public (FTP) upload now sends `logo/logo.svg`, matching `deploy.ps1`.
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
