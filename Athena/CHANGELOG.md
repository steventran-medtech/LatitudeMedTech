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

## [0.5.2] — 2026-06-06 (E2E Architecture Alignment)

### Fixed
- **BUG-1** Intro/exit voice now speaks via Kokoro (bf_emma) — `_speak_phrase` and `_speak_phrase_greeting` in server.py delegate to `voice_bridge._speak_sentence` instead of using the Windows SAPI voice
- **BUG-2** Response latency reduced: `SILENCE_DURATION` 0.8→0.65 s; post-response cooldown 1.0→0.5 s + mic flush 1.5→0.75 s; `_correct_transcript` skipped for confident (non-low-conf) transcripts
- **BUG-3** Deliverable completion announcements no longer cut off: removed duplicate frontend `fetch('/api/voice/notify', ...)` from `agent_done` handler; server-side `run_agent()` batching is the single notification path
- **BUG-4** Documents hub now shows only Gate-10-approved deliverables; `list_documents()` cross-references `review_queue` approved set
- **BUG-5 / G-08** `deck_agent.py` now calls `submit_for_review()` after saving PPTX; iso_coach_agent already had Gate 10 in CLI path (confirmed)
- **BUG-6** App.jsx shows a full-screen loading overlay with animated progress bar from launch until the main WebSocket connects

### Added
- `memory.get_approved_reviews()` — returns all review_queue rows with `status='approved'`
- `kb_annotations.client_id` column + migration for per-client annotation scoping (G-06)
- Gate 3 confidence scoring in `sow_agent.py` and `regulatory_strategy_agent.py` (G-01)
- Phase 2C design inputs: UN-024/025/026/027 in DC-002 v1.8, DC-004 v1.9, dc_verify.py (66 tests, 0 failures)
- Phase 2C agent roster added to CLAUDE.md v13

## [Unreleased]

_Changes landed on `main` but not yet stamped into a numbered release go here._

### Added
- **Voice PTT — Press to Listen (UN-020-V / DI-020-V):** Manual push-to-talk button added to
  the Voice HUD. When Athena is in Listening state a "Press to Listen" button appears below the
  orb; clicking it calls `POST /api/voice/listen`, which sets `_ptt_event` to bypass wake-word
  detection and jump straight to recording. Handles both the pre-listen race (event checked before
  `_listen_for_wake` blocks) and mid-listen race (event checked per audio chunk inside the function).
  `triggerListen` added to `useVoiceSession` hook; PTT endpoint added to `qa_test.py` route list.

### Fixed
- **Google Drive connect response key (C4):** `FileViewer.jsx` `connectDrive` was checking
  `data.ok` but `server.py` now returns `{started: true}` (async OAuth refactor). Fixed to
  `data.started`. Separately, `loadView()` was called immediately before the background OAuth
  thread completed; replaced with a 2-second polling loop against `GET /api/google/auth-status`
  (up to 120 s) that calls `loadView()` only once `configured=true`. Button label updated to
  "Complete authorization in browser…" while polling.
- **PTT rejection feedback (C5):** `triggerListen` now reads the `POST /api/voice/listen`
  response; if `ok=false` (server busy/not-listening), a `pttRejected` flag is set for 1.5 s
  and a "Busy — try again" label appears below the PTT button. Previously the rejection was
  silently discarded with no user feedback.

- **Client creation (C1 — DI-018-A):** `POST /api/clients` now wraps `mem.add_client()` in
  try/except and returns `{"error": "<message>"}` with HTTP 500 on database failure. Frontend
  now checks `res.ok` and surfaces the actual server error instead of the generic
  "Failed to create client." message.

### Added
- **Client intake validation (C2 — DI-018-B):** IntakeForm in `ClientsView.jsx` enforces
  required fields (Full Name, Email, Program/Tier) before submission. Each missing field
  highlights with a red border and inline error message; errors clear per-field as the user
  types. UN-018 and DI-018-A/B added to DC-001/002/003/004; `test_DI_018_A` and
  `test_DI_018_B` added to `dc_verify.py`.

### Changed
- **Splash progress bar (C3 — DI-019-A, DI-019-B):** Progress bar repositioned to the full-width
  bottom edge of the splash window (no side padding). Numeric percentage counter removed. UN-019
  and DI-019-A/B added to DC-001/002/003/004; `test_DI_019_A` and `test_DI_019_B` added to
  `dc_verify.py`.
- **Voice silence duration (C3 — DI-004-E):** `SILENCE_DURATION` reduced from 1.5 s to 0.8 s
  in both `settings.json` and `voice_bridge.py` default. Reduces Athena's post-speech pause
  by ~700 ms. Value is at the DC-006 floor (0.8 s) and remains within the safe range [0.8, 2.0].
  DI-004-E requirement statement and `test_DI_004_E` updated accordingly.

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
