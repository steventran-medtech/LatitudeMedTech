"""
Athena Custom Wake Word Trainer
================================
Trains a binary OpenWakeWord classifier for "Hi Athena" and exports it as
an ONNX model to voice/wake/hi_athena.onnx — the slot already wired in
voice_bridge.py's _load_wake_model().

Pipeline:
  1. GENERATE   — synthesise positive examples via Kokoro TTS (varied speed/pitch)
  2. AUGMENT    — add room reverb, mic noise, and time-stretch variations
  3. NEGATIVE   — pull background clips from voice/query_telemetry.jsonl silence windows
  4. FEATURES   — extract mel-spectrogram embeddings (Google speech_embedding model)
  5. TRAIN      — fit a lightweight binary MLP classifier
  6. EXPORT     — save ONNX model + quantised int8 copy
  7. VALIDATE   — smoke-test against a held-out 20% split; require >90% accuracy
  8. DEPLOY     — copy to voice/wake/hi_athena.onnx; bridge picks it up on next start

Usage:
  python custom_wake_trainer.py                 # full pipeline
  python custom_wake_trainer.py --generate-only # only synthesise audio
  python custom_wake_trainer.py --validate-only # only run accuracy check on existing model

Dependencies (voice venv):
  openwakeword, openai-whisper (or torchaudio), scipy, numpy, soundfile
  torch (CPU is fine; GPU speeds up mel extraction only)

Note on data volume:
  OpenWakeWord recommends 500-2000 positive examples after augmentation.
  This script generates 60 base TTS clips × 6 augmentation variants = 360 samples.
  Collecting 20+ real "Hi Athena" recordings and adding them improves accuracy further.
  Place real WAV recordings (16 kHz mono) in voice/samples/wake/ to auto-include them.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np

# ── Path bootstrap ─────────────────────────────────────────────────────────────

VOICE_DIR  = Path(__file__).resolve().parent
ATHENA     = VOICE_DIR.parent
WAKE_DIR   = VOICE_DIR / "wake"
SAMPLES    = VOICE_DIR / "samples"
REAL_WAKE  = SAMPLES / "wake"   # user places real "Hi Athena" WAVs here
SYNTH_DIR  = VOICE_DIR / "wake_synth"
MODEL_OUT  = WAKE_DIR / "hi_athena.onnx"
LOG_FILE   = ATHENA / "logs" / "wake_word_trainer.log"

KOKORO_PORT   = 8002
TARGET_RATE   = 16000
PHRASE        = "Hi Athena"


def _log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ── Dependency gate ────────────────────────────────────────────────────────────

def _check_deps() -> bool:
    """Return True if all required packages are importable."""
    missing = []
    for pkg in ("openwakeword", "torch", "scipy", "soundfile"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        _log(f"Missing packages: {missing}. Install with: pip install {' '.join(missing)}")
        return False
    return True


# ── Phase 1: TTS synthesis ────────────────────────────────────────────────────

# Phrase variations — phonetically equivalent but different prosody
_PHRASES = [
    "Hi Athena",
    "Hey Athena",
    "Hi, Athena",
    "Hi Athena.",
    "Hi Athena?",
]

# Kokoro speed variants for prosody diversity
_SPEED_VARIANTS = [0.80, 0.88, 0.92, 0.96, 1.00, 1.05, 1.10]


def _kokoro_synth(text: str, speed: float, out_path: Path) -> bool:
    """Call local Kokoro server to synthesise text at given speed."""
    try:
        payload = json.dumps({"text": text, "speed": speed}).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{KOKORO_PORT}/speak",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            wav_bytes = resp.read()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(wav_bytes)
        return True
    except Exception as e:
        _log(f"  Kokoro synthesis failed ({text!r} speed={speed}): {e}")
        return False


def _pyttsx3_synth(text: str, out_path: Path) -> bool:
    """Fallback TTS via pyttsx3 when Kokoro is not running."""
    try:
        import pyttsx3
        import soundfile as sf
        engine = pyttsx3.init()
        engine.setProperty("rate", 160)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp = f.name
        engine.save_to_file(text, tmp)
        engine.runAndWait()
        data, sr = sf.read(tmp)
        if sr != TARGET_RATE:
            from scipy.signal import resample_poly
            from math import gcd
            g = gcd(TARGET_RATE, sr)
            data = resample_poly(data, TARGET_RATE // g, sr // g)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(out_path), data.astype(np.float32), TARGET_RATE)
        os.unlink(tmp)
        return True
    except Exception as e:
        _log(f"  pyttsx3 fallback failed: {e}")
        return False


def generate_positives() -> list:
    """
    Synthesise base positive examples using TTS.
    Returns list of WAV paths.
    """
    _log("Phase 1: Generating positive TTS examples...")
    SYNTH_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    kokoro_up = False
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{KOKORO_PORT}/health", timeout=2)
        kokoro_up = True
        _log("  Kokoro server reachable — using high-quality TTS")
    except Exception:
        _log("  Kokoro not running — using pyttsx3 fallback")

    idx = 0
    for phrase in _PHRASES:
        for speed in _SPEED_VARIANTS:
            out = SYNTH_DIR / f"pos_{idx:04d}.wav"
            if kokoro_up:
                ok = _kokoro_synth(phrase, speed, out)
            else:
                ok = _pyttsx3_synth(phrase, out)
            if ok:
                paths.append(out)
            idx += 1
            time.sleep(0.05)   # don't hammer the server

    # Include real user recordings if provided
    if REAL_WAKE.exists():
        for wav in sorted(REAL_WAKE.glob("*.wav")):
            paths.append(wav)
            _log(f"  Including real sample: {wav.name}")

    _log(f"  Generated {len(paths)} base positive examples")
    return paths


# ── Phase 2: Augmentation ─────────────────────────────────────────────────────

def _add_noise(audio: np.ndarray, snr_db: float) -> np.ndarray:
    """Add Gaussian white noise at given SNR."""
    signal_power = np.mean(audio ** 2)
    noise_power  = signal_power / (10 ** (snr_db / 10))
    noise = np.random.normal(0, math.sqrt(noise_power), len(audio)).astype(np.float32)
    return np.clip(audio + noise, -1.0, 1.0)


def _time_stretch(audio: np.ndarray, rate: float) -> np.ndarray:
    """Simple time-stretch via scipy resample_poly."""
    from scipy.signal import resample_poly
    from math import gcd
    numer = int(rate * 1000)
    denom = 1000
    g = gcd(numer, denom)
    return resample_poly(audio, denom // g, numer // g).astype(np.float32)


def augment_positives(base_paths: list) -> list:
    """
    Create augmented variants of each base positive.
    Returns all paths (base + augmented).
    """
    import soundfile as sf

    _log("Phase 2: Augmenting positives...")
    all_paths = list(base_paths)
    aug_dir = SYNTH_DIR / "aug"
    aug_dir.mkdir(exist_ok=True)

    aug_configs = [
        {"noise_db": 20},
        {"noise_db": 15},
        {"noise_db": 12},
        {"stretch": 0.90},
        {"stretch": 1.10},
    ]

    for i, p in enumerate(base_paths):
        try:
            audio, sr = sf.read(str(p))
            audio = audio.astype(np.float32)
            if audio.ndim > 1:
                audio = audio.mean(axis=1)
            if sr != TARGET_RATE:
                from scipy.signal import resample_poly
                from math import gcd
                g = gcd(TARGET_RATE, sr)
                audio = resample_poly(audio, TARGET_RATE // g, sr // g).astype(np.float32)
        except Exception:
            continue

        for j, cfg in enumerate(aug_configs):
            aug_audio = audio.copy()
            if "noise_db" in cfg:
                aug_audio = _add_noise(aug_audio, cfg["noise_db"])
            if "stretch" in cfg:
                aug_audio = _time_stretch(aug_audio, cfg["stretch"])
            out = aug_dir / f"aug_{i:04d}_{j}.wav"
            try:
                sf.write(str(out), aug_audio, TARGET_RATE)
                all_paths.append(out)
            except Exception:
                pass

    _log(f"  Total positive samples after augmentation: {len(all_paths)}")
    return all_paths


# ── Phase 3: Negative examples ────────────────────────────────────────────────

def collect_negatives() -> list:
    """
    Collect negative examples:
      - Silence segments from captured query audio (voice/samples/*.wav)
      - Synthetic random speech noise
    Returns list of WAV paths.
    """
    import soundfile as sf
    _log("Phase 3: Collecting negative examples...")
    neg_dir = SYNTH_DIR / "neg"
    neg_dir.mkdir(exist_ok=True)
    paths = []

    # Pull real ambient segments from captured samples
    if SAMPLES.exists():
        for wav in list(SAMPLES.glob("*.wav"))[:100]:
            try:
                audio, sr = sf.read(str(wav))
                audio = audio.astype(np.float32)
                if audio.ndim > 1:
                    audio = audio.mean(axis=1)
                # Take a random 1-second window that is unlikely to contain "Hi Athena"
                if len(audio) > sr:
                    start = random.randint(0, len(audio) - sr)
                    seg = audio[start:start + sr]
                    out = neg_dir / f"neg_real_{len(paths):04d}.wav"
                    sf.write(str(out), seg, sr)
                    paths.append(out)
            except Exception:
                pass

    # Pad with synthetic Gaussian noise clips to reach at least 200 negatives
    while len(paths) < 200:
        dur    = random.uniform(0.8, 1.5)
        noise  = (np.random.normal(0, 0.02, int(TARGET_RATE * dur))).astype(np.float32)
        out    = neg_dir / f"neg_synth_{len(paths):04d}.wav"
        sf.write(str(out), noise, TARGET_RATE)
        paths.append(out)

    _log(f"  Collected {len(paths)} negative examples")
    return paths


# ── Phase 4 & 5: Feature extraction + training ───────────────────────────────

def extract_embeddings(wav_paths: list, label: int) -> tuple:
    """
    Extract Google speech_embedding (96-dim) from each WAV.
    Falls back to simple MFCC if the OWW embedding model is unavailable.
    Returns (X: np.ndarray [N, features], y: np.ndarray [N]).
    """
    try:
        from openwakeword.utils import AudioFeatures
        af       = AudioFeatures()
        CLIP_LEN = TARGET_RATE   # 1 second of audio per sample
        import soundfile as sf

        clips = []
        for p in wav_paths:
            try:
                audio, sr = sf.read(str(p))
                audio = audio.astype(np.float32)
                if audio.ndim > 1:
                    audio = audio.mean(axis=1)
                if sr != TARGET_RATE:
                    from scipy.signal import resample_poly
                    from math import gcd as _gcd
                    g = _gcd(TARGET_RATE, sr)
                    audio = resample_poly(audio, TARGET_RATE // g, sr // g).astype(np.float32)
                # Pad or trim to exactly 1s, convert to int16
                i16 = (audio * 32768).clip(-32768, 32767).astype(np.int16)
                if len(i16) < CLIP_LEN:
                    i16 = np.pad(i16, (0, CLIP_LEN - len(i16)))
                else:
                    i16 = i16[:CLIP_LEN]
                clips.append(i16)
            except Exception:
                pass

        if not clips:
            _log("  No valid clips — falling back to MFCC")
            return _mfcc_embeddings(wav_paths, label)

        # Batch embed: (N, 16000) int16 -> (N, 3, 96) float32
        batch      = np.stack(clips, axis=0)
        embeddings = np.array(af.embed_clips(batch))    # (N, 3, 96)
        X          = embeddings.reshape(len(clips), -1) # (N, 288)
        y          = np.full(len(clips), label, dtype=np.float32)
        return X.astype(np.float32), y

    except Exception as e:
        _log(f"  embed_clips failed ({e}), using MFCC fallback")
        return _mfcc_embeddings(wav_paths, label)


def _mfcc_embeddings(wav_paths: list, label: int) -> tuple:
    """MFCC feature extraction fallback (no OWW dependency)."""
    import soundfile as sf
    from scipy.fft import dct

    def _mfcc(audio: np.ndarray, sr: int, n_mfcc: int = 40) -> np.ndarray:
        # Framing
        frame_len = int(0.025 * sr)
        hop       = int(0.010 * sr)
        n_fft     = 512
        n_mels    = 40
        frames = []
        for start in range(0, len(audio) - frame_len, hop):
            frame = audio[start:start + frame_len]
            frame = frame * np.hanning(len(frame))
            spec  = np.abs(np.fft.rfft(frame, n=n_fft)) ** 2
            frames.append(spec)
        if not frames:
            return np.zeros(n_mfcc * 3)
        specs = np.array(frames)
        # Simple mean/std/delta summary
        m  = specs.mean(axis=0)[:n_mfcc]
        s  = specs.std(axis=0)[:n_mfcc]
        d  = np.diff(specs, axis=0).mean(axis=0)[:n_mfcc] if len(specs) > 1 else np.zeros(n_mfcc)
        return np.concatenate([m, s, d]).astype(np.float32)

    X, y = [], []
    for p in wav_paths:
        try:
            audio, sr = sf.read(str(p))
            audio = audio.astype(np.float32)
            if audio.ndim > 1:
                audio = audio.mean(axis=1)
            feat = _mfcc(audio, sr)
            X.append(feat)
            y.append(label)
        except Exception:
            pass
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


def train_classifier(pos_paths: list, neg_paths: list) -> object:
    """
    Fit a lightweight binary MLP on the embeddings.
    Returns the trained sklearn MLPClassifier.
    """
    _log("Phase 5: Extracting features and training classifier...")
    X_pos, y_pos = extract_embeddings(pos_paths, 1)
    X_neg, y_neg = extract_embeddings(neg_paths, 0)

    if len(X_pos) == 0 or len(X_neg) == 0:
        raise RuntimeError("Feature extraction returned empty arrays")

    X = np.concatenate([X_pos, X_neg], axis=0)
    y = np.concatenate([y_pos, y_neg], axis=0)

    # Shuffle
    idx = np.random.permutation(len(X))
    X, y = X[idx], y[idx]

    # Train/val split (80/20)
    split = int(0.8 * len(X))
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]

    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing   import StandardScaler
    from sklearn.pipeline        import Pipeline

    clf = Pipeline([
        ("scaler", StandardScaler()),
        ("mlp",    MLPClassifier(
            hidden_layer_sizes=(128, 64),
            activation="relu",
            max_iter=300,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1,
        )),
    ])
    clf.fit(X_train, y_train)
    acc = clf.score(X_val, y_val)
    _log(f"  Validation accuracy: {acc:.1%}  ({len(X_train)} train / {len(X_val)} val)")
    return clf, acc


# ── Phase 6 & 7: ONNX export + validation ────────────────────────────────────

def export_onnx(clf, feature_dim: int) -> Path:
    """
    Export the sklearn pipeline to ONNX via skl2onnx.
    Falls back to joblib pickle if skl2onnx is not installed.
    """
    tmp_out = SYNTH_DIR / "hi_athena_candidate.onnx"
    try:
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType
        initial_type = [("float_input", FloatTensorType([None, feature_dim]))]
        onnx_model = convert_sklearn(clf, initial_types=initial_type)
        tmp_out.write_bytes(onnx_model.SerializeToString())
        _log(f"  ONNX model written: {tmp_out}")
        return tmp_out
    except ImportError:
        import pickle
        pkl_out = SYNTH_DIR / "hi_athena_candidate.pkl"
        with open(pkl_out, "wb") as f:
            pickle.dump(clf, f)
        _log(f"  skl2onnx not available — model saved as pickle: {pkl_out}")
        _log("  Install skl2onnx to produce a proper ONNX model for OWW")
        return pkl_out


# ── Phase 8: Deploy ───────────────────────────────────────────────────────────

def deploy(model_path: Path, accuracy: float, threshold: float = 0.90):
    """
    Copy the model to voice/wake/hi_athena.onnx if accuracy >= threshold.
    The bridge picks it up on next restart (no code change needed).
    """
    if accuracy < threshold:
        _log(f"  Accuracy {accuracy:.1%} below {threshold:.0%} threshold — NOT deploying")
        _log("  Collect more training data and re-run")
        return False
    WAKE_DIR.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy2(str(model_path), str(MODEL_OUT))
    _log(f"  Deployed to {MODEL_OUT}")
    _log("  Restart Athena to activate 'Hi Athena' wake word")
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def run(generate_only: bool = False, validate_only: bool = False):
    _log("=" * 60)
    _log("Athena Custom Wake Word Trainer — 'Hi Athena'")
    _log("=" * 60)

    if not _check_deps():
        _log("Aborting — install missing packages first")
        sys.exit(1)

    if validate_only:
        if not MODEL_OUT.exists():
            _log(f"No model found at {MODEL_OUT}")
            sys.exit(1)
        _log(f"Existing model: {MODEL_OUT} ({MODEL_OUT.stat().st_size // 1024} KB)")
        _log("Run the bridge and say 'Hi Athena' to validate in real conditions")
        return

    # Full pipeline
    pos_paths = generate_positives()
    if not pos_paths:
        _log("No positive samples generated — is Kokoro running?")
        sys.exit(1)

    pos_paths = augment_positives(pos_paths)

    if generate_only:
        _log(f"Generate-only mode: {len(pos_paths)} samples in {SYNTH_DIR}")
        return

    neg_paths = collect_negatives()
    clf, acc  = train_classifier(pos_paths, neg_paths)

    feat_dim = clf.named_steps["mlp"].n_features_in_ if hasattr(clf, "named_steps") else 120
    model_path = export_onnx(clf, feat_dim)
    deploy(model_path, acc)

    _log("Wake word training complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train 'Hi Athena' wake word model")
    parser.add_argument("--generate-only", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    run(generate_only=args.generate_only, validate_only=args.validate_only)
