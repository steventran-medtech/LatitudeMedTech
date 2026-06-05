# Miso One TTS — Setup Guide

Miso One (MisoTTS 8B) dropped June 3 2026. Open weights, self-hosted.
110ms latency. Swap in place of Piper once model is downloaded.

## Step 1 — Clone the model

```powershell
cd C:\Users\huann\LatitudeMedTech\Athena\voice
git clone https://github.com/MisoLabsAI/MisoTTS miso
```

## Step 2 — Install dependencies into the existing venv

```powershell
cd C:\Users\huann\LatitudeMedTech\Athena\voice
venv\Scripts\activate
pip install -r miso\requirements.txt
```

## Step 3 — Download model weights

Follow the instructions in miso\README.md. Weights are hosted on
Hugging Face at: https://huggingface.co/MisoLabs/MisoTTS

```powershell
pip install huggingface_hub
python -c "from huggingface_hub import snapshot_download; snapshot_download('MisoLabs/MisoTTS', local_dir='miso/weights')"
```

## Step 4 — Create the inference wrapper

The voice_bridge.py calls: python miso/run_tts.py --text "..." --output out.wav

Create miso\run_tts.py to match that interface using the MisoTTS API.
See miso\README.md for the inference API.

## Step 5 — Switch backend

In Athena\voice\.env, change:
  VOICE_TTS_BACKEND=piper
to:
  VOICE_TTS_BACKEND=miso

Restart Athena. No other code changes needed.

## Voice cloning (optional)

Miso supports one-shot voice cloning from a ~10 second WAV clip.
Record a clean sample of your voice and pass it as a reference.
Update _speak_miso() in voice_bridge.py to pass --reference your_voice.wav.

## Notes

- English only (as of June 2026)
- Half-duplex — handles one turn at a time (fine for Athena's use case)
- Managed API from Miso Labs is coming — update _speak_miso() when it ships
  to remove the subprocess call and use their SDK instead
