# CAPA-Content-002 — Deliverable Rendering & Title Integrity (Briefing + Article Pipelines)

**Date:** 2026-06-05
**Status:** CLOSED — All corrective and preventive actions implemented
**Raised by:** Steven Tran (direct feedback — "clunky" briefing; broken edit-progress UX; garbled title)
**Priority:** P0 — Client-facing quality failure across multiple deliverable surfaces

---

## Problem Statement

Six defects surfaced across two deliverable pipelines (Daily Briefing, MedTech Meridian articles) and the shared Review UI, all degrading outputs below the Big 4 / management-consultant standard required of every Latitude deliverable.

**Daily Briefing (rendering + template):**
1. Citations rendered as raw mojibake — `[FDA Alert]` literal text followed by a bare `http://…` URL — because the markdown renderer had no link case.
2. Duplicate stacked H1 titles (auto-header title + model-emitted `# BRIEFING:` line).
3. The review label `Alpha — Steve Review Required` leaked into the body as a stray bold line instead of the metadata badge.
4. Final item truncated mid-URL — model hit the `max_tokens` cap.

**Article pipeline (title integrity):**
5. A stray foreign-script token (`審查`, CJK for "review") was injected into the article title, rendering as mojibake in the Review Queue header and the published-draft header while the body H1 was clean.

**Review UI (edit lifecycle):**
6. "Edit with a prompt" progress was trapped inside the preview modal — closing the preview orphaned the in-flight revision and erased all progress indication.

---

## Root Cause Analysis (5-Why)

| # | Why | Finding |
|---|-----|---------|
| 1 | Why do citations render as raw URLs? | `renderInline` in `App.jsx` handled bold/italic/code but had **no markdown-link case**; the `C.ocean` "links" color was defined but never wired. Affects *every* deliverable view sharing `MarkdownView`, not just briefings. |
| 2 | Why two titles / a stray label? | `save_briefing` prepends a title + has no `status` frontmatter, while the generation prompt didn't forbid the model emitting its own title/label — so both appeared. |
| 3 | Why was the briefing truncated? | `max_tokens=900` was below the worst-case output once the model also spent tokens on the redundant title/label. |
| 4 | Why did a CJK token reach a client-facing title? | LLM artifact in the generated title field; `content_agent.save_draft` wrote `topic['title']` verbatim with **no sanitization** before it flowed to frontmatter, slug, and `review_queue`. |
| 5 | Why did edit progress vanish on close? | Edit state (`editing`, `editMsg`) lived inside the `ReviewViewer` modal; closing unmounted it and orphaned the request. No state was lifted to the persistent queue. |
| 6 | Why did all of these persist? | No rendering-invariant checks or title-hygiene guard between generation and the client-facing surface; defects only caught by Steven on visual inspection. |

---

## Corrective Actions (implemented)

| # | Action | File | Status |
|---|--------|------|--------|
| CA-1 | Add markdown-link + bare-URL rendering to `renderInline` using the designated `C.ocean` link color | `ui/frontend/src/App.jsx` | ✓ Done |
| CA-2 | Forbid the model emitting its own title/`BRIEFING:` line; move review label to `status:` frontmatter badge | `agents/briefing_agent.py` | ✓ Done |
| CA-3 | Raise briefing `max_tokens` 900 → 1400 to prevent truncation | `agents/briefing_agent.py` | ✓ Done |
| CA-4 | Rewrite 2026-06-05 briefing to the corrected format (single title, badge, inline links, complete final item) | `briefings/2026-06-05_briefing.md` | ✓ Done |
| CA-5 | Add `clean_title()` foreign-script guard; apply to title before frontmatter/slug/review-queue | `agents/content_agent.py` | ✓ Done |
| CA-6 | Correct the live corrupted title in draft frontmatter + `review_queue` record (id 15) | draft `.md` + `memory/latitude_memory.db` | ✓ Done |
| CA-7 | Lift edit lifecycle to `ReviewView`; show live "Revising…/✓ Revised/✕ Failed" badge on the queue item; allow closing the preview mid-edit; disable approve/reject while editing | `ui/frontend/src/ReviewView.jsx` | ✓ Done |

---

## Preventive Actions (implemented)

| # | Action | File | Status |
|---|--------|------|--------|
| PA-1 | Rendering-invariant added to the Autonomous QA Protocol: after any `renderInline`/`MarkdownView` change, regress links/bold/frontmatter across all views sharing the renderer (Briefing, Content, HR, M&A, ISO) | `CLAUDE.md` | ✓ Done |
| PA-2 | Title-hygiene rule recorded: generated titles carry no non-Latin script and must match the deliverable H1; enforced by `clean_title()` | `CLAUDE.md` + `content_agent.py` | ✓ Done |
| PA-3 | Canonical title now **derived from the body H1** via `title_from_body()` (falls back to cleaned generated title) — header and queue title can no longer diverge, and the intended word is preserved rather than stripped | `agents/content_agent.py` | ✓ Done |
| PA-4 | `clean_title` / title-from-H1 / shared-renderer invariants documented under Content Standards + QA Protocol | `CLAUDE.md` | ✓ Done |

---

## Verification

- Frontend (`vite build`): exit 0, no errors (both `App.jsx` and `ReviewView.jsx` changes).
- `content_agent.py`: `py_compile` clean; `clean_title` strips CJK while preserving em-dashes and curly quotes (unit-checked against the actual corrupted string).
- Live data: briefing renders single title + badge + clickable citations; corrupted article title corrected in both draft and DB.

---

## Notes / Residual Risk

Resolved. `clean_title` (CA-5) remains as a defense-in-depth scrub, but PA-3 (`title_from_body`) is now the primary control: the canonical title is the article's own H1, so a stray token can neither reach the header nor diverge the queue title from it, and the reader-intended wording is preserved. Verified end-to-end against the original corrupted string ("…Until審查 Day" → "…Until Review Day").

*Alpha — Steve Review Required*
