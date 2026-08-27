# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning follows [SemVer](https://semver.org/).

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
