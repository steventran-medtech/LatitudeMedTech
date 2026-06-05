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

import numpy as np
import sounddevice as sd
import soundfile as sf
from math import gcd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from scipy.signal import resample_poly
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

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
                    "Spoken confirmation for Steven. One sentence, max 15 words. "
                    "British English. No markdown or lists. "
                    "Example: 'Starting your marketing brief now.' "
                    "or 'On it — generating outreach for Jon Speer.'"
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
        log.warning(f"Intent classification failed, falling through to conversation: {e}")
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

def _track_query(latency_ms: float, empty: bool = False):
    """Log per-query stats; adjust silence threshold if too many false starts."""
    global SILENCE_THRESHOLD
    _session_stats["queries"] += 1
    _session_stats["latencies_ms"].append(latency_ms)
    if empty:
        _session_stats["empty_transcripts"] += 1

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
                                 "silence_threshold": SILENCE_THRESHOLD})

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
    Pre-warm OWW + Whisper in a background thread at server startup.
    The voice loop blocks until this completes, so the first activation
    is immediate instead of waiting 10-20 s for model loading.
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
            _emit("loading", message="Loading Whisper transcription model (cached after first run)…")
            _whisper_model = _load_whisper()
            _emit("loading", message="Models ready.")
        except Exception as e:
            _emit("error", message=f"Model preload failed: {e}")
        finally:
            _models_ready.set()

    t = threading.Thread(target=_load, daemon=True, name="model-preloader")
    t.start()

def _listen_for_wake(oww_model):
    """
    Stream mic → resample → openwakeword. Returns True on detection.
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
                    i16 = (rs * 32768).clip(-32768, 32767).astype(np.int16)
                    pred = oww_model.predict(i16)
                    for _, score in pred.items():
                        if score >= WAKE_THRESHOLD:
                            return True
        except Exception as e:
            # Audio device hiccup — wait briefly and retry instead of crashing
            _emit("level", level=0.0)
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 1.5, 3.0)  # back off up to 3s
    return False

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
            silence = silence + 1 if _rms(mono) < SILENCE_THRESHOLD else 0
            if silence >= sil_chunks: break
    _emit("level", level=0.0)
    return np.concatenate(frames) if frames else np.array([], dtype=np.float32)

_LOW_CONFIDENCE_THRESHOLD = -0.7   # avg_logprob below this = uncertain transcript

def _transcribe(whisper_model, audio):
    """
    Transcribe audio. Returns (text, confident: bool).
    avg_logprob per segment: 0 = perfect, -1 = poor. Threshold -0.7.
    """
    if audio.size == 0:
        return "", True
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp = f.name
    try:
        sf.write(tmp, audio, TARGET_RATE)
        segs_iter, _ = whisper_model.transcribe(
            tmp, language="en", beam_size=5, vad_filter=True)
        segs = list(segs_iter)
        text = " ".join(s.text.strip() for s in segs).strip()
        # Confidence: average log-prob across segments (higher = better)
        if segs:
            avg_lp = sum(s.avg_logprob for s in segs) / len(segs)
            confident = avg_lp >= _LOW_CONFIDENCE_THRESHOLD
        else:
            confident = True
        return text, confident
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
            max_tokens=80,
            system=(
                "You are a speech-to-text correction assistant for a MedTech executive. "
                "Fix transcription errors — wrong homophones, missing words, garbled STT — "
                "while preserving meaning. MedTech terms: FDA, ISO 13485, MDR, QMS, CAPA, "
                "510(k), PMA, MDSAP, RAPS, RA/QA. "
                "Return ONLY the corrected text with no explanation."
            ),
            messages=[{"role": "user", "content": f"Correct: {raw}"}],
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
        "- Spoken British English. No markdown, lists, or symbols.\n"
        "- Maximum 2 sentences. Never more unless explicitly asked.\n"
        "- Answer first. Cut all preamble, filler, and restating the question.\n"
        "- Agent confirmations: one sentence only.\n"
        "DISCLAIMER: Regulatory content is educational. Not licensed advice."
    )

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

def _speak_kokoro(text: str):
    """Send text to persistent Kokoro server, play returned WAV."""
    payload = json.dumps({"text": text, "voice": KOKORO_VOICE}).encode()
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
    text = text.strip()
    if not text:
        return
    try:
        if TTS_BACKEND == "piper":
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
    # Brief pause after TTS — lets Windows audio device fully release
    # before we re-open the input stream for wake word detection
    time.sleep(0.25)

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
        if TTS_BACKEND == "piper":
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

# ── Main voice loop ───────────────────────────────────────────────────────────

def _voice_loop():
    global _state

    # Skip loading state entirely if models are already warm from startup preload
    already_ready = _models_ready.is_set()

    if not already_ready:
        _state = VS.LOADING
        _emit("loading", message=f"Mic: {DEVICE_NAME} @ {DEVICE_RATE} Hz")

    # Ensure Kokoro is running (fast no-op health check if already up)
    if TTS_BACKEND == "kokoro":
        if not already_ready:
            _emit("loading", message="Starting Kokoro TTS server…")
        kokoro_thread = threading.Thread(target=_start_kokoro_server, daemon=True)
        kokoro_thread.start()

    # Wait for pre-loaded models only if not yet ready
    if not already_ready:
        _emit("loading", message="Waiting for models to finish loading…")
        _models_ready.wait(timeout=60)

    oww     = _oww_model
    whisper = _whisper_model
    history = []

    if oww is None:
        _state = VS.STOPPED
        _emit("stopped", reason="Wake word model failed"); return

    _state = VS.LISTENING
    _emit("listening", message="Say 'Alexa' to activate")

    while _active:
        if not _listen_for_wake(oww) or not _active:
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

        text, confident = _transcribe(whisper, audio)
        empty = not bool(text)
        _track_query(0, empty=empty)

        if not text:
            _state = VS.LISTENING
            _emit("listening", message="No speech detected — listening again")
            continue

        # Confidence check: silently correct via LLM if Whisper was uncertain.
        # This fixes homophone swaps and garbled words without blocking the
        # response or asking the user to repeat. Falls back to raw text if
        # the correction call fails.
        if not confident:
            corrected = _correct_transcript(text)
            if corrected != text:
                _emit("transcript", text=f"{corrected}  [corrected]")
            else:
                _emit("transcript", text=f"{text}  [low conf]")
            text = corrected
        else:
            _emit("transcript", text=text)

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
                confirm = f"On it — starting the {label} now."
            _emit("thinking", query=text, agent=agent_id)
            _state = VS.SPEAKING
            _emit("speaking", response=confirm, agent=agent_id)
            _speak_sentence(confirm)
            history.append({"role": "user", "content": text})
            history.append({"role": "assistant", "content": confirm})
            if len(history) > 20: history = history[-20:]
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

        # Streaming: Claude text streams → sentence TTS plays progressively
        # First audio arrives in ~1.2s instead of 4-6s (CAPA-Voice-001)
        t0 = time.time()
        _state = VS.SPEAKING
        _emit("speaking", response="…")   # UI shows speaking immediately
        response = _ask_claude_streaming(text, history, kb_ctx=kb_ctx)
        latency_ms = (time.time() - t0) * 1000
        _track_query(latency_ms)

        history.append({"role": "user",      "content": text})
        history.append({"role": "assistant", "content": response})
        if len(history) > 20: history = history[-20:]
        _emit("speaking", response=response)   # update UI with full text
        _play_chime(False)

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
            "device_rate": DEVICE_RATE, "voice": KOKORO_VOICE}


@router.get("/devices")
async def list_devices():
    devs = [{"index": i, "name": d["name"], "rate": int(d["default_samplerate"])}
            for i, d in enumerate(sd.query_devices())
            if d["max_input_channels"] > 0]
    return {"devices": devs}


async def voice_websocket_endpoint(ws: WebSocket):
    await voice_manager.connect(ws)
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect:
        voice_manager.disconnect(ws)
