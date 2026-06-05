"""
Latitude MedTech Voice Assistant — Athena (v3 — Memory Enhanced)
=================================================================
Wake word  : "Alexa" (placeholder until Hi Athena model trained)
STT        : faster-whisper (local)
LLM        : Claude API
TTS        : Piper (if installed) -> pyttsx3 fallback
Memory     : Shared SQLite context — knows what agents have done
"""

import os, sys, time, tempfile, subprocess
import numpy as np
import sounddevice as sd
import soundfile as sf
from pathlib import Path
from dotenv import load_dotenv

_ATHENA = Path(__file__).resolve().parent.parent   # voice/ -> Athena/
load_dotenv(_ATHENA / 'voice' / '.env')

# ── Shared memory ─────────────────────────────────────────────────────────────
sys.path.insert(0, str(_ATHENA / 'agents'))
try:
    from memory import Memory
    _mem        = Memory()
    _has_memory = True
except Exception:
    _has_memory = False
    _mem        = None

# ── Config ────────────────────────────────────────────────────────────────────
WAKE_WORD_MODEL   = "alexa"
INFERENCE_FW      = "onnx"
WHISPER_MODEL     = "base.en"
SAMPLE_RATE       = 16000
CHUNK_DURATION    = 0.08
CHUNK_SAMPLES     = int(SAMPLE_RATE * CHUNK_DURATION)
SILENCE_THRESHOLD = 0.005
SILENCE_DURATION  = 2.5
MAX_RECORD_SEC    = 30
WAKE_THRESHOLD    = 0.5
PIPER_EXE         = Path("piper/piper.exe")
PIPER_MODEL       = Path("piper/en_US-lessac-medium.onnx")
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

def build_system_prompt():
    base = """You are Athena, the voice assistant for Latitude MedTech LLC.
You assist the founder — a QA/RA professional and MedTech coach in San Diego.

You help with:
- Career coaching for early-career QA/RA professionals
- Medical device regulatory knowledge (FDA, EU MDR, ISO 13485, MDSAP) for planning/educational purposes
- MedTech Meridian Substack strategy
- Business development and strategic planning

VOICE RULES:
- Natural spoken English only. No markdown, bullets, or symbols.
- Under 80 words unless asked for detail.
- Complete sentences. No filler phrases.
- DISCLAIMER: Regulatory content is educational only. Not licensed regulatory advice."""

    if _has_memory and _mem:
        ctx = _mem.context_summary()
        if ctx:
            base += f"\n\nCurrent system context:\n{ctx}"

    return base

# ── Terminal colors ───────────────────────────────────────────────────────────
class C:
    RESET="\033[0m"; BOLD="\033[1m"; BLUE="\033[94m"
    TEAL="\033[96m"; AMBER="\033[93m"; GREEN="\033[92m"
    RED="\033[91m";  GRAY="\033[90m";  WHITE="\033[97m"

def log(msg, color=C.GRAY): print(f"{color}{msg}{C.RESET}")

def banner():
    print(f"""
{C.BLUE}{C.BOLD}  ATHENA -- Latitude MedTech Voice Assistant v3{C.RESET}
{C.GRAY}  Memory: {'enabled' if _has_memory else 'disabled'} | Say "Alexa" to activate | Ctrl+C to exit{C.RESET}
""")

# ── Audio ─────────────────────────────────────────────────────────────────────
def play_chime(freq=880, freq2=1100, dur=0.12, vol=0.4):
    try:
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        sd.play(np.concatenate([np.sin(2*np.pi*freq*t), np.sin(2*np.pi*freq2*t)]).astype(np.float32)*vol, SAMPLE_RATE)
        sd.wait()
    except Exception: pass

def play_done_chime(freq=660, dur=0.10, vol=0.3):
    try:
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        sd.play((np.sin(2*np.pi*freq*t)*vol).astype(np.float32), SAMPLE_RATE)
        sd.wait()
    except Exception: pass

def rms(chunk): return float(np.sqrt(np.mean(chunk.astype(np.float32)**2)))

# ── Wake word ─────────────────────────────────────────────────────────────────
def load_wake_word():
    try:
        from openwakeword.model import Model
        log("Loading wake word model...", C.GRAY)
        model = Model(wakeword_models=[WAKE_WORD_MODEL], inference_framework=INFERENCE_FW)
        log(f"Wake word ready: '{WAKE_WORD_MODEL.title()}'", C.GREEN)
        return model
    except Exception as e:
        log(f"ERROR loading wake word: {e}", C.RED); sys.exit(1)

def listen_for_wake_word(oww_model):
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=1280) as stream:
        while True:
            chunk, _ = stream.read(1280)
            pred = oww_model.predict(chunk.flatten())
            for _, score in pred.items():
                if score >= WAKE_THRESHOLD: return True

# ── STT ───────────────────────────────────────────────────────────────────────
def load_whisper():
    try:
        from faster_whisper import WhisperModel
        log(f"Loading Whisper ({WHISPER_MODEL})...", C.GRAY)
        model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        log("Whisper ready.", C.GREEN)
        return model
    except Exception as e:
        log(f"ERROR: {e}", C.RED); sys.exit(1)

def record_until_silence():
    log("  Recording...", C.AMBER)
    frames, silence_frames = [], 0
    max_f = int(MAX_RECORD_SEC / CHUNK_DURATION)
    sil_c = int(SILENCE_DURATION / CHUNK_DURATION)
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=CHUNK_SAMPLES) as stream:
        while len(frames) < max_f:
            chunk, _ = stream.read(CHUNK_SAMPLES)
            flat = chunk.flatten(); frames.append(flat)
            silence_frames = silence_frames+1 if rms(flat) < SILENCE_THRESHOLD*32768 else 0
            if silence_frames >= sil_c: break
    audio = np.concatenate(frames)
    log(f"  Recorded {len(audio)/SAMPLE_RATE:.1f}s.", C.GRAY)
    return audio

def transcribe(whisper_model, audio):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f: tmp = f.name
    try:
        sf.write(tmp, audio.astype(np.float32)/32768.0, SAMPLE_RATE)
        segs, _ = whisper_model.transcribe(tmp, language="en", beam_size=3, vad_filter=True)
        return " ".join(s.text.strip() for s in segs).strip()
    finally:
        try: os.unlink(tmp)
        except: pass

# ── Claude ────────────────────────────────────────────────────────────────────
def ask_claude(user_text, history):
    if not ANTHROPIC_API_KEY:
        return "API key not found. Please set ANTHROPIC_API_KEY in your dot env file."
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msgs   = [*[{"role": m["role"], "content": m["content"]} for m in history],
                  {"role": "user", "content": user_text}]
        resp   = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=200,
            system=build_system_prompt(),
            messages=msgs,
        )
        answer = resp.content[0].text.strip()

        # Log to shared memory
        if _has_memory and _mem:
            _mem.log('voice_assistant', 'query', {
                'query':    user_text[:200],
                'response': answer[:200],
            })

        return answer
    except Exception as e:
        return f"I encountered an error: {e}"

# ── TTS ───────────────────────────────────────────────────────────────────────
def speak(text):
    if PIPER_EXE.exists() and PIPER_MODEL.exists():
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f: out = f.name
            proc = subprocess.run([str(PIPER_EXE), "--model", str(PIPER_MODEL), "--output_file", out],
                input=text.encode("utf-8"), capture_output=True, timeout=15)
            if proc.returncode == 0 and Path(out).exists():
                data, sr = sf.read(out)
                sd.play(data.astype(np.float32), sr); sd.wait(); return
        except Exception: pass
        finally:
            try: os.unlink(out)
            except: pass
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 175)
        engine.say(text); engine.runAndWait()
    except Exception as e:
        log(f"  TTS unavailable: {e}", C.RED)
        log(f"  Response: {text}", C.WHITE)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    banner()
    if not ANTHROPIC_API_KEY:
        log("WARNING: ANTHROPIC_API_KEY not set.\n", C.AMBER)

    oww     = load_wake_word()
    whisper = load_whisper()
    history = []

    log(f"\n{C.TEAL}Ready. Listening for wake word...{C.RESET}\n")

    try:
        while True:
            listen_for_wake_word(oww)
            log(f"\n{C.TEAL}*  Athena activated!{C.RESET}")
            play_chime()

            audio = record_until_silence()
            log("  Transcribing...", C.GRAY)
            text  = transcribe(whisper, audio)

            if not text:
                log("  (No speech detected -- try again)", C.GRAY)
                log(f"\n{C.TEAL}Listening...{C.RESET}")
                continue

            log(f"\n{C.WHITE}You:{C.RESET} {text}")
            log(f"{C.BLUE}Thinking...{C.RESET}")

            response = ask_claude(text, history)
            history += [{"role": "user", "content": text}, {"role": "assistant", "content": response}]
            if len(history) > 20: history = history[-20:]

            log(f"{C.TEAL}Athena:{C.RESET} {response}\n")
            speak(response)
            play_done_chime()
            log(f"{C.GRAY}Listening for wake word...{C.RESET}")

    except KeyboardInterrupt:
        log("\nShutting down Athena. Goodbye.", C.BLUE)
        if _has_memory and _mem:
            _mem.log('voice_assistant', 'shutdown', {'session_turns': len(history)//2})
        sys.exit(0)

if __name__ == "__main__":
    main()
