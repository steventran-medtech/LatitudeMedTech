# Changelog

All notable changes to **Athena** (the Latitude MedTech AI Operating System) are
recorded here. The format is based on [Keep a Changelog](https://keepachangelog.com/),
and Athena follows [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.

- **MAJOR** — incompatible or sweeping changes to how Athena works.
- **MINOR** — new capabilities added in a backward-compatible way.
- **PATCH** — bug fixes and small refinements.

While Athena is in **alpha** (`0.x`), the major version stays at `0` and each
new batch of features bumps the minor version. The single source of truth for
the *current* version is [`VERSION.json`](VERSION.json); this file is the human
record of what changed between each version. Keep them in lock-step — see
[`ops/release.ps1`](ops/release.ps1) and the "Releasing a version" section below.

## How to cut a new version

1. Move everything under **[Unreleased]** into a new dated version heading.
2. Run `ops/release.ps1 -Version <x.y.z>` to stamp `VERSION.json` (date + version)
   and create a matching git tag (`v<x.y.z>`).
3. Commit the changelog + `VERSION.json` together.

---

## [Unreleased]

_Changes landed on `main` but not yet stamped into a numbered release go here._

---

## [0.5.0] — 2026-06-05 · "Torrey Pines"

The first formally versioned release of Athena. This baseline captures the app as
it stands after the marketing, voice, and briefing work, and introduces in-app
version tracking so every future change is visible from the dashboard.

### Added
- **In-app version display.** The sidebar now shows the running version; clicking
  it opens an About panel with the full changelog.
- `VERSION.json` as the canonical source of truth for the current version, plus
  this `CHANGELOG.md` and an `ops/release.ps1` helper for cutting releases.
- `GET /api/version` backend endpoint serving the current version and changelog.
- Marketing agent integrated into the Athena UI and voice flow, with a brand
  identity package and an 18-slide sales deck.
- Claude Haiku tool-use classifier for voice intent detection (replacing the
  brittle regex-based intent matching).

### Changed
- Daily Briefing supports same-day focused re-runs.
- Review Queue gained an edit-prompt step and cleaner rendering.

### Fixed
- Voice loop stability and silent transcript correction; tab no longer switches
  away mid-conversation when an agent is triggered.

## [0.4.0] — 2026-06-04 · "Marketing"

### Added
- Marketing agent, full brand identity package, and an 18-slide sales deck.
- Today/yesterday toggle for the hourly token chart on the Dashboard.

### Changed
- HR dashboard roster expanded to include `eu_mdr` and `hr`, with a
  day-selectable timeseries.

## [0.3.0] — 2026-06-03 · "Workforce"

### Added
- Per-agent skill / knowledge-base profiles plus a firm-wide master profile,
  surfacing skill accumulation on the Workforce dashboard.
- Figure-rendering helpers for branded Word deliverables (matplotlib + docx).

### Fixed
- Workforce dashboard, review viewer, agent-run UI, and deliverable routing.

## [0.2.0] — 2026-06-02 · "Foundation"

### Added
- Canonical path configuration: all agents route through `ATHENA_ROOT`.
- Version-control discipline documented in `CLAUDE.md`.

### Changed
- Stopped tracking the runtime SQLite database in git (kept local only).

## [0.1.0] — 2026-06-02 · "Genesis"

### Added
- Initial Latitude MedTech / Athena codebase: FastAPI backend, React + Vite
  desktop UI, agent runners, voice bridge, and the knowledge base.

[Unreleased]: https://github.com/steventran-medtech/LatitudeMedTech/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/steventran-medtech/LatitudeMedTech/releases/tag/v0.5.0
[0.4.0]: https://github.com/steventran-medtech/LatitudeMedTech/releases/tag/v0.4.0
[0.3.0]: https://github.com/steventran-medtech/LatitudeMedTech/releases/tag/v0.3.0
[0.2.0]: https://github.com/steventran-medtech/LatitudeMedTech/releases/tag/v0.2.0
[0.1.0]: https://github.com/steventran-medtech/LatitudeMedTech/releases/tag/v0.1.0
