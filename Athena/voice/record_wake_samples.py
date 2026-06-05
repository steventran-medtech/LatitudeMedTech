"""
Athena Wake Word Sample Recorder
==================================
Records "Hi Athena" voice samples and saves them to voice/samples/wake/
for use with custom_wake_trainer.py.

Usage:
  python record_wake_samples.py          # record until you type 'q'
  python record_wake_samples.py --n 20   # stop after 20 samples

Controls:
  Press ENTER  → record one sample (speak after the beep)
  Type 'q'     → quit
  Type 'p'     → playback last recording to verify it
  Type 'd'     → delete last recording (redo it)
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import threading
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf

# ── Paths ──────────────────────────────────────────────────────────────────────
VOICE_DIR = Path(__file__).resolve().parent
OUT_DIR   = VOICE_DIR / "samples" / "wake"
TARGET_SR = 16000

# ── Recording params ───────────────────────────────────────────────────────────
MAX_SEC          = 3.0    # max recording length
SILENCE_THRESH   = 0.008  # RMS below this = silence
SILENCE_FRAMES   = 12     # consecutive silent frames before auto-stop (at 50ms/frame = 0.6s)
PRE_ROLL_FRAMES  = 3      # frames to keep before speech starts (avoids clipping the onset)


def _beep(freq: int = 880, dur: float = 0.12, vol: float = 0.4):
    """Play a short beep to cue the speaker."""
    t    = np.linspace(0, dur, int(TARGET_SR * dur), False)
    wave = (np.sin(2 * np.pi * freq * t) * vol).astype(np.float32)
    sd.play(wave, TARGET_SR)
    sd.wait()


def _get_input_device() -> int | None:
    """Pick the best available mic (same scoring as voice_bridge)."""
    env_dev = os.getenv("VOICE_INPUT_DEVICE", "").strip()
    if env_dev.isdigit():
        return int(env_dev)
    best_idx, best_score = None, -999
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] < 1:
            continue
        n = d["name"].lower()
        if any(k in n for k in ("stereo mix", "loopback", "pc speaker")):
            score = -100
        elif any(k in n for k in ("headset", "headphone")):
            score = 100
        elif "array" in n:
            score = 85
        elif "microphone" in n:
            score = 40
        elif "mic" in n:
            score = 30
        else:
            score = 10
        if i < 20:
            score += 2
        if score > best_score:
            best_score, best_idx = score, i
    return best_idx


def record_one(device: int | None, label: str) -> np.ndarray | None:
    """
    Record one utterance. Returns audio as float32 array at TARGET_SR.
    Auto-stops on silence. Returns None if nothing was captured.
    """
    frame_sz   = int(TARGET_SR * 0.050)   # 50 ms frames
    max_frames = int(MAX_SEC * TARGET_SR / frame_sz)
    frames     = []
    silent_count = 0
    speech_started = False
    pre_roll = []

    with sd.InputStream(device=device, samplerate=TARGET_SR,
                        channels=1, dtype="float32",
                        blocksize=frame_sz) as stream:
        for _ in range(max_frames):
            chunk, _ = stream.read(frame_sz)
            audio    = chunk.flatten()
            rms      = float(np.sqrt(np.mean(audio ** 2)))

            if not speech_started:
                pre_roll.append(audio.copy())
                if len(pre_roll) > PRE_ROLL_FRAMES:
                    pre_roll.pop(0)
                if rms > SILENCE_THRESH:
                    speech_started = True
                    frames.extend(pre_roll)
                    frames.append(audio.copy())
            else:
                frames.append(audio.copy())
                if rms < SILENCE_THRESH:
                    silent_count += 1
                    if silent_count >= SILENCE_FRAMES:
                        break
                else:
                    silent_count = 0

    if not frames or not speech_started:
        return None
    return np.concatenate(frames).astype(np.float32)


def save_sample(audio: np.ndarray, out_dir: Path, idx: int) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"hi_athena_{idx:03d}.wav"
    sf.write(str(path), audio, TARGET_SR)
    return path


def run(target_n: int = 0):
    device = _get_input_device()
    dev_name = sd.query_devices(device)["name"] if device is not None else "default"
    print(f"\n{'='*55}")
    print("  Athena Wake Word Sample Recorder")
    print(f"{'='*55}")
    print(f"  Mic    : {dev_name}")
    print(f"  Output : {OUT_DIR}")
    print(f"  Target : {'unlimited' if target_n == 0 else target_n} samples")
    print(f"{'='*55}")
    print("\n  CONTROLS")
    print("    ENTER → record  |  p → playback  |  d → delete  |  q → quit\n")

    # Count existing samples so we don't overwrite
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    existing = sorted(OUT_DIR.glob("hi_athena_*.wav"))
    idx      = int(existing[-1].stem.split("_")[-1]) + 1 if existing else 1
    count    = len(existing)
    last_path: Path | None = None

    if existing:
        print(f"  {count} existing sample(s) found — continuing from #{idx}\n")

    while True:
        if target_n > 0 and count >= target_n:
            print(f"\n  Target of {target_n} samples reached. Done!")
            break

        try:
            cmd = input(f"  [{count} saved] ENTER to record, q/p/d: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  Stopped.")
            break

        if cmd == "q":
            break

        if cmd == "p":
            if last_path and last_path.exists():
                print(f"  Playing {last_path.name}...")
                data, sr = sf.read(str(last_path))
                sd.play(data.astype(np.float32), sr)
                sd.wait()
            else:
                print("  Nothing to play yet.")
            continue

        if cmd == "d":
            if last_path and last_path.exists():
                last_path.unlink()
                count  -= 1
                idx    -= 1
                print(f"  Deleted {last_path.name}.")
                last_path = None
            else:
                print("  Nothing to delete.")
            continue

        # Record
        print("  Ready — say 'Hi Athena' now...", end="", flush=True)
        _beep(880, 0.10)   # low tone = get ready
        time.sleep(0.05)
        _beep(1320, 0.10)  # high tone = go

        audio = record_one(device, label=f"sample_{idx}")

        if audio is None or len(audio) < TARGET_SR * 0.2:
            print(" (nothing captured — try again)")
            continue

        duration = len(audio) / TARGET_SR
        peak     = float(np.max(np.abs(audio)))
        last_path = save_sample(audio, OUT_DIR, idx)
        count    += 1
        idx      += 1
        print(f" saved → {last_path.name}  ({duration:.2f}s, peak {peak:.2f})")

        # Warn if very quiet
        if peak < 0.05:
            print("  ⚠  Recording is very quiet — move closer to the mic")
        elif peak > 0.95:
            print("  ⚠  Recording may be clipping — move back slightly")

    print(f"\n  {count} total samples in {OUT_DIR}")
    if count >= 10:
        print("  Ready to train! Run: python custom_wake_trainer.py")
    else:
        print(f"  Record {max(0, 10 - count)} more for best results.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record 'Hi Athena' wake word samples")
    parser.add_argument("--n", type=int, default=0,
                        help="Stop after N samples (0 = unlimited)")
    args = parser.parse_args()
    run(target_n=args.n)
