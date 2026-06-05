# CAPA-Voice-001 — Voice Response Latency & Activation Clarity

**Date:** 2026-06-04
**Status:** CLOSED — Corrective actions implemented
**Raised by:** Steven Tran (3rd occurrence — mandatory CAPA trigger)
**Reviewed by:** Pending Steven approval

---

## Problem Statement

Voice responses take 4–10+ seconds from wake word to first audio. No clear indication Athena has activated between the wake word and response. Users cannot distinguish "Athena is processing" from "Athena did not hear me."

---

## Root Cause Analysis (5-Why)

| # | Why | Finding |
|---|---|---|
| 1 | Why is response slow? | Full TTS audio is generated before any playback begins |
| 2 | Why is full audio generated first? | `_speak_kokoro()` POSTs complete response text, waits for complete WAV |
| 3 | Why is full response text available before TTS? | Claude API call is synchronous — waits for all 80 tokens |
| 4 | Why is there dead silence during processing? | No progressive feedback between wake detection and response |
| 5 | Why has this not been fixed? | Previous fixes addressed model loading, not the generation pipeline |

**Primary root cause:** Sequential pipeline — Wake → Record → Transcribe → LLM → TTS → Play. No parallelism, no streaming, no progressive feedback.

**Contributing factors:**
- Activation chime: 80ms at 0.25 volume — imperceptible to users
- No "I heard you, thinking…" acknowledgement phrase
- Kokoro TTS processes full response (~60 words = ~1.2s) before first audio

---

## Corrective Actions (implemented)

| # | Action | File | Status |
|---|---|---|---|
| CA-1 | Sentence-level streaming TTS — play each sentence as generated | `voice_bridge.py` | ✓ Done |
| CA-2 | Streaming Claude API — pipe text to TTS per sentence boundary | `voice_bridge.py` | ✓ Done |
| CA-3 | Immediate acknowledgement phrase after transcription | `voice_bridge.py` | ✓ Done |
| CA-4 | Stronger activation chime (200ms, 0.5 volume, 2-tone) | `voice_bridge.py` | ✓ Done |
| CA-5 | "Thinking" WebSocket event with visible UI animation | `voice_bridge.py` | ✓ Done |

## Preventive Actions

| # | Action | Owner | Due |
|---|---|---|---|
| PA-1 | Voice session latency tracked per query; HR flags if avg > 4s | `voice_bridge.py` memory | ✓ Done |
| PA-2 | Voice self-optimization — adjusts silence threshold based on false-start rate | `voice_bridge.py` | ✓ Done |
| PA-3 | QA protocol requires voice latency test after any TTS/LLM change | CLAUDE.md | ✓ Done |

---

## Expected Outcome

First audio from Athena within **1.5 seconds** of query completion:
- Transcription: ~400ms (Whisper tiny.en)
- First sentence generation: ~600ms (Claude streaming)
- First sentence TTS: ~200ms (Kokoro hot)
- **Total to first audio: ~1.2s**

*Alpha — Steve Review Required*
