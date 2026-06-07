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

### CO-014 (fix) — C1 Corrective: Remove duplicate FileViewer import in ReviewView.jsx (DI-002-J)

- **ReviewView.jsx**: Removed duplicate `import FileViewer from "./FileViewer.jsx"` on line 8; duplicate caused a Vite build failure that prevented the Document Queue from loading and caused Chrome to open to the error overlay.
- **DI-002-J** (P0, VERIFIED): New regression test `test_DI_002_J` in `dc_verify.py` asserts no duplicate import declarations in `ReviewView.jsx`.

### CO-013 (splash-done-signal) — UN-019: Splash 100% guaranteed before Chrome opens (DI-019-L)

- **start_splash.hta**: Added `CloseSplash` sub that writes `.athena_splash_done` before `window.close()`; `Tick` sub now calls `window.setTimeout "CloseSplash"` instead of `window.setTimeout "window.close()"`.
- **start_athena.ps1**: Replaced `Start-Sleep -Milliseconds 2500` race condition with a 200ms polling loop waiting for `.athena_splash_done` (max 6s timeout); flag cleaned up at startup.
- **DI-019-G** verification method updated: gap now signal-bounded to < 400ms.
- **dc_verify.py**: `test_DI_019_G` updated; `test_DI_019_L` (P0) added; 109/109 PASSED.

### CO-012 — UN-007 + UN-002: Tab rename + AGENT_TAB routing fix

### Changed
- **UN-007, UN-002 / CO-012** Renamed "Content Drafts" tab to "MedTech Meridian Drafts" (NAV_ITEMS + ContentView h2); fixed AGENT_TAB — coaching_brief→"coaching", consulting_agent/ma_intelligence_agent/sow_agent/regulatory_strategy_agent→"queue"; fixed WorkQueuePanel awaiting_review routing target from "review"→"queue" (DI-007-F, DI-002-H, DI-002-I)

### CO-011 — UN-034 Engineering Process Integrity (Formal Registration + Test Correction)

- **DI-034-A (corrected)**: `test_DI_034_A` rewritten to verify `CLAUDE.md` contains the co-commit rule phrase "must also update at least one design control document" — prior test incorrectly checked `qms_simulator_agent.py` for `submit_for_review(` (CO-010 artifact)
- **DI-034-B–F (confirmed VERIFIED)**: Auth Centralization Standard, voice_bridge.py Boundary, Progress Bar Specification, App.jsx Responsibility Scope, CLAUDE.md Update Policy — all CLAUDE.md section checks confirmed correct
- **DC-004 v2.9 coverage summary corrected**: 34 UNs, 116 DIs total, 100 VERIFIED, 8 PARTIAL, 8 OPEN; stale TG-009/010/011 entries collapsed to CLOSED
- **DC-005 v2.0**: DI-034-A–F test procedure entries added (check phrase / section presence in CLAUDE.md; fail action documents remediation step)
- **DC-006**: CO-011 formally registered; Next available → CO-012

### CO-010 — UN-033 Voice Latency + UN-034 Engineering Integrity + UN-030 Publication Format

- **DI-033-A/B/C (VERIFIED)**: `_voice_loop` shares one `sd.InputStream` per query cycle; `_listen_for_wake` and `_record_query` accept `stream` parameter — eliminates 200–500 ms Windows MME close/reopen gap after wake detection
- **DI-030-D (VERIFIED)**: `PUBLICATION_FORMAT_GUIDE` dict added to `AgentBase` class in `agent_base.py`; `system_prompt()` injects publication-style directive per agent name (8 styles: content/briefing/consulting/ma/marketing/iso/deck/coaching)
- **DI-030-E (VERIFIED)**: `## Output Format Standard` section added to all 8 production agent persona files in `.claude/agents/`
- **DI-034-A–F (VERIFIED)**: Engineering Integrity Standards section added to `CLAUDE.md` — co-commit rule, auth centralization, voice_bridge.py audio boundary, progress bar spec, App.jsx scope, CLAUDE.md update policy
- CAPA-DC-002.md opened and closed: DI-033-A/B/C tests re-registered in dc_verify.py


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

### Fixed
- **CO-004 / DI-019-H:** Splash progress bar could freeze indefinitely at any whole-number percentage (97% and 99% both observed). Root cause: `PollChromeReady` asymptotically converges `targetVal` to a hard cap of 97; once `stepVal` catches up, `Tick`'s `If stepVal < targetVal` branch is permanently false. A ceiling-based keep-alive merely moves the freeze (e.g., to 99%). Fix: `ElseIf Not readyToClose Then stepVal = stepVal + 0.05` with `If stepVal >= 99.5 Then stepVal = targetVal` wrap -- bar cycles 97->98->99->wrap->97->... at 320 ms/pt; no ceiling means no freeze at any whole number. `test_DI_019_H` expanded from 5 to 9 checks, adding keep-alive presence, no-blocking-ceiling, floor rate, and wrap@99.5.

### Added
- **UN-003, UN-023 / CO-003 — RAG Reviewable Reports + Historical QARA Knowledge:** `rag_agent.py` now submits a rich Markdown ingestion report to the review queue after each run. Report includes a `## Newly Ingested Documents` table (document title/URL, category, chunk count) and a "No new documents ingested this run." fallback (DI-003-C, DI-003-D). `TAVILY_QUERIES` expanded with 7 historically-scoped entries covering FDA 1976 Medical Device Amendments, 21 CFR 820 history, ISO 13485 evolution, EU MDR/MDD history, GMP origin, CAPA history, and IMDRF/GHTF origin (DI-023-B). Non-deterministic `random.sample` rotation replaced with `tm_yday`-based day-of-year bucketing so the same date always covers the same query window (DI-023-C). Four QARA regulatory RSS sources added to `learning_sources.py["rag"]` — RAPS Regulatory Focus, Federal Register Medical Devices, IMDRF, and FDA CDRH (DI-023-B).
- **DI-019-J (C2):** Splash screen `#dots` element now cycles sequentially (`.` → `..` → `...`) via VBScript `TickDots` timer at 400 ms/state — matching Claude Code's in-progress indicator pattern. Replaces CSS `dotFlash` wave animation. `test_DI_019_J` added to `dc_verify.py`.
- **UN-030 (C2): McKinsey/Latitude Brand Formatting Standard** — Formal DC trace for cross-cutting deliverable formatting quality: DI-030-A (exec_summary in all 6 deck types, including pitch which was missing it), DI-030-B (McKinsey/Big-4 quality directive verified across all 6 deliverable agents), DI-030-C (Latitude MedTech LLC brand identity via agent_base.py). Three new `test_DI_030_A/B/C` verification tests. DC-001 v1.3 / DC-002 v2.4 / DC-003 v1.3 / DC-004 v2.4 / DC-005 v1.5 updated.

### Changed
- **DI-019-G (C3):** Splash-to-Chrome gap tightened from < 5 s to < 3 s — `start_athena.ps1` `Start-Sleep` reduced 3500 ms → 2500 ms; `test_DI_019_G` threshold updated to ≤ 2500 ms.
- **DI-019-H (C3):** Anti-stall bound now mathematically proven — `test_DI_019_H` computes `(99.5 − cap) / min_floor × 16 ms < 1000 ms` to verify bar can close from cap to 99.5% in < 1 s; DC-002 v2.1 / DC-004 v2.1 / DC-005 v1.2 updated.

### Added
- **Voice PTT — Press to Listen (UN-020-V / DI-020-V):** Manual push-to-talk button added to
  the Voice HUD. When Athena is in Listening state a "Press to Listen" button appears below the
  orb; clicking it calls `POST /api/voice/listen`, which sets `_ptt_event` to bypass wake-word
  detection and jump straight to recording. Handles both the pre-listen race (event checked before
  `_listen_for_wake` blocks) and mid-listen race (event checked per audio chunk inside the function).
  `triggerListen` added to `useVoiceSession` hook; PTT endpoint added to `qa_test.py` route list.

### Changed
- **Splash title font size (DI-019-I):** Athena `.name` title on the splash screen increased from
  100px to 101px (1pt). Applied to both `Athena/ui/start_splash.hta` (fixed value) and
  `Athena/electron/main.js` (clamp min/max bumped from 60/100px to 61/101px).

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
- **Voice silence duration (C3 — DI-004-E):** `SILENCE_DURATION` further tuned to 0.5 s in
  `settings.json` (code default 0.65 s). Requirement range updated to [0.4, 0.65] s. Reduces
  Athena's post-speech pause; `test_DI_004_E` checks the new range.

### Fixed
- **UN-028-A — Startup echo:** Athena's greeting was played via direct TTS while the mic was
  open, causing the intro phrase to be transcribed as a user command. Fix: `_speak_phrase_greeting`
  in `server.py` now routes the greeting through `_notification_queue`; the voice loop drains the
  queue before ever opening the mic, then handles cooldown normally. A 0.5 s sleep on voice loop
  startup ensures the greeting arrives before the first drain (DI-028-C, DI-028-D).
- **UN-028-B — 5-second silence wait:** `_vad_query` aggressiveness was 1, classifying ambient
  noise as speech and preventing silence from accumulating. Fix: `_vad_query` aggressiveness
  raised to 2; post-speech silence counter now uses VAD alone (RMS AND-gate removed) so the
  counter increments immediately after speech stops (DI-028-A, DI-028-B).

### Added
- **UN-029 — Audio device detection:** `_device_monitor_loop` polls the system default input
  device every 3 s. When the device changes (e.g., headphones plugged in or removed),
  `_apply_device` updates sampling parameters, `_device_changed` Event signals `_listen_for_wake`
  to break and reopen the stream with the new device, and a `device_changed` WebSocket event is
  emitted to the UI (DI-029-A, DI-029-B, DI-029-C).

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
