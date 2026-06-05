"""
Kokoro TTS inference script.
Called as a subprocess by voice_bridge.py.

Usage:
  python run_kokoro.py --text "Hello" --output out.wav [--voice af_heart]

Voices (American English):
  af_heart  — warm, professional female (default)
  af_bella  — clear, neutral female
  am_adam   — deep male
  am_echo   — lighter male
"""

import argparse
import os
import sys

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

parser = argparse.ArgumentParser()
parser.add_argument("--text",   required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--voice",  default="af_heart")
args = parser.parse_args()

try:
    import soundfile as sf
    from kokoro import KPipeline

    pipeline = KPipeline(lang_code="a")  # American English
    audio_out = None

    for _, _, audio in pipeline(args.text, voice=args.voice):
        if audio_out is None:
            audio_out = audio
        else:
            import numpy as np
            audio_out = np.concatenate([audio_out, audio])

    if audio_out is None or len(audio_out) == 0:
        print("ERROR: no audio generated", file=sys.stderr)
        sys.exit(1)

    sf.write(args.output, audio_out, 24000)
    print(f"OK {len(audio_out)} samples")

except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
