# DC-005 — Manual Verification Protocol (MTP)
**Document:** DC-005-MTP · Version 1.0 · 2026-06-07  
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
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

**Tester:** \_\_\_\_\_\_\_\_\_\_  **Date:** \_\_\_\_\_\_\_\_\_\_  **Result (Pass/Fail):** \_\_\_\_\_\_\_\_\_\_

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
**DI:** DI-022-A  **Priority:** P0  **Phase:** Phase 3

### Objective
Confirm end-to-end voice latency — from end of user speech to first audible
agent response — is ≤ 1.75 seconds. This is a tighter threshold than MTP-001
and covers the full pipeline: VAD silence detection → STT → Claude streaming
→ sentence split → Kokoro TTS first byte.

### Setup
1. Start Athena (`start_athena.ps1`).
2. Confirm the voice header badge shows "Listening."
3. Confirm the RTX 4070 is the active GPU (check Task Manager → GPU).
4. Have a stopwatch or phone timer ready.
5. **Run 3 warm-up queries first** (discarded) — cold model loads inflate first-run latency.

### Test Steps

| Step | Action | Expected Result |
|---|---|---|
| 1 | Say the wake word; wait for chime | Chime within 1 s |
| 2 | Ask: **"Define CAPA in one sentence."** | Voice bridge captures query |
| 3 | Start stopwatch **at the moment silence is detected** (you stop speaking) | — |
| 4 | Stop stopwatch **at first audible syllable of response** | — |
| 5 | Record elapsed time | — |
| 6 | Repeat steps 1–5 for 5 runs, varying query length | — |

**Suggested queries (short, to isolate pipeline latency not LLM think time):**
- "What is FDA 510k?"
- "Define risk management."
- "Name one ISO 13485 clause."
- "What does MDSAP stand for?"
- "Define design control."

### Pass Criteria
- ≥ 4 of 5 runs: elapsed ≤ **1.75 seconds**.
- No single run > **2.5 seconds** (hard cap).

### Failure Actions
- If 2+ runs > 1.75 s: profile `_ask_claude_streaming` and Kokoro TTS
  pipeline in `voice_bridge.py`; check `SILENCE_DURATION` setting.
- If consistent > 2.0 s: consider reverting DI-022-A threshold to 2.0 s
  via change order and filing a CAPA for engineering investigation.

### Record

| Run | Query | Elapsed (s) | Pass/Fail |
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
