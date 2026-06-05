# Latitude MedTech Voice Assistant — Windows Setup

Say **"Hey Jarvis"** → assistant activates → speak your query → Claude responds aloud.

---

## Prerequisites

- Windows 10 or 11
- Python 3.10 or 3.11 (recommended — faster-whisper works best here)
- A working microphone
- Anthropic API key

---

## Step 1 — Clone / download this folder

Place the `voice/` folder somewhere permanent, e.g.:

```
C:\Users\YourName\LatitudeMedTech\voice\
```

---

## Step 2 — Create a virtual environment

Open Command Prompt or PowerShell in the `voice/` folder:

```bat
python -m venv venv
venv\Scripts\activate
```

---

## Step 3 — Install Python dependencies

```bat
pip install -r requirements.txt
```

If you hit a PyAudio error on Windows:

```bat
pip install pipwin
pipwin install pyaudio
```

---

## Step 4 — Download openwakeword models

Run once after install:

```bat
python -c "import openwakeword; openwakeword.utils.download_models()"
```

This downloads the "hey_jarvis" and other built-in wake word models locally.

---

## Step 5 — Install Piper TTS (voice output)

1. Go to: https://github.com/rhasspy/piper/releases
2. Download: `piper_windows_amd64.zip`
3. Extract into a folder called `piper/` inside your `voice/` directory:

```
voice/
  piper/
    piper.exe
    ...
```

4. Download a voice model:
   - Go to: https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/lessac/medium
   - Download both files:
     - `en_US-lessac-medium.onnx`
     - `en_US-lessac-medium.onnx.json`
   - Place both in `voice/piper/`

Final structure:
```
voice/
  piper/
    piper.exe
    en_US-lessac-medium.onnx
    en_US-lessac-medium.onnx.json
```

---

## Step 6 — Set your API key

Create a file called `.env` in the `voice/` folder:

```
ANTHROPIC_API_KEY=your_api_key_here
```

Never commit this file to Git. It is already in .gitignore.

---

## Step 7 — Run

```bat
venv\Scripts\activate
python assistant.py
```

You should see the Latitude MedTech banner and "Listening for wake word..."

Say **"Hey Jarvis"** — you'll hear a two-tone chime. Then speak your query. Claude responds aloud.

---

## Changing the wake word

Open `assistant.py` and change:

```python
WAKE_WORD_MODEL = "hey_jarvis"
```

Built-in options: `"hey_jarvis"`, `"alexa"`, `"hey_mycroft"`, `"hey_rhasspy"`

For a custom wake word ("Hey Latitude", "Hey Claude", etc.) — see:
https://github.com/dscripka/openWakeWord#custom-models

---

## Tuning for your microphone

If the assistant cuts off too early or records too long, adjust in `assistant.py`:

```python
SILENCE_THRESHOLD = 0.012   # increase if it cuts off mid-sentence
SILENCE_DURATION  = 1.8     # increase for longer pauses between words
```

---

## Whisper model size tradeoffs

| Model     | Speed  | Accuracy | RAM    |
|-----------|--------|----------|--------|
| tiny.en   | Fast   | Good     | ~400MB |
| base.en   | Fast   | Better   | ~600MB | ← default
| small.en  | Medium | Best     | ~1.2GB |
| medium.en | Slow   | Excellent| ~2.5GB |

Change in `assistant.py`:
```python
WHISPER_MODEL = "base.en"
```

---

## Run on startup (optional)

To have the assistant start automatically with Windows:

1. Create a file `start_assistant.bat`:
```bat
@echo off
cd C:\Users\YourName\LatitudeMedTech\voice
call venv\Scripts\activate
python assistant.py
```

2. Press `Win + R` → type `shell:startup` → press Enter
3. Place a shortcut to `start_assistant.bat` in that folder

---

## Troubleshooting

**"No module named openwakeword"**
→ Make sure your venv is activated: `venv\Scripts\activate`

**PyAudio install fails**
→ `pip install pipwin && pipwin install pyaudio`

**Wake word not detecting**
→ Lower `WAKE_THRESHOLD` in assistant.py (try 0.3)
→ Make sure you downloaded models: `python -c "import openwakeword; openwakeword.utils.download_models()"`

**Whisper download hangs**
→ First run downloads the model (~150MB for base.en). Wait for it.

**Piper produces no sound**
→ Check `piper/piper.exe` and `piper/en_US-lessac-medium.onnx` both exist
→ Run piper manually to test: `echo "hello" | piper\piper.exe --model piper\en_US-lessac-medium.onnx --output_file test.wav`

**"ANTHROPIC_API_KEY not set"**
→ Create `.env` file in the voice/ folder with your key

---

## Architecture (for reference)

```
Microphone
    ↓
openwakeword  ←── always listening, local, ~0% CPU at idle
    ↓ wake word detected
Play chime
    ↓
sounddevice   ←── records until silence
    ↓
faster-whisper ←── local STT, no API, MedTech terminology aware
    ↓
Claude API    ←── only external call in the pipeline
    ↓
Piper TTS     ←── local neural voice, no API
    ↓
Speaker
```

Total latency from end of speech to first word of response: ~2–4 seconds on a modern laptop.

---

Latitude MedTech LLC · San Diego, CA · latitudemedtech.com
