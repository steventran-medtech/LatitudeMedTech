# DC-005 — Manual Verification Protocol (MTP)
**Document:** DC-005-MTP · Version 1.1 · 2026-06-07  
**Approved by:** Steven Tran  
**Companion to:** DC-005 Verification Protocol · DC-004 RTM

---

## Purpose

Three design inputs cannot be verified by static code analysis alone because
they depend on observable runtime behavior. This protocol defines the exact
steps for Steven to execute each test against the running Athena system and
record the result.

**Prerequisite:** Athena must be fully started (`start_athena.ps1` complete,
Chrome open, voice session active for MTP-001 and MTP-003).

---

## MTP-001 — First TTS Audio Latency ≤ 2 s  
**DI:** DI-004-C  **Priority:** P0  **Phase:** Phase 3

### Objective
Confirm that the first audible TTS byte from Kokoro is delivered within
2 seconds of voice query completion.

### Setup
1. Start Athena (`start_athena.ps1`).
2. Confirm voice is active — the header badge shows "Listening."
3. Have a stopwatch or phone timer ready.

### Test Steps

| Step | Action | Expected Result |
|---|---|---|
| 1 | Say the wake word ("Athena") and wait for the chime | Chime sounds within 1 second |
| 2 | Ask a short, factual question: **"What is ISO 13485?"** | Voice bridge enters record mode |
| 3 | Start the stopwatch **when you finish speaking** | — |
| 4 | Stop the stopwatch **when you hear the first syllable of the response** | — |
| 5 | Record elapsed time | — |

### Pass Criteria
- Elapsed time ≤ **2.0 seconds** on ≥ 3 of 5 consecutive runs.

### Failure Actions
- If > 2.0 s: check `voice/sessions.jsonl` for timing logs; review
  `_ask_claude_streaming` and Kokoro pipeline in `voice_bridge.py`.
- File a CAPA if 3+ consecutive failures (threshold from DC-005 §CAPA Triggers).

### Record
| Run | Query | Elapsed (s) | Pass/Fail |
|---|---|---|---|
| 1 | What is ISO-13485? | 21 | Fail |
| 2 | How many mergers and acquisitions were there for MedTech in 2024? | 18 | Fail |
| 3 | What were the main quality roadblocks for Stryker's acquisition of Masimo medical? | 15 | Fail |
| 4 | What is ISO-14971? | 31 | Fail |
| 5 | What is an example of biocompatibility standard for medical devices? | 27 | Fail |

**Tester:** Steven Tran  **Date:** 6/7/2026  **Result (Pass/Fail):** Fail

---

## MTP-002 — Deck Section Completeness  
**DI:** DI-009-A  **Priority:** P1  **Phase:** Phase 3

### Objective
Confirm that a generated PPTX deck contains all five required sections:
Cover, Executive Summary, Narrative, Charts, and Recommendations.

### Setup
1. Start Athena with server running.
2. Navigate to the **Decks** tab.

### Test Steps

| Step | Action | Expected Result |
|---|---|---|
| 1 | Click **Generate Deck** (or trigger via voice: "Generate a strategy deck for a 510k submission") | Agent runs; spinner appears |
| 2 | Wait for completion; check the Document Queue for the deck submission | Deck appears in Pending queue |
| 3 | Approve the deck in Document Queue | Deck moves to Approved |
| 4 | Download the approved deck from the Decks tab | `.pptx` file downloads |
| 5 | Open the `.pptx` in PowerPoint or LibreOffice | File opens without error |
| 6 | Verify slide 1: **Cover slide** with title and date | Present |
| 7 | Verify slide 2 (or section): **Executive Summary** (Situation / Complication / Resolution structure) | Present |
| 8 | Verify middle slides: **Narrative / Analysis** content | Present |
| 9 | Verify chart slide: at least one data table or visual | Present |
| 10 | Verify final slide: **Recommendations / Next Steps** | Present |

### Pass Criteria
All five sections present in the generated PPTX.

### Failure Actions
- If any section missing: check `deck_agent.py` `_DECK_GUIDES` entry and
  `deck_skills.py` slide construction order.
- Update DI-009-A status to PARTIAL and open a CAPA if section absent.

### Record

| Section | Present (Y/N) |
|---|---|
| Cover slide | |
| Executive Summary | |
| Narrative / Analysis | |
| Chart / Visual | |
| Recommendations | |

**Deck file:** \_\_\_\_\_\_\_\_\_\_  **Tester:** \_\_\_\_\_\_\_\_\_\_  **Date:** \_\_\_\_\_\_\_\_\_\_  **Result (Pass/Fail):** \_\_\_\_\_\_\_\_\_\_

---

## MTP-003 — Voice Conversation Latency ≤ 1.75 s  
**DI:** DI-022-A / DI-022-B  **Priority:** P0  **Phase:** Phase 3

### Objective
Confirm end-to-end voice latency — LLM-start to first audible agent sentence —
is ≤ 1.75 seconds. CO-019 added `test_voice_latency_live.py` which automates
the WebSocket event timing. **Run the script; stopwatch backup is secondary.**

### Preferred Method — Automated Script (CO-019)

```powershell
# From the repo root (Athena must be running with voice active)
python design_control\test_voice_latency_live.py
```

The script:
1. Connects to the voice WebSocket at `ws://127.0.0.1:8000/api/voice/ws`
2. Prompts you through 5 timed queries (press Enter before each)
3. Records `voice_thinking` → `voice_speaking_partial` latency per run
4. Outputs pass/fail: ≥ 4 of 5 runs ≤ 1.75 s

**Note:** The script measures LLM-start → first TTS sentence (excludes SILENCE_DURATION + STT).
Full silence-to-audio latency ≈ script result + ~0.73 s (0.65 s silence window + ~0.08 s GPU STT).

### Setup
1. Start Athena (`start_athena.ps1`).
2. Confirm the voice header badge shows "Listening."
3. Confirm the RTX 4070 is the active GPU (Task Manager → GPU).
4. **Run 2–3 warm-up queries first** (not counted) — cold Kokoro inflates first-run latency.

### Backup Method — Manual Stopwatch

| Step | Action | Expected Result |
|---|---|---|
| 1 | Say the wake word; wait for chime | Chime within 1 s |
| 2 | Ask: **"Define CAPA in one sentence."** | Voice bridge captures query |
| 3 | Start stopwatch **when you stop speaking** | — |
| 4 | Stop stopwatch **at first audible syllable** | — |
| 5 | Record elapsed time | — |
| 6 | Repeat for 5 runs | — |

### Pass Criteria
- ≥ 4 of 5 runs: LLM-to-audio ≤ **1.75 s** (script) or stopwatch ≤ **2.5 s** (manual includes silence window).
- No single run > **3.0 seconds** hard cap.

### Failure Actions
- If 2+ runs fail: check `SILENCE_DURATION` in `Athena/settings.json` (must be ≤ 0.65).
- Confirm Kokoro healthy: `curl http://127.0.0.1:8002/health`
- Review `_ask_claude_streaming` streaming pipeline in `voice_bridge.py`.
- If persistent > 2.0 s full-cycle: open CAPA.

### Record (Script Run)

| Run | Query | Script LLM→Audio (s) | Pass/Fail |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

**Tester:** \_\_\_\_\_\_\_\_\_\_  **Date:** \_\_\_\_\_\_\_\_\_\_  **Result (Pass/Fail):** \_\_\_\_\_\_\_\_\_\_

---

## Status Update Procedure

After completing each MTP:

1. Record result in the table above (sign and date).
2. If **PASS**: update the DI status in DC-002 from PARTIAL to VERIFIED.
   Update DC-004 RTM to match. Bump document version. Open a CO (C1 class).
3. If **FAIL**: open a CAPA using the template in `Athena/ops/hr/CAPA-*.md`.
   Do not update DI status until the CAPA is closed and the test re-run passes.

---

## Summary Table

| MTP | DI | Requirement | Current Status | Phase |
|---|---|---|---|---|
| MTP-001 | DI-004-C | First TTS byte ≤ 2 s | PARTIAL | Phase 3 |
| MTP-002 | DI-009-A | Deck: cover + exec summary + narrative + chart + recommendations | PARTIAL | Phase 3 |
| MTP-003 | DI-022-A | End-to-end voice latency ≤ 1.75 s | PARTIAL | Phase 3 |

*All three static automated tests pass (`dc_verify.py` exits 0). These
protocols close the live-stack verification gap.*
