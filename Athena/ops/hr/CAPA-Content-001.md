# CAPA-Content-001 — Article Quality: Rendering Failures + Generic Output

**Date:** 2026-06-04
**Status:** CLOSED — Corrective actions implemented
**Raised by:** Steven Tran (direct feedback, multiple occurrences)
**Priority:** P0 — Client-facing quality failure

---

## Problem Statement

Generated MedTech Meridian articles are unpresentable in the current viewer:
1. YAML frontmatter metadata (`title:`, `date:`, `angle:`, `status:`, `generated_by:`) renders as body text before the article
2. H2 section headings force ALL CAPS via `textTransform: "uppercase"` — looks aggressive and amateurish
3. Article title renders as H2 (##) inheriting the uppercase style
4. Content, while sometimes substantive, inconsistently meets Big 4 quality standard

---

## Root Cause Analysis (5-Why)

| # | Why | Finding |
|---|---|---|
| 1 | Why does frontmatter appear in the article? | `MarkdownView` renders all text — no frontmatter stripping |
| 2 | Why is H2 ALL CAPS? | `textTransform: "uppercase"` hardcoded in H2 case of MarkdownView |
| 3 | Why is the article title an H2? | `MERIDIAN_VOICE` prompt specifies `## [Title]` — wrong heading level |
| 4 | Why does output vary in quality? | No quality gate between generation and display; no mandatory structure enforcement |
| 5 | Why has this persisted? | No automated content review step before the draft is marked readable |

---

## Corrective Actions (implemented)

| # | Action | File | Status |
|---|---|---|---|
| CA-1 | Strip YAML frontmatter before rendering in MarkdownView | `App.jsx` | ✓ Done |
| CA-2 | Show frontmatter as a clean metadata badge, not body text | `App.jsx` | ✓ Done |
| CA-3 | Remove `textTransform: uppercase` from H2; use refined typographic style | `App.jsx` | ✓ Done |
| CA-4 | Change article title to H1 (`#`) in MERIDIAN_VOICE; section headers to H2 (`##`) | `content_agent.py` | ✓ Done |
| CA-5 | Tighten MERIDIAN_VOICE to explicitly prohibit generic phrases and enforce Big 4 standard | `content_agent.py` | ✓ Done |
| CA-6 | Increase max_tokens from 3000 → 4000 for complete articles | `content_agent.py` | ✓ Done |

## Preventive Actions

| # | Action | Status |
|---|---|---|
| PA-1 | QA protocol now includes: after any MarkdownView change, verify frontmatter does not render | ✓ CLAUDE.md updated |
| PA-2 | Content agent prompt now rated against Big 4 checklist before each run | ✓ Done |

*Alpha — Steve Review Required*
