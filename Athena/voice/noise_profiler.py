"""
Athena Ambient Noise Profiler
===============================
Samples the microphone during silence windows to build a rolling noise floor model.
Exports a profile to voice/.noise_profile.json that the voice_optimizer reads to
derive data-driven silence_threshold recommendations instead of blind heuristics.

Also reads query_telemetry.jsonl to measure the empirical ambient noise floor
from logged wake_score / stt_logprob patterns without needing live mic access.

Usage:
  python noise_profiler.py --live     # sample mic for 30s and export profile
  python noise_profiler.py --offline  # derive profile from telemetry logs only
  python noise_profiler.py            # offline (default — runs in background safely)

The exported profile:
  {
    "measured_at": "...",
    "method": "live" | "offline",
    "noise_floor_rms": 0.004,        # estimated ambient RMS level
    "recommended_silence_threshold": 0.006,
    "recommended_wake_threshold":    0.52,
    "p10_wake_score":  0.51,         # 10th percentile of detection scores
    "p90_wake_score":  0.74,
    "p10_stt_logprob": -0.62,
    "samples_analysed": 120
  }
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────────

VOICE_DIR      = Path(__file__).resolve().parent
ATHENA         = VOICE_DIR.parent
TELEMETRY_FILE = VOICE_DIR / "query_telemetry.jsonl"
PROFILE_FILE   = VOICE_DIR / ".noise_profile.json"
SETTINGS_FILE  = ATHENA / "settings.json"
LOG_FILE       = ATHENA / "logs" / "voice_optimizer.log"

TARGET_RATE = 16000


def _log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [noise_profiler] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ── Live mic sampling ─────────────────────────────────────────────────────────

def sample_live(duration_secs: int = 30) -> dict:
    """
    Open the microphone and measure RMS amplitude during non-speech windows.
    Returns summary statistics.
    """
    try:
        import sounddevice as sd
        import webrtcvad
    except ImportError as e:
        _log(f"Live sampling unavailable: {e}. Falling back to offline mode.")
        return sample_offline()

    _log(f"Live sampling: recording {duration_secs}s of ambient audio...")

    vad  = webrtcvad.Vad(2)   # aggressiveness 2 (same as bridge)
    chunk_ms  = 30
    chunk_sz  = int(TARGET_RATE * chunk_ms / 1000)
    rms_values = []

    try:
        with sd.InputStream(samplerate=TARGET_RATE, channels=1,
                            dtype="int16", blocksize=chunk_sz) as stream:
            end = time.time() + duration_secs
            while time.time() < end:
                chunk, _ = stream.read(chunk_sz)
                pcm = chunk.flatten().astype(np.int16)
                rms = float(np.sqrt(np.mean(pcm.astype(np.float32) ** 2))) / 32768.0
                # Only count non-speech frames for noise floor estimation
                try:
                    is_speech = vad.is_speech(pcm.tobytes(), TARGET_RATE)
                except Exception:
                    is_speech = rms > 0.01
                if not is_speech:
                    rms_values.append(rms)
    except Exception as e:
        _log(f"Mic sampling error: {e}")
        return sample_offline()

    return _summarise_live(rms_values)


def _summarise_live(rms_values: list) -> dict:
    if not rms_values:
        _log("No non-speech frames captured — check microphone")
        return {}
    arr = np.array(rms_values)
    noise_floor   = float(np.percentile(arr, 75))   # 75th pct of silence = practical floor
    # Silence threshold: 20% above noise floor so genuine speech stands out
    rec_threshold = round(min(noise_floor * 1.20, 0.015), 4)
    _log(f"  Noise floor (75th pct RMS): {noise_floor:.5f}")
    _log(f"  Recommended silence_threshold: {rec_threshold}")
    return {
        "method":                         "live",
        "noise_floor_rms":                round(noise_floor, 5),
        "noise_floor_p50":                round(float(np.percentile(arr, 50)), 5),
        "noise_floor_p90":                round(float(np.percentile(arr, 90)), 5),
        "recommended_silence_threshold":  rec_threshold,
        "samples_analysed":               len(rms_values),
    }


# ── Offline telemetry analysis ────────────────────────────────────────────────

def sample_offline(days: int = 14) -> dict:
    """
    Derive noise floor from query_telemetry.jsonl without live mic access.

    Uses:
    - stt_logprob distribution to estimate STT uncertainty under noise
    - wake_score distribution to calibrate optimal wake_threshold
    - empty transcript rate as a proxy for false-trigger sensitivity
    """
    _log("Offline analysis: reading query_telemetry.jsonl...")

    if not TELEMETRY_FILE.exists():
        _log("No telemetry file found — run Athena with the updated bridge first")
        return {}

    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    rows = []
    for line in TELEMETRY_FILE.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
            if r.get("ts", "") >= cutoff:
                rows.append(r)
        except Exception:
            pass

    if not rows:
        _log("No recent telemetry — collect data first")
        return {}

    _log(f"  Analysing {len(rows)} telemetry records")

    wake_scores  = [r["wake_score"]   for r in rows if r.get("wake_score", 0) > 0]
    stt_logprobs = [r["stt_logprob"]  for r in rows if r.get("stt_logprob", 0) != 0]
    empty_rate   = sum(1 for r in rows if r.get("empty")) / max(len(rows), 1)
    cur_silence  = rows[-1].get("silence_threshold", 0.005) if rows else 0.005
    cur_wake     = rows[-1].get("wake_threshold", 0.5)      if rows else 0.5

    result = {
        "method":          "offline",
        "samples_analysed": len(rows),
        "empty_rate":       round(empty_rate, 3),
    }

    # Wake threshold recommendation
    if wake_scores:
        p10_wake = float(np.percentile(wake_scores, 10))
        p90_wake = float(np.percentile(wake_scores, 90))
        # Ideal threshold sits just above the bottom 10th pct of detections
        # so we keep genuine wakes while discarding near-threshold noise.
        rec_wake = round(min(0.70, max(0.35, p10_wake + 0.05)), 2)
        result.update({
            "p10_wake_score":             round(p10_wake, 3),
            "p50_wake_score":             round(float(np.percentile(wake_scores, 50)), 3),
            "p90_wake_score":             round(p90_wake, 3),
            "recommended_wake_threshold": rec_wake,
        })
        _log(f"  Wake scores p10={p10_wake:.3f} p90={p90_wake:.3f} -> recommend {rec_wake}")

    # STT confidence distribution
    if stt_logprobs:
        p10_lp = float(np.percentile(stt_logprobs, 10))
        p50_lp = float(np.percentile(stt_logprobs, 50))
        result.update({
            "p10_stt_logprob": round(p10_lp, 3),
            "p50_stt_logprob": round(p50_lp, 3),
        })
        _log(f"  STT logprob p10={p10_lp:.3f} p50={p50_lp:.3f}")

    # Silence threshold recommendation from empty-transcript rate
    if empty_rate > 0.35:
        rec_silence = round(min(0.015, cur_silence * 1.15), 4)
        _log(f"  High empty rate ({empty_rate:.0%}): recommend silence_threshold {rec_silence}")
    elif empty_rate < 0.05 and cur_silence > 0.004:
        rec_silence = round(max(0.003, cur_silence * 0.92), 4)
        _log(f"  Low empty rate ({empty_rate:.0%}): can relax silence_threshold to {rec_silence}")
    else:
        rec_silence = cur_silence
        _log(f"  Empty rate ({empty_rate:.0%}) normal — silence_threshold OK at {cur_silence}")
    result["recommended_silence_threshold"] = rec_silence

    return result


# ── Export ────────────────────────────────────────────────────────────────────

def export_profile(data: dict):
    """Write the noise profile to voice/.noise_profile.json."""
    if not data:
        _log("No profile data to export")
        return
    data["measured_at"] = datetime.now().isoformat()
    PROFILE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    _log(f"Profile written: {PROFILE_FILE}")


def load_profile() -> dict:
    """Load the most recent noise profile, or empty dict if not found."""
    if not PROFILE_FILE.exists():
        return {}
    try:
        return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


# ── Main ──────────────────────────────────────────────────────────────────────

def run(live: bool = False) -> dict:
    _log("=" * 50)
    _log("Athena Ambient Noise Profiler")
    _log("=" * 50)

    if live:
        data = sample_live(duration_secs=30)
    else:
        data = sample_offline()

    export_profile(data)
    _log("Profiling complete.")
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Athena Ambient Noise Profiler")
    parser.add_argument("--live",    action="store_true", help="Sample mic live for 30s")
    parser.add_argument("--offline", action="store_true", help="Derive from telemetry logs")
    args = parser.parse_args()
    run(live=args.live)
