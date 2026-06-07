#!/usr/bin/env python3
"""
Interactive Voice Latency Test — DI-022-A/B Live Verification  (CO-019)
========================================================================
Connects to the Athena voice WebSocket, guides Steven through 5 timed
queries, and measures the latency from LLM-start (voice_thinking event)
to first audible TTS sentence (voice_speaking_partial event).

Pass criteria (DI-022-A): ≥ 4 of 5 runs ≤ 1.75 s.

Usage (Athena must be running with voice active):
    python design_control\\test_voice_latency_live.py

Requires:
    pip install websockets        (run once in the project venv)
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Guard — must be run directly, not imported
# ---------------------------------------------------------------------------
if __name__ != "__main__":
    raise ImportError("This script is a runnable test harness, not a module.")

try:
    import websockets
except ImportError:
    print("ERROR: 'websockets' not installed.")
    print("Fix:   pip install websockets   (run in the project venv)")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
THRESHOLD_S = 1.75                          # DI-022-A latency ceiling
PASS_RUNS   = 4                             # minimum passing runs out of 5
WS_URL      = "ws://127.0.0.1:8000/api/voice/ws"
TIMEOUT_S   = 30                            # per-run wall-clock limit

TEST_QUERIES = [
    "What is ISO 13485?",
    "Define CAPA in one sentence.",
    "What does FDA stand for?",
    "Name one design control document.",
    "What is risk management?",
]


# ---------------------------------------------------------------------------
# Per-run timing logic
# ---------------------------------------------------------------------------
async def run_one_query(ws, run_idx: int) -> float | None:
    """
    Guides Steven through one query.
    Returns LLM-to-first-audio latency in seconds, or None on skip/timeout.

    Event sequence captured:
      voice_thinking       — post-STT, Claude call starting  → t_thinking
      voice_speaking_partial — first TTS sentence dispatched → t_first_audio
    """
    query = TEST_QUERIES[run_idx]
    print(f"\n  ── Run {run_idx + 1} of 5 ──")
    print(f"  Query : \"{query}\"")
    print("  Action: Say the wake phrase ('Hi Athena'), then ask the query above.")
    print("  Press Enter when you are ready to speak...", end="", flush=True)
    # Non-blocking input — run in executor so we don't block the event loop
    await asyncio.get_event_loop().run_in_executor(None, input)

    t_thinking   = None
    t_first_audio = None
    deadline     = time.monotonic() + TIMEOUT_S

    while time.monotonic() < deadline:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=1.0)
        except asyncio.TimeoutError:
            continue
        except Exception as exc:
            print(f"\n  [!] WebSocket error: {exc}")
            return None

        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue

        etype = event.get("type", "")

        if etype == "voice_thinking" and t_thinking is None:
            t_thinking = time.monotonic()
            print("  [✓] voice_thinking received  (STT done, LLM starting)…", flush=True)

        elif etype == "voice_speaking_partial" and t_thinking is not None and t_first_audio is None:
            t_first_audio = time.monotonic()
            elapsed = t_first_audio - t_thinking
            verdict = "PASS" if elapsed <= THRESHOLD_S else "FAIL"
            sentence_preview = str(event.get("sentence", ""))[:60]
            print(f"  [✓] voice_speaking_partial   (first audio sentence)")
            if sentence_preview:
                print(f"      Preview: \"{sentence_preview}\"")
            print(f"  Latency: {elapsed:.3f} s  [{verdict}]")
            return elapsed

        elif etype == "voice_listening" and t_thinking is not None and t_first_audio is None:
            # Voice returned to listening without a speaking_partial — false wake or empty response
            print("  [!] Voice returned to listening without a response — run skipped.")
            return None

    print(f"  [!] Timeout after {TIMEOUT_S} s — no response received.")
    return None


# ---------------------------------------------------------------------------
# Main harness
# ---------------------------------------------------------------------------
async def main() -> int:
    print()
    print("=" * 62)
    print("  Athena Voice Latency Test  —  DI-022-A/B Live Verification")
    print("=" * 62)
    print()
    print(f"  Threshold : LLM-start → first audio ≤ {THRESHOLD_S} s")
    print(f"  Pass rule : ≥ {PASS_RUNS} of 5 runs within threshold")
    print(f"  WebSocket : {WS_URL}")
    print()
    print("  Prerequisites (check before continuing):")
    print("   1. Athena fully started  (start_athena.ps1 complete)")
    print("   2. Voice active          (header badge shows 'Listening')")
    print("   3. RTX 4070 GPU active   (Task Manager → GPU utilisation)")
    print("   4. Run 2–3 warm-up queries first — cold Kokoro skews results")
    print()
    print("  Note: This script measures the LLM→TTS segment only.")
    print("  Full silence-to-audio adds ~0.73 s (silence window + GPU STT).")
    print()
    input("  Press Enter when ready to begin the 5 timed runs…")

    results: list[float | None] = []

    try:
        async with websockets.connect(WS_URL) as ws:
            print(f"\n  Connected to {WS_URL}")
            for i in range(5):
                elapsed = await run_one_query(ws, i)
                results.append(elapsed)
                if i < 4:
                    print("\n  Waiting 3 s before next run…", flush=True)
                    await asyncio.sleep(3)
    except OSError as exc:
        print(f"\n  ERROR: Cannot connect to {WS_URL}")
        print(f"  Details: {exc}")
        print("  Check: curl http://127.0.0.1:8000/api/voice/status")
        return 1

    # ── Summary ──────────────────────────────────────────────────────────────
    valid   = [r for r in results if r is not None]
    passing = [r for r in valid   if r <= THRESHOLD_S]
    overall = "PASS" if len(passing) >= PASS_RUNS else "FAIL"

    print()
    print("=" * 62)
    print("  RESULTS")
    print("=" * 62)
    for i, r in enumerate(results, 1):
        if r is None:
            print(f"  Run {i}:  SKIPPED")
        else:
            verdict = "PASS" if r <= THRESHOLD_S else "FAIL"
            bar     = "█" * min(int(r / THRESHOLD_S * 20), 20)
            print(f"  Run {i}:  {r:.3f} s  [{verdict}]  {bar}")

    print()
    print(f"  {len(passing)}/{len(valid)} valid runs ≤ {THRESHOLD_S} s")
    print(f"  DI-022-A verdict: {overall}")

    if overall == "PASS":
        print()
        print("  Next steps:")
        print("  1. Record result in DC-005_manual_verification_protocol.md MTP-003.")
        print("  2. Open a CO (C1) to update DC-002 DI-022-A status → VERIFIED.")
    else:
        print()
        print("  Failure — investigate:")
        print("   1. Check SILENCE_DURATION in Athena/settings.json  (must be ≤ 0.65)")
        print("   2. Confirm Kokoro healthy: curl http://127.0.0.1:8002/health")
        print("   3. Confirm RTX 4070 in use (not CPU fallback Whisper)")
        print("   4. Review _ask_claude_streaming in Athena/voice/voice_bridge.py")
        print("   5. File a CAPA if 3+ consecutive test sessions fail")

    print()
    return 0 if overall == "PASS" else 1


sys.exit(asyncio.run(main()))
