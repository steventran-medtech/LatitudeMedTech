"""
Athena Voice Bridge
====================
Always-listening voice layer: wake word → Whisper STT → intent routing
→ Claude / agent → Kokoro TTS (British English, persistent server).

Key behaviours:
- Records at device native rate, resamples to 16 kHz for OWW + Whisper
- Kokoro runs as a persistent sidecar server (port 8002) — no per-call
  Python startup; model stays hot in memory for ~200 ms TTS latency
- Voice intents auto-trigger agents (content, briefing, RAG, ISO, coaching)
- Agent context loaded from .claude/agents/*.md files (no extra API calls)

.env keys:
  VOICE_TTS_BACKEND   kokoro (default) | piper | miso
  VOICE_KOKORO_VOICE  bf_emma (default, British female)
  VOICE_INPUT_DEVICE  device index (blank = system default)
"""

import os
import sys
import asyncio
import io
import json
import re
import subprocess
import threading
import tempfile
import time
import urllib.request
import urllib.error
from collections import deque

import hashlib
import numpy as np
import sounddevice as sd
import soundfile as sf
from math import gcd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from scipy.signal import resample_poly

try:
    import webrtcvad as _webrtcvad
    _vad = _webrtcvad.Vad(2)   # aggressiveness 2: filters keyboard/ambient, keeps speech
    _VAD_FRAME = 480            # 30 ms @ 16 kHz — exact frame size required by webrtcvad
except ImportError:
    _vad = None
    _VAD_FRAME = 480
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect

ATHENA = Path(__file__).resolve().parent.parent          # voice/ -> Athena/
RULES  = ATHENA.parent / ".claude" / "agents"
load_dotenv(ATHENA / "voice" / ".env")

sys.path.insert(0, str(ATHENA / "agents"))
try:
    from memory import Memory
    _mem = Memory()
    _has_memory = True
except Exception:
    _mem = None
    _has_memory = False

try:
    from kb_query import KBQuery
    _kb = KBQuery()
except Exception:
    _kb = None

# ── Config ────────────────────────────────────────────────────────────────────

TARGET_RATE       = 16000
CHUNK_SAMPLES_16K = 1280
SILENCE_THRESHOLD = 0.01
SILENCE_DURATION  = 1.5   # 0.8 cut off speech mid-sentence → bad transcription → blocked response
MAX_RECORD_SEC    = 30
WAKE_THRESHOLD    = 0.5
WHISPER_MODEL     = "tiny.en"    # tiny is 3× faster than base with acceptable accuracy

TTS_BACKEND   = os.getenv("VOICE_TTS_BACKEND",  "kokoro").lower()
KOKORO_VOICE  = os.getenv("VOICE_KOKORO_VOICE", "bf_emma")
KOKORO_PORT   = 8002
KOKORO_PYTHON = ATHENA / "voice" / "kokoro_venv" / "Scripts" / "python.exe"
KOKORO_SERVER = ATHENA / "voice" / "kokoro_server.py"
PIPER_EXE     = ATHENA / "voice" / "piper" / "piper.exe"
PIPER_MODEL   = ATHENA / "voice" / "piper" / "en_US-lessac-medium.onnx"
MISO_DIR      = ATHENA / "voice" / "miso"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
WAKE_PHRASE       = "hi athena"

BACKEND_URL = "http://127.0.0.1:8000"

# ── Auto mic selection ────────────────────────────────────────────────────────

def _score_mic(name: str) -> int:
    """
    Score mic devices. Higher = preferred.

    Priority (no earbuds):
      headset/headphone > microphone array > single mic (headphone jack) > line

    The headphone jack "Microphone" input is silent without earbuds plugged in,
    so the built-in array must score HIGHER than the single mic entry.
    When earbuds are plugged in, override with VOICE_INPUT_DEVICE=1 in .env.
    """
    n = name.lower()
    if any(k in n for k in ("stereo mix", "loopback", "what u hear", "pc speaker")): return -100
    if "line" in n and "microphone" not in n: return 5      # UR22C line — last resort
    if any(k in n for k in ("headset", "headphone")): return 100
    if "array" in n: return 85                              # built-in array — works without earbuds
    if "microphone" in n and "array" not in n: return 40   # headphone jack — empty without earbuds
    if "mic" in n: return 30
    return 10

def _select_input_device():
    """
    Auto-select the best available microphone.
    Priority: headset/headphone > single microphone > array > line.
    Respects VOICE_INPUT_DEVICE env override.
    """
    override = os.getenv("VOICE_INPUT_DEVICE", "").strip()
    if override.isdigit():
        idx = int(override)
        try:
            d = sd.query_devices(idx, kind="input")
            return idx, int(d["default_samplerate"]), d["name"], min(d["max_input_channels"], 2)
        except Exception:
            pass

    best_idx, best_score, best_info = None, -999, None
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] < 1:
            continue
        score = _score_mic(d["name"])
        # Prefer MME host (indices <20) for lower latency on Windows
        if i < 20:
            score += 2
        if score > best_score:
            best_score = score
            best_idx   = i
            best_info  = d

    if best_info:
        return best_idx, int(best_info["default_samplerate"]), best_info["name"], min(best_info["max_input_channels"], 2)
    return None, TARGET_RATE, "default", 1

INPUT_DEVICE, DEVICE_RATE, DEVICE_NAME, DEVICE_CH = _select_input_device()

_g    = gcd(TARGET_RATE, DEVICE_RATE)
_UP   = TARGET_RATE  // _g
_DOWN = DEVICE_RATE  // _g
CHUNK_NATIVE = int(CHUNK_SAMPLES_16K * DEVICE_RATE / TARGET_RATE)

# ── Conversation history persistence ─────────────────────────────────────────
_HISTORY_FILE = ATHENA / "voice" / ".athena_history.json"
_HISTORY_MAX  = 40   # keep last 40 messages (~20 turns)

def _load_history() -> list:
    """Load conversation history from disk. Returns empty list if missing/corrupt."""
    try:
        if _HISTORY_FILE.exists():
            data = json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data[-_HISTORY_MAX:]
    except Exception:
        pass
    return []

def _save_history(history: list):
    """Persist conversation history to disk after each turn."""
    try:
        _HISTORY_FILE.write_text(
            json.dumps(history[-_HISTORY_MAX:], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass

# ── Model pre-warm cache ──────────────────────────────────────────────────────
# Models are loaded once at startup into these module-level variables.
# _voice_loop() reuses them instead of reloading on every start.
_oww_model      = None
_whisper_model  = None
_models_loading = False
_models_ready   = threading.Event()

# ── Voice state ───────────────────────────────────────────────────────────────

class VS:
    IDLE = "idle"; LOADING = "loading"; LISTENING = "listening"
    AWAKE = "awake"; THINKING = "thinking"; SPEAKING = "speaking"
    STOPPED = "stopped"

_state  = VS.IDLE
_active = False

# ── WebSocket manager ─────────────────────────────────────────────────────────

class VoiceConnectionManager:
    def __init__(self):
        self.clients = []
    async def connect(self, ws):
        await ws.accept(); self.clients.append(ws)
    def disconnect(self, ws):
        if ws in self.clients: self.clients.remove(ws)
    async def broadcast(self, data):
        dead = []
        for ws in self.clients:
            try: await ws.send_json(data)
            except: dead.append(ws)
        for ws in dead: self.disconnect(ws)

voice_manager = VoiceConnectionManager()
_loop = None

def _emit(event, **kwargs):
    global _loop
    if _loop and voice_manager.clients:
        payload = {"type": f"voice_{event}", "ts": datetime.now().isoformat(), **kwargs}
        asyncio.run_coroutine_threadsafe(voice_manager.broadcast(payload), _loop)

# ── Agent context loader ──────────────────────────────────────────────────────

_agent_contexts = {}

def _load_agent_context(name: str) -> str:
    """Load agent persona from .claude/agents/<name>.md — cached in memory."""
    if name in _agent_contexts:
        return _agent_contexts[name]
    for fname in [f"{name}.md", f"{name}-agent.md"]:
        f = RULES / fname
        if f.exists():
            text = f.read_text(encoding="utf-8")
            _agent_contexts[name] = text
            return text
    return ""

# ── Intent classification via Claude tool-use ─────────────────────────────────
# Athena uses Claude Haiku to decide whether a query should trigger a background
# agent. No regex pattern-matching — Claude reasons about the request in context,
# handles paraphrases and ambiguity, and generates the spoken confirmation itself.

_AGENT_TOOL_SCHEMA = {
    "name": "trigger_agent",
    "description": (
        "Trigger one of Athena's background agents when Steven explicitly asks for a "
        "task to be run. Only call this tool when the user is making a clear request "
        "to execute a task — NOT for questions you can answer conversationally. "
        "When in doubt, do NOT call this tool and answer directly instead."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "agent": {
                "type": "string",
                "enum": [
                    "content",             # Write/draft a Substack article or content piece
                    "briefing",            # Daily market and industry briefing
                    "rag",                 # Ingest / update the knowledge base
                    "iso",                 # Generate an ISO 13485 coaching clause
                    "coaching_brief",      # Generate a coaching brief for a named client
                    "consulting",          # Run the consulting frameworks/methodology agent
                    "ma",                  # Run the M&A intelligence agent
                    "marketing",           # Weekly marketing brief (default)
                    "marketing_plan",      # 30-60-90 day guerilla marketing plan
                    "marketing_events",    # Upcoming MedTech events calendar
                    "marketing_scorecard", # Marketing pipeline KPI scorecard
                    "marketing_outreach",  # Personalised outreach copy for a specific target
                ],
                "description": "The agent to trigger.",
            },
            "override": {
                "type": "string",
                "description": (
                    "Optional extra context passed to the agent: a topic focus, "
                    "client name (for coaching_brief), outreach target name or company "
                    "(for marketing_outreach), or a search/analysis query. "
                    "Leave empty string if not applicable."
                ),
            },
            "confirmation": {
                "type": "string",
                "description": (
                    "Spoken confirmation for Steven. Exactly two sentences. British English. No markdown or lists. "
                    "Sentence 1: name the agent and describe the specific deliverable "
                    "(e.g. 'Running your Daily Briefing — pulling market intel and your pipeline updates.'). "
                    "Sentence 2: estimated delivery time "
                    "(e.g. 'Expect your brief in about two minutes.'). "
                    "Be specific: if override context is given (client name, topic, target), name it."
                ),
            },
        },
        "required": ["agent", "override", "confirmation"],
    },
}

_CLASSIFY_SYSTEM = (
    "You are the intent classifier for Athena, a voice assistant for Latitude MedTech LLC. "
    "Steven Tran (CEO) is speaking to you. Your only job is to decide whether his request "
    "should trigger a background agent, or whether you should answer conversationally.\n\n"
    "TRIGGER an agent only when Steven explicitly asks to RUN a task: "
    "'generate', 'draft', 'write', 'run', 'start', 'give me my [X]', 'what's the pipeline', "
    "'outreach for [person]', 'brief for [client]', etc.\n\n"
    "DO NOT trigger an agent for:\n"
    "- Questions you can answer directly ('What is ISO 13485?', 'How long does a 510k take?')\n"
    "- Ambiguous requests where you're unsure\n"
    "- Conversational follow-ups to previous answers\n\n"
    "If you call trigger_agent, the 'confirmation' field is what Athena will speak aloud. "
    "Keep it to one short sentence, British English, no markdown."
)


def _classify_intent(text: str, history: list):
    """
    Ask Claude Haiku (with tool_use) whether this query should trigger an agent.
    Returns (agent_id, override, confirmation_text) or (None, None, None).
    Falls through to the conversational path if classification fails or no tool is called.
    """
    try:
        import anthropic as _ant
        client = _ant.Anthropic(api_key=ANTHROPIC_API_KEY)
        recent = history[-6:] if len(history) > 6 else history
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=256,
            system=_CLASSIFY_SYSTEM,
            tools=[_AGENT_TOOL_SCHEMA],
            tool_choice={"type": "auto"},
            messages=recent + [{"role": "user", "content": text}],
        )
        for block in resp.content:
            if getattr(block, "type", None) == "tool_use" and block.name == "trigger_agent":
                inp = block.input
                return (
                    inp.get("agent"),
                    inp.get("override", ""),
                    inp.get("confirmation", ""),
                )
        return None, None, None
    except Exception as e:
        print(f"[voice] Intent classification failed, falling through to conversation: {e}")
        return None, None, None

def _trigger_agent(agent_id: str, override: str = "") -> bool:
    """Fire an agent via the local FastAPI backend. Returns True if accepted."""
    # Map intent ids → endpoint + payload builder
    def _marketing_payload(mode, target=""):
        return json.dumps({"mode": mode, "target": target}).encode()

    ROUTE_MAP = {
        "content":            ("/api/agents/content",    lambda o: json.dumps({"override": o}).encode()),
        "briefing":           ("/api/agents/briefing",   lambda o: json.dumps({"override": o}).encode()),
        "rag":                ("/api/agents/rag",        lambda o: json.dumps({"override": o}).encode()),
        "iso":                ("/api/agents/iso",        lambda _: json.dumps({}).encode()),
        "coaching_brief":     ("/api/agents/brief",      lambda o: json.dumps({"client": o}).encode()),
        "consulting":         ("/api/agents/consulting", lambda _: json.dumps({"mode": "learn"}).encode()),
        "ma":                 ("/api/agents/ma",         lambda o: json.dumps({"mode": "learn", "topic": o}).encode()),
        "marketing":          ("/api/agents/marketing",  lambda _: _marketing_payload("brief")),
        "marketing_plan":     ("/api/agents/marketing",  lambda _: _marketing_payload("plan")),
        "marketing_events":   ("/api/agents/marketing",  lambda _: _marketing_payload("events")),
        "marketing_scorecard":("/api/agents/marketing",  lambda _: _marketing_payload("scorecard")),
        "marketing_outreach": ("/api/agents/marketing",  lambda t: _marketing_payload("outreach", t)),
    }
    route = ROUTE_MAP.get(agent_id)
    if not route:
        return False
    ep, build_payload = route
    try:
        payload = build_payload(override)
        req = urllib.request.Request(
            f"{BACKEND_URL}{ep}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5):
            pass
        _emit("voice_agent_queued",
              agentId=agent_id,
              label=_AGENT_LABELS.get(agent_id, agent_id),
              context=override,
              etaSeconds=_AGENT_ETA_SECONDS.get(agent_id, 120))
        return True
    except Exception:
        return False

_AGENT_LABELS = {
    "content":            "Content Draft",
    "briefing":           "Daily Briefing",
    "rag":                "RAG Ingestion",
    "iso":                "ISO 13485 Coach",
    "coaching_brief":     "Coaching Brief",
    "consulting":         "Consulting Agent",
    "ma":                 "M&A Intelligence",
    "marketing":          "Marketing Brief",
    "marketing_plan":     "Marketing Plan",
    "marketing_events":   "Events Calendar",
    "marketing_scorecard":"Marketing Scorecard",
    "marketing_outreach": "Outreach Copy",
}

_AGENT_ETA = {
    "content":             "about three to five minutes",
    "briefing":            "about two minutes",
    "rag":                 "about a minute",
    "iso":                 "about a minute",
    "coaching_brief":      "about two minutes",
    "consulting":          "two to three minutes",
    "ma":                  "three to four minutes",
    "marketing":           "about two minutes",
    "marketing_plan":      "three to five minutes",
    "marketing_events":    "about a minute",
    "marketing_scorecard": "about two minutes",
    "marketing_outreach":  "about a minute",
}

_AGENT_ETA_SECONDS = {
    "content":             240,
    "briefing":            120,
    "rag":                  60,
    "iso":                  60,
    "coaching_brief":      120,
    "consulting":          180,
    "ma":                  210,
    "marketing":           120,
    "marketing_plan":      300,
    "marketing_events":     60,
    "marketing_scorecard": 120,
    "marketing_outreach":   60,
}

# Queue of short spoken notifications Athena delivers between listening turns.
# Populated by the /api/voice/notify endpoint; drained in _voice_loop.
_notification_queue: deque = deque()

# ── Kokoro persistent server ──────────────────────────────────────────────────

_kokoro_proc = None

def _start_kokoro_server():
    global _kokoro_proc
    if not KOKORO_PYTHON.exists() or not KOKORO_SERVER.exists():
        return False
    # Already running?
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{KOKORO_PORT}/health", timeout=1):
            return True
    except Exception:
        pass

    env = {**os.environ, "HF_HUB_DISABLE_SYMLINKS_WARNING": "1"}
    _kokoro_proc = subprocess.Popen(
        [str(KOKORO_PYTHON), str(KOKORO_SERVER), str(KOKORO_PORT)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    # Wait up to 30 s for model to load
    for _ in range(60):
        time.sleep(0.5)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{KOKORO_PORT}/health", timeout=1):
                return True
        except Exception:
            pass
        if _kokoro_proc.poll() is not None:
            return False  # crashed
    return False

def _stop_kokoro_server():
    try:
        urllib.request.urlopen(
            urllib.request.Request(f"http://127.0.0.1:{KOKORO_PORT}/shutdown",
                                   method="POST"), timeout=2)
    except Exception:
        pass
    if _kokoro_proc:
        _kokoro_proc.terminate()

# ── Audio helpers ─────────────────────────────────────────────────────────────

def _to_mono_float(chunk):
    f = chunk.astype(np.float32)
    if f.max() > 1.0: f /= 32768.0
    if f.ndim == 2:   f = f.mean(axis=1)
    return f

def _resample(audio_f32):
    if DEVICE_RATE == TARGET_RATE: return audio_f32
    return resample_poly(audio_f32, _UP, _DOWN).astype(np.float32)

def _rms(chunk_f32):
    return float(np.sqrt(np.mean(chunk_f32 ** 2)))

def _chunk_is_speech(chunk_f32_16k: np.ndarray) -> bool:
    """True if the 16 kHz chunk likely contains human speech (not keyboard/ambient noise)."""
    if _vad is None:
        return True
    frame = chunk_f32_16k[:_VAD_FRAME]
    if len(frame) < _VAD_FRAME:
        return True
    pcm = (frame * 32768).clip(-32768, 32767).astype(np.int16).tobytes()
    try:
        return _vad.is_speech(pcm, TARGET_RATE)
    except Exception:
        return True

def _play_chime(activate=True):
    """
    Activation: crisp 2-tone ascending chime (200ms, 0.5 vol) — unmistakably heard.
    Done: single soft descending note (suppress by default).
    """
    try:
        if activate:
            # Two-tone ascending — clearly signals "I'm listening"
            dur = 0.10
            t   = np.linspace(0, dur, int(TARGET_RATE * dur), False)
            lo  = np.sin(2 * np.pi * 880  * t) * 0.5
            hi  = np.sin(2 * np.pi * 1320 * t) * 0.5
            wave = np.concatenate([lo, hi]).astype(np.float32)
        else:
            # Soft single descending note — end of response
            dur  = 0.08
            t    = np.linspace(0, dur, int(TARGET_RATE * dur), False)
            wave = (np.sin(2 * np.pi * 660 * t) * 0.3).astype(np.float32)
        sd.play(wave, TARGET_RATE)
        sd.wait()
    except Exception:
        pass

# ── Self-optimisation tracking ────────────────────────────────────────────────

_session_stats = {
    "queries":          0,
    "empty_transcripts": 0,
    "latencies_ms":     [],
}

def _track_query(latency_ms: float, empty: bool = False,
                 stt_logprob: float = 0.0, wake_score: float = 0.0,
                 transcript: str = "", stt_ms: float = 0.0):
    """
    Log per-query stats; adjust silence threshold if too many false starts.
    Now also writes rich telemetry to query_telemetry.jsonl for ML training.
    """
    global SILENCE_THRESHOLD
    _session_stats["queries"] += 1
    _session_stats["latencies_ms"].append(latency_ms)
    if empty:
        _session_stats["empty_transcripts"] += 1

    # Write ML telemetry for every query — used by voice_optimizer & whisper_finetuner
    _log_query_telemetry({
        "ts":                datetime.now().isoformat(),
        "transcript_words":  len(transcript.split()) if transcript else 0,
        "stt_logprob":       round(stt_logprob, 4),
        "wake_score":        round(wake_score, 4),
        "stt_latency_ms":    round(stt_ms),
        "total_latency_ms":  round(latency_ms),
        "empty":             empty,
        "silence_threshold": SILENCE_THRESHOLD,
        "wake_threshold":    WAKE_THRESHOLD,
        "whisper_model":     WHISPER_MODEL,
    })

    # Self-optimise: if >40% of activations produce empty transcripts,
    # the silence threshold is too low — tighten it to reduce false triggers.
    q = _session_stats["queries"]
    if q >= 10:
        empty_rate = _session_stats["empty_transcripts"] / q
        if empty_rate > 0.40 and SILENCE_THRESHOLD < 0.05:
            SILENCE_THRESHOLD = round(min(SILENCE_THRESHOLD * 1.25, 0.05), 4)
            _emit("info", message=f"Auto-tuned silence threshold to {SILENCE_THRESHOLD}")
        elif empty_rate < 0.10 and SILENCE_THRESHOLD > 0.008:
            SILENCE_THRESHOLD = round(max(SILENCE_THRESHOLD * 0.9, 0.008), 4)

    # Report to HR memory every 20 queries
    if q % 20 == 0 and _has_memory and _mem:
        avg_ms = sum(_session_stats["latencies_ms"][-20:]) / 20
        _mem.log_event("voice_bridge", "self_optimise",
                       metadata={"avg_latency_ms": round(avg_ms),
                                 "empty_rate": round(empty_rate if q >= 10 else 0, 3),
                                 "silence_threshold": SILENCE_THRESHOLD,
                                 "avg_stt_logprob": round(stt_logprob, 3),
                                 "avg_wake_score": round(wake_score, 3)})

# ── Wake word ─────────────────────────────────────────────────────────────────

def _load_wake_model():
    try:
        from openwakeword.model import Model
        custom = ATHENA / "voice" / "wake" / "hi_athena.onnx"
        if custom.exists():
            return Model(wakeword_models=[str(custom)], inference_framework="onnx")
        return Model(wakeword_models=["alexa"], inference_framework="onnx")
    except Exception as e:
        _emit("error", message=f"Wake word model failed: {e}")
        return None

def _preload_models():
    """
    Pre-warm OWW, Whisper, AND Kokoro in a background thread at server startup.
    _models_ready fires only after all three are up so the startup script's
    readiness gate and the voice loop both have a single reliable signal.
    """
    global _oww_model, _whisper_model, _models_loading, _models_ready
    if _models_loading:
        return
    _models_loading = True

    def _load():
        global _oww_model, _whisper_model
        try:
            _emit("loading", message="Loading wake word model…")
            _oww_model = _load_wake_model()
            _emit("loading", message="Loading Whisper transcription model…")
            _whisper_model = _load_whisper()
            if TTS_BACKEND == "kokoro":
                _emit("loading", message="Starting Kokoro TTS server…")
                _start_kokoro_server()   # blocks until Kokoro health-check passes
            _emit("loading", message="All systems ready.")
        except Exception as e:
            _emit("error", message=f"Model preload failed: {e}")
        finally:
            _models_ready.set()

    t = threading.Thread(target=_load, daemon=True, name="model-preloader")
    t.start()

def _listen_for_wake(oww_model):
    """
    Stream mic → resample → openwakeword. Returns (detected: bool, max_score: float).
    max_score is the highest OWW confidence seen at detection — logged for threshold tuning.
    Robust: catches device errors, re-opens stream, keeps listening.
    """
    level_every = max(1, int(0.1 * DEVICE_RATE / CHUNK_NATIVE))
    n = 0
    retry_delay = 0.5
    while _active:
        try:
            with sd.InputStream(device=INPUT_DEVICE, samplerate=DEVICE_RATE,
                                channels=DEVICE_CH, dtype="int16",
                                blocksize=CHUNK_NATIVE) as stream:
                while _active:
                    chunk, _ = stream.read(CHUNK_NATIVE)
                    mono = _to_mono_float(chunk)
                    rs   = _resample(mono)
                    n += 1
                    if n % level_every == 0:
                        _emit("level", level=round(min(1.0, _rms(mono) * 8), 3))
                    if _chunk_is_speech(rs):
                        i16 = (rs * 32768).clip(-32768, 32767).astype(np.int16)
                        pred = oww_model.predict(i16)
                        max_score = max(pred.values()) if pred else 0.0
                        for _, score in pred.items():
                            if score >= WAKE_THRESHOLD:
                                return True, round(float(max_score), 4)
        except Exception as e:
            # Audio device hiccup — wait briefly and retry instead of crashing
            _emit("level", level=0.0)
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 1.5, 3.0)  # back off up to 3s
    return False, 0.0

# ── STT ───────────────────────────────────────────────────────────────────────

def _load_whisper():
    from faster_whisper import WhisperModel
    # Use CUDA if available (RTX 4070 → ~50ms vs ~400ms on CPU)
    try:
        import torch
        if torch.cuda.is_available():
            _emit("loading", message=f"Whisper loading on GPU ({torch.cuda.get_device_name(0)})…")
            return WhisperModel(WHISPER_MODEL, device="cuda", compute_type="float16")
    except Exception:
        pass
    return WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")

def _record_query():
    frames = []
    silence = 0
    sil_chunks = int(SILENCE_DURATION * TARGET_RATE / CHUNK_SAMPLES_16K)
    max_chunks  = int(MAX_RECORD_SEC  * TARGET_RATE / CHUNK_SAMPLES_16K)
    with sd.InputStream(device=INPUT_DEVICE, samplerate=DEVICE_RATE,
                        channels=DEVICE_CH, dtype="int16",
                        blocksize=CHUNK_NATIVE) as stream:
        while len(frames) < max_chunks and _active:
            chunk, _ = stream.read(CHUNK_NATIVE)
            mono = _to_mono_float(chunk)
            rs   = _resample(mono)
            _emit("level", level=round(min(1.0, _rms(mono) * 8), 3))
            frames.append(rs)
            is_speech = _chunk_is_speech(rs)
            silence = silence + 1 if (_rms(mono) < SILENCE_THRESHOLD or not is_speech) else 0
            if silence >= sil_chunks: break
    _emit("level", level=0.0)
    return np.concatenate(frames) if frames else np.array([], dtype=np.float32)

_LOW_CONFIDENCE_THRESHOLD = -0.7   # avg_logprob below this = uncertain transcript

# ── ML telemetry & sample capture ────────────────────────────────────────────
TELEMETRY_FILE = ATHENA / "voice" / "query_telemetry.jsonl"
SAMPLES_DIR    = ATHENA / "voice" / "samples"

# Reads capture_samples flag from settings.json at module load.
# Set to true in settings.json to save WAV clips for Whisper fine-tuning.
_CAPTURE_SAMPLES = False
try:
    _cfg_path = ATHENA / "settings.json"
    if _cfg_path.exists():
        _CAPTURE_SAMPLES = json.loads(_cfg_path.read_text(encoding="utf-8")).get(
            "voice", {}).get("capture_samples", False)
except Exception:
    pass


def _log_query_telemetry(data: dict):
    """Append one per-query telemetry record to query_telemetry.jsonl."""
    try:
        with open(TELEMETRY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
    except Exception:
        pass


def _save_audio_sample(audio: np.ndarray, transcript: str, avg_logprob: float):
    """
    Save a WAV clip + JSON sidecar to voice/samples/ for Whisper fine-tuning.
    Only saves when capture_samples=true and the transcript is non-empty.
    Confident transcripts (avg_logprob > -0.5) are labelled as training-ready.
    """
    if not _CAPTURE_SAMPLES or not transcript.strip():
        return
    try:
        SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
        ts  = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
        key = hashlib.md5(transcript.encode()).hexdigest()[:6]
        wav_path  = SAMPLES_DIR / f"{ts}_{key}.wav"
        meta_path = SAMPLES_DIR / f"{ts}_{key}.json"
        sf.write(str(wav_path), audio, TARGET_RATE)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "transcript": transcript,
                "avg_logprob": round(avg_logprob, 4),
                "training_ready": avg_logprob > -0.5,
                "ts": datetime.now().isoformat(),
            }, f)
    except Exception:
        pass

# Domain vocabulary injected as Whisper's initial_prompt.
# Biases the decoder toward MedTech/regulatory terms before any LLM correction,
# catching substitutions like "part of FDA 483s" → "report of FDA 483s"
# at zero latency cost (no extra API call).
_WHISPER_DOMAIN_PROMPT = (
    "Latitude MedTech, FDA 483, Form 483, 483 observations, inspectional observations, "
    "warning letter, FDA report, ISO 13485, 510(k), PMA, De Novo, CAPA, QMS, MDR, "
    "MDSAP, CFR 820, CFR 21, medical device, regulatory submission, predicate device, "
    "substantial equivalence, design controls, risk management, clinical evaluation, "
    "post-market surveillance, adverse event, recall, field safety, FDA audit, "
    "generate report, draft briefing, run briefing, M&A report, pipeline report, "
    "Steven, Latitude MedTech, San Diego."
)

def _transcribe(whisper_model, audio):
    """
    Transcribe audio. Returns (text, confident: bool, avg_logprob: float).
    avg_logprob per segment: 0 = perfect, -1 = poor. Threshold -0.7.
    avg_logprob is now returned so callers can log it for ML training.
    """
    if audio.size == 0:
        return "", True, 0.0
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp = f.name
    try:
        sf.write(tmp, audio, TARGET_RATE)
        segs_iter, _ = whisper_model.transcribe(
            tmp, language="en", beam_size=5, vad_filter=True,
            initial_prompt=_WHISPER_DOMAIN_PROMPT)
        segs = list(segs_iter)
        text = " ".join(s.text.strip() for s in segs).strip()
        # Confidence: average log-prob across segments (higher = better)
        if segs:
            avg_lp = sum(s.avg_logprob for s in segs) / len(segs)
            confident = avg_lp >= _LOW_CONFIDENCE_THRESHOLD
        else:
            avg_lp  = 0.0
            confident = True
        return text, confident, avg_lp
    finally:
        try: os.unlink(tmp)
        except: pass


def _correct_transcript(raw: str) -> str:
    """
    Silent LLM correction for low-confidence transcripts.
    Sends the raw Whisper output to Claude Haiku with a MedTech-aware
    correction prompt. Returns the corrected text, or raw if the call fails.
    Fast: ~200 ms on typical broadband.
    """
    if not ANTHROPIC_API_KEY or not raw:
        return raw
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=120,
            system=(
                "You are a speech-to-text correction assistant for a MedTech regulatory executive. "
                "Fix transcription errors — wrong homophones, missing words, garbled STT output — "
                "while preserving the speaker's intent exactly.\n\n"
                "Key domain vocabulary (prefer these over phonetically similar common words):\n"
                "- Documents: report, briefing, brief, memorandum, submission, filing\n"
                "- FDA: FDA 483, Form 483, 483 observations, inspectional observations, "
                "warning letter, untitled letter, consent decree, import alert\n"
                "- Regulatory: ISO 13485, 510(k), PMA, De Novo, MDSAP, MDR, CFR 820, "
                "CAPA, QMS, design controls, risk management, post-market surveillance\n"
                "- Actions: generate, draft, run, analyze, summarize, pull, find, search\n"
                "- People/places: Steven, Latitude MedTech, San Diego\n\n"
                "If the text is already correct, return it unchanged. "
                "Return ONLY the corrected text with no explanation or punctuation changes."
            ),
            messages=[{"role": "user", "content": f"Correct this transcript: {raw}"}],
        )
        corrected = resp.content[0].text.strip()
        return corrected if corrected else raw
    except Exception:
        return raw

# ── LLM ───────────────────────────────────────────────────────────────────────

def _build_system_prompt():
    # Load CLAUDE.md core values + voice-specific additions
    claude_md = ATHENA.parent / "CLAUDE.md"
    firm_context = ""
    if claude_md.exists():
        raw = claude_md.read_text(encoding="utf-8")
        # Extract just the values + north star sections (keep prompt lean)
        for section in ["## Core Values", "## North Star", "## Two Business Lines"]:
            start = raw.find(section)
            if start != -1:
                end = raw.find("\n## ", start + 1)
                firm_context += raw[start:end if end != -1 else start + 600] + "\n"

    # KB context for the query topic
    kb_context = ""
    if _kb and _kb.has_content():
        # Will be injected per-query; placeholder here
        pass

    return (
        "You are Athena, the voice assistant and chief of staff for Latitude MedTech LLC — "
        "a MedTech and Pharma management consulting firm in San Diego, CA. "
        "You serve Steven Tran, Managing Partner and CEO.\n\n"
        f"{firm_context}\n"
        "You can trigger agents on Steven's behalf when he asks for: content drafts, "
        "daily briefings, knowledge base updates, ISO coaching, coaching briefs, "
        "or marketing tasks (weekly brief, 30-60-90 plan, outreach copy, events calendar, "
        "pipeline status).\n\n"
        "VOICE RULES — follow strictly:\n"
        "- Conversational British English. Use contractions naturally: don't, can't, it's, I'd, you'll.\n"
        "- No markdown, lists, bullet points, asterisks, or symbols — these won't render in speech.\n"
        "- Maximum 2 sentences. Never more unless explicitly asked.\n"
        "- Answer first. Cut all preamble and restating the question.\n"
        "- Vary sentence length for natural rhythm — mix short punchy sentences with longer ones.\n"
        "- Speak like a trusted colleague, not a formal report.\n"
        "- Agent confirmations: one sentence only.\n"
        "DISCLAIMER: Regulatory content is educational. Not licensed advice."
    )

# ── TTS text pre-processing ───────────────────────────────────────────────────
# Cleans LLM output before it hits Kokoro: strips markdown remnants, expands
# MedTech shorthand that Kokoro would mangle, and normalises symbols.

_TTS_SUBS = [
    (re.compile(r'\*+([^*]+)\*+'),          r'\1'),          # bold/italic markdown
    (re.compile(r'`([^`]+)`'),              r'\1'),          # inline code
    (re.compile(r'^#+\s*', re.MULTILINE),   ''),             # heading hashes
    (re.compile(r'\b510\(k\)', re.I),       'five-ten-K'),
    (re.compile(r'\b510k\b',   re.I),       'five-ten-K'),
    (re.compile(r'\bISO\s*13485\b'),        'I S O thirteen four eighty-five'),
    (re.compile(r'\bCAPAs?\b'),             'CAPA'),         # already word-like; keep
    (re.compile(r'\bFDA\b'),                'F D A'),
    (re.compile(r'\bQMS\b'),                'Q M S'),
    (re.compile(r'\bMDR\b'),                'M D R'),
    (re.compile(r'\bPMA\b'),                'P M A'),
    (re.compile(r'\bMDSAP\b'),              'M D S A P'),
    (re.compile(r'\bUDI\b'),                'U D I'),
    (re.compile(r'\bRAQA\b'),               'R A Q A'),
    (re.compile(r'&'),                      'and'),
    (re.compile(r'\s{2,}'),                 ' '),            # collapse extra spaces
]

def _preprocess_tts(text: str) -> str:
    for pattern, repl in _TTS_SUBS:
        text = pattern.sub(repl, text)
    return text.strip()


_SENTENCE_END = re.compile(r'(?<=[.!?])\s+')

def _split_sentences(text: str) -> list:
    """Split text into speakable sentence chunks."""
    parts = _SENTENCE_END.split(text.strip())
    return [p.strip() for p in parts if p.strip()]

def _ask_claude_streaming(text: str, history: list, kb_ctx: str = "") -> str:
    """
    CAPA-Voice-001 fix: stream Claude response and TTS each sentence immediately.
    First audio plays in ~1.2 s instead of waiting for the full response.
    Returns the complete response text for history logging.
    """
    if not ANTHROPIC_API_KEY:
        _speak_sentence("API key not configured.")
        return "API key not configured."
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        system = _build_system_prompt()
        if kb_ctx:
            system += f"\n\nRELEVANT KNOWLEDGE:\n{kb_ctx}"
        msgs = [{"role": m["role"], "content": m["content"]} for m in history]
        msgs.append({"role": "user", "content": text})

        full_text = ""
        buffer    = ""

        with client.messages.stream(
            model="claude-haiku-4-5",
            max_tokens=120,
            system=system,
            messages=msgs,
        ) as stream:
            for chunk in stream.text_stream:
                full_text += chunk
                buffer    += chunk
                # Flush buffer to TTS at each sentence boundary
                if _SENTENCE_END.search(buffer):
                    sentences = _SENTENCE_END.split(buffer)
                    for s in sentences[:-1]:
                        s = s.strip()
                        if s:
                            # Phase 2A: emit each sentence to UI as it's spoken
                            _emit("speaking_partial", sentence=s)
                            _speak_sentence(s)
                    buffer = sentences[-1]

        # Flush any remaining text
        if buffer.strip():
            _emit("speaking_partial", sentence=buffer.strip())
            _speak_sentence(buffer.strip())

        if _has_memory and _mem:
            _mem.log_event("voice_bridge", "query",
                           subject=text[:200], metadata={"response": full_text[:200]})
        return full_text.strip()

    except Exception as e:
        msg = "I ran into an error, please try again."
        _speak_sentence(msg)
        return msg

# Keep non-streaming fallback for agent confirmations (short, single sentence)
def _ask_claude(text: str, history: list, kb_ctx: str = "") -> str:
    return _ask_claude_streaming(text, history, kb_ctx)

# ── TTS ───────────────────────────────────────────────────────────────────────

KOKORO_SPEED           = float(os.getenv("VOICE_KOKORO_SPEED",         "0.92"))
ELEVENLABS_API_KEY     = os.getenv("VOICE_ELEVENLABS_API_KEY",    "")
ELEVENLABS_VOICE_ID    = os.getenv("VOICE_ELEVENLABS_VOICE_ID",   "9BWtsMINqrJLrRacOk9x")
ELEVENLABS_MODEL       = os.getenv("VOICE_ELEVENLABS_MODEL",      "eleven_turbo_v2_5")
ELEVENLABS_SAMPLE_RATE = 24000

def _speak_elevenlabs(text: str):
    """
    Stream PCM audio from ElevenLabs and play via sounddevice.
    pcm_24000 = raw 16-bit signed PCM at 24 kHz — no decode overhead.
    eleven_turbo_v2_5 targets ~150 ms first-byte latency.
    """
    from elevenlabs.client import ElevenLabs
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    audio_gen = client.text_to_speech.convert(
        text=text,
        voice_id=ELEVENLABS_VOICE_ID,
        model_id=ELEVENLABS_MODEL,
        output_format="pcm_24000",
    )
    pcm = b"".join(audio_gen)
    audio_arr = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    sd.play(audio_arr, ELEVENLABS_SAMPLE_RATE)
    sd.wait()

def _speak_kokoro(text: str):
    """Send text to persistent Kokoro server, play returned WAV."""
    payload = json.dumps({"text": text, "voice": KOKORO_VOICE, "speed": KOKORO_SPEED}).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{KOKORO_PORT}/speak",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        wav_bytes = resp.read()
    buf  = io.BytesIO(wav_bytes)
    data, sr = sf.read(buf)
    sd.play(data.astype(np.float32), sr)

def _speak_sentence(text: str):
    """
    Sentence-level TTS — called per sentence during streaming.
    Plays synchronously (waits for audio to finish) before next sentence TTS starts.
    """
    text = _preprocess_tts(text)
    if not text:
        return
    try:
        if TTS_BACKEND == "elevenlabs":
            _speak_elevenlabs(text)
        elif TTS_BACKEND == "piper":
            _speak_piper(text)
        elif TTS_BACKEND == "miso":
            raise NotImplementedError("Miso API not yet available")
        else:
            _speak_kokoro(text)
            sd.wait()   # block until this sentence finishes
    except Exception:
        try:
            import pyttsx3
            e = pyttsx3.init(); e.setProperty("rate", 175)
            e.say(text); e.runAndWait()
        except Exception:
            pass
    # Pause after TTS — lets room echo decay so the mic doesn't hear Athena's own voice
    time.sleep(0.4)

def _speak_piper(text: str):
    if not (PIPER_EXE.exists() and PIPER_MODEL.exists()):
        raise FileNotFoundError("Piper not found")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        out = f.name
    try:
        proc = subprocess.run(
            [str(PIPER_EXE), "--model", str(PIPER_MODEL), "--output_file", out],
            input=text.encode("utf-8"), capture_output=True, timeout=15)
        if proc.returncode == 0 and Path(out).stat().st_size > 0:
            data, sr = sf.read(out)
            sd.play(data.astype(np.float32), sr); sd.wait(); return
        raise RuntimeError("Piper failed")
    finally:
        try: os.unlink(out)
        except: pass

def _speak(text: str):
    try:
        if TTS_BACKEND == "elevenlabs":
            _speak_elevenlabs(text)
        elif TTS_BACKEND == "piper":
            _speak_piper(text)
        elif TTS_BACKEND == "miso":
            raise NotImplementedError("Miso API not yet available")
        else:
            _speak_kokoro(text)
    except Exception:
        try:
            import pyttsx3
            e = pyttsx3.init(); e.setProperty("rate", 175)
            e.say(text); e.runAndWait()
        except Exception: pass

def _post_response_cooldown(oww_model):
    """
    After TTS finishes, prevent the speaker audio from echoing back into the mic
    and falsely triggering wake word detection or filling _record_query with
    non-silent audio. Strategy:
      1. Wait for the Windows audio pipeline to fully drain (speaker reverb dies out).
      2. Open the mic and discard ~0.75 s of buffered audio.
      3. Reset the OWW model's accumulated prediction scores.
    """
    time.sleep(1.0)
    try:
        flush_chunks = int(1.5 * DEVICE_RATE / CHUNK_NATIVE)
        with sd.InputStream(device=INPUT_DEVICE, samplerate=DEVICE_RATE,
                            channels=DEVICE_CH, dtype="int16",
                            blocksize=CHUNK_NATIVE) as stream:
            for _ in range(flush_chunks):
                stream.read(CHUNK_NATIVE)
    except Exception:
        pass
    try:
        oww_model.reset()
    except Exception:
        pass

# ── Main voice loop ───────────────────────────────────────────────────────────

def _voice_loop():
    global _state

    # Skip loading state entirely if models are already warm from startup preload
    already_ready = _models_ready.is_set()

    if not already_ready:
        _state = VS.LOADING
        _emit("loading", message=f"Mic: {DEVICE_NAME} @ {DEVICE_RATE} Hz")

    # Ensure Kokoro is running (fast no-op health check if already up)
    # If preload hasn't finished yet (very fast launch), wait for it
    if not already_ready:
        _emit("loading", message="Waiting for models to finish loading…")
        _models_ready.wait(timeout=90)

    oww     = _oww_model
    whisper = _whisper_model
    history = _load_history()

    if oww is None:
        _state = VS.STOPPED
        _emit("stopped", reason="Wake word model failed"); return

    _state = VS.LISTENING
    _emit("listening", message="Say 'Alexa' to activate")

    while _active:
        # Deliver queued agent-completion notifications before the next listen cycle.
        if _notification_queue:
            while _notification_queue and _active:
                note = _notification_queue.popleft()
                _state = VS.SPEAKING
                _emit("speaking", response=note)
                for s in _split_sentences(note):
                    _emit("speaking_partial", sentence=s)
                    _speak_sentence(s)
                _post_response_cooldown(oww)
            if not _active:
                break
            _state = VS.LISTENING
            _emit("listening", message="Say 'Alexa' to activate")

        wake_detected, wake_score = _listen_for_wake(oww)
        if not wake_detected or not _active:
            break

        _state = VS.AWAKE
        _emit("awake", message="Recording…")
        _play_chime(True)          # clear 2-tone chime — user hears "I'm listening"

        try:
            audio = _record_query()
        except Exception as e:
            # Audio device hiccup during recording — log and keep listening.
            _emit("info", message=f"Recording error (retrying): {e}")
            _state = VS.LISTENING
            _emit("listening", message="Say 'Alexa' to activate")
            time.sleep(0.5)
            continue

        stt_t0 = time.time()
        try:
            text, confident, avg_logprob = _transcribe(whisper, audio)
        except Exception as e:
            _emit("info", message=f"Transcription error (retrying): {e}")
            _state = VS.LISTENING
            _emit("listening", message="Say 'Alexa' to activate")
            continue
        stt_ms = (time.time() - stt_t0) * 1000

        empty = not bool(text)
        _track_query(0, empty=empty, stt_logprob=avg_logprob,
                     wake_score=wake_score, transcript=text, stt_ms=stt_ms)

        # Save audio clip for ML training when enabled
        if text:
            _save_audio_sample(audio, text, avg_logprob)

        if not text:
            _state = VS.LISTENING
            _emit("listening", message="No speech detected — listening again")
            continue

        # Always run LLM correction — Whisper can be confident but still wrong
        # on domain-specific terms (e.g. "part of FDA 483s" → "report of FDA 483s").
        # Falls back to raw text if the correction call fails.
        try:
            corrected = _correct_transcript(text)
            if corrected != text:
                _emit("transcript", text=f"{corrected}  [corrected]")
                text = corrected
            else:
                tag = "" if confident else "  [low conf]"
                _emit("transcript", text=f"{text}{tag}")

            # ── Intent classification: LLM-driven, not regex ──────────────────
            # Haiku+tool_use decides whether to dispatch an agent or fall through
            # to the full conversational path. Classification adds ~200ms but only
            # fires when Haiku returns a tool_use block — conversational turns
            # proceed to streaming Sonnet as before.
            _state = VS.THINKING
            _emit("thinking", query=text)
            agent_id, override, confirm = _classify_intent(text, history)
            if agent_id:
                ok = _trigger_agent(agent_id, override or "")
                if not ok:
                    confirm = "I couldn't reach that agent — check the backend is running."
                elif not confirm:
                    label = _AGENT_LABELS.get(agent_id, agent_id)
                    eta   = _AGENT_ETA.get(agent_id, "a few minutes")
                    confirm = f"Running your {label} now. Should be ready in {eta}."
                _emit("thinking", query=text, agent=agent_id)
                _state = VS.SPEAKING
                _emit("speaking", response=confirm, agent=agent_id)
                # Speak sentence by sentence so UI builds up progressively
                for s in _split_sentences(confirm):
                    _emit("speaking_partial", sentence=s)
                    _speak_sentence(s)
                history.append({"role": "user", "content": text})
                history.append({"role": "assistant", "content": confirm})
                if len(history) > _HISTORY_MAX: history = history[-_HISTORY_MAX:]
                _save_history(history)
                _post_response_cooldown(oww)
                _state = VS.LISTENING
                _emit("listening", message="Say 'Alexa' to activate")
                continue

            # ── Conversational query: KB grounding + streaming Claude → TTS ───
            kb_ctx = ""
            if _kb and _kb.has_content():
                chunks = _kb.search(text, top_k=3)
                kb_ctx = _kb.format_context(chunks, max_chars=1200)

            _state = VS.THINKING
            _emit("thinking", query=text)
        except Exception as e:
            print(f"[voice] Request handling error (retrying): {e}")
            _state = VS.LISTENING
            _emit("listening", message="Say 'Alexa' to activate")
            continue

        # Streaming: Claude text streams → sentence TTS plays progressively
        # First audio arrives in ~1.2s instead of 4-6s (CAPA-Voice-001)
        t0 = time.time()
        _state = VS.SPEAKING
        _emit("speaking", response="…")   # UI shows speaking immediately
        response = _ask_claude_streaming(text, history, kb_ctx=kb_ctx)
        latency_ms = (time.time() - t0) * 1000
        _track_query(latency_ms, stt_logprob=avg_logprob,
                     wake_score=wake_score, transcript=text, stt_ms=stt_ms)

        history.append({"role": "user",      "content": text})
        history.append({"role": "assistant", "content": response})
        if len(history) > _HISTORY_MAX: history = history[-_HISTORY_MAX:]
        _save_history(history)
        _emit("speaking", response=response)   # update UI with full text
        _play_chime(False)
        _post_response_cooldown(oww)

        _state = VS.LISTENING
        _emit("listening", message="Say 'Alexa' to activate")

    _state = VS.STOPPED
    _emit("level", level=0.0)
    _emit("stopped", reason="Voice assistant stopped")
    _stop_kokoro_server()
    if _has_memory and _mem:
        _mem.log_event("voice_bridge", "shutdown",
                       metadata={"session_turns": len(history) // 2})

# ── API router ────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/voice", tags=["voice"])
_voice_thread = None

# Pre-load models as soon as this module is imported (server startup)
_preload_models()


@router.post("/start")
async def start_voice():
    global _active, _voice_thread, _loop
    if _active:
        return {"status": "already_running", "state": _state}
    _loop   = asyncio.get_event_loop()
    _active = True
    _voice_thread = threading.Thread(target=_voice_loop, daemon=True, name="athena-voice")
    _voice_thread.start()
    return {"status": "started", "tts_backend": TTS_BACKEND,
            "device": DEVICE_NAME, "device_rate": DEVICE_RATE,
            "voice": KOKORO_VOICE}


@router.post("/stop")
async def stop_voice():
    global _active
    _active = False
    return {"status": "stopping"}


@router.get("/status")
async def voice_status():
    return {"active": _active, "state": _state, "tts_backend": TTS_BACKEND,
            "wake_phrase": WAKE_PHRASE, "device": DEVICE_NAME,
            "device_rate": DEVICE_RATE, "voice": KOKORO_VOICE,
            "models_ready": _models_ready.is_set()}


@router.post("/notify")
async def voice_notify(request: Request):
    """Queue a short spoken notification for Athena to deliver between listening turns."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    text = str(body.get("text", "")).strip()
    if text and _active:
        _notification_queue.append(text)
        return {"ok": True}
    return {"ok": False, "reason": "voice not active" if not _active else "empty text"}


@router.get("/devices")
async def list_devices():
    devs = [{"index": i, "name": d["name"], "rate": int(d["default_samplerate"])}
            for i, d in enumerate(sd.query_devices())
            if d["max_input_channels"] > 0]
    return {"devices": devs}


async def voice_websocket_endpoint(ws: WebSocket):
    await voice_manager.connect(ws)
    # Send current state immediately so clients that connect after voice started
    # don't miss the transition (e.g. "listening" emitted before WS was open).
    try:
        await ws.send_json({"type": f"voice_{_state}", "ts": datetime.now().isoformat(),
                            "models_ready": _models_ready.is_set()})
    except Exception:
        pass
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect:
        voice_manager.disconnect(ws)
