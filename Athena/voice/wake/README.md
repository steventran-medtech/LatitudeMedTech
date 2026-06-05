# Custom Wake Word — "Hi Athena"

**Status:** Awaiting Steven's one-time Colab training run. Until then, the live
system falls back to the **"alexa"** wake word (per CLAUDE.md Voice Architecture).

## How the live system uses this folder

`voice/voice_bridge.py` → `_load_wake_model()` checks this exact path on startup:

```
Athena/voice/wake/hi_athena.onnx
```

- If the file exists → it is loaded as the wake word ("Hi Athena").
- If it does not exist → it falls back to the built-in **"alexa"** model.

**No code change is needed to deploy.** Drop the trained `hi_athena.onnx` into
this folder and restart Athena. The loader auto-detects it.

## Why this can't be finished autonomously

Training a wake word needs synthetic-audio generation + GPU training and a
HuggingFace token (`HF_TOKEN`). That is an external, manual step — handed off
to Steven. Two supported paths:

### Path A — Google Colab (recommended, free GPU, ~20–40 min)
1. Open the openWakeWord training notebook:
   https://colab.research.google.com/github/dscripka/openWakeWord/blob/main/notebooks/automatic_model_training.ipynb
2. Target phrase: **`Hi Athena`** (also add `Hey Athena` as a variant).
3. Run all cells; download the resulting `.onnx`.
4. Rename it to **`hi_athena.onnx`** and place it in **this folder**.
5. Restart Athena and say "Hi Athena".

### Path B — Local trainer (needs `HF_TOKEN` + heavy deps)
```powershell
cd Athena\agents
..\voice\venv\Scripts\python.exe train_wake_word.py          # train
..\voice\venv\Scripts\python.exe train_wake_word.py --test   # mic test
```
The trainer now writes directly to `voice/wake/hi_athena.onnx` (this folder),
so no further wiring is required.

## Verify after deploying
```powershell
cd Athena\agents
..\voice\venv\Scripts\python.exe train_wake_word.py --test
```
Say "Hi Athena" — a detection line should print. Then launch Athena normally.
