"""
Hi Athena — Custom Wake Word Trainer
======================================
Trains a custom "Hi Athena" wake word model using
openwakeword's synthetic training pipeline.

Uses your HuggingFace token to download the required
text-to-speech models for synthetic data generation.

No real recordings needed. openwakeword generates thousands
of synthetic audio samples of "Hi Athena" and trains a model.

Usage:
    python train_wake_word.py          (full training pipeline)
    python train_wake_word.py --test   (test existing model)

Output:
    Athena/voice/wake/hi_athena.onnx   (the path voice_bridge.py auto-loads)

Deploy: the trained model is written straight to voice/wake/. The live system
(voice_bridge.py _load_wake_model) auto-detects it on startup — no code edit
needed. If absent, it falls back to the built-in "alexa" wake word.

.env variables:
    HF_TOKEN=your_huggingface_token
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from dotenv import load_dotenv

# Derive the Athena code root from this file's location (agents/ -> Athena/),
# matching how voice_bridge.py resolves ATHENA. Avoids the Path.home()/Athena
# data-tree, which is NOT where voice_bridge reads the wake model from.
ATHENA_ROOT = Path(__file__).resolve().parents[1]   # ...\LatitudeMedTech\Athena
load_dotenv(ATHENA_ROOT / 'voice' / '.env')

# Write to the path the live voice system actually reads (voice_bridge.py:404).
MODELS_DIR = ATHENA_ROOT / 'voice' / 'wake'
LOG_DIR    = ATHENA_ROOT / 'logs'
MODELS_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'wake_word_trainer.log'),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger('wake_word_trainer')

HF_TOKEN   = os.getenv('HF_TOKEN', '')
WAKE_PHRASE = "Hi Athena"
MODEL_OUT   = MODELS_DIR / 'hi_athena.onnx'


# ── Dependency check ──────────────────────────────────────────────────────────

def check_deps():
    """Check and install required packages for training."""
    required = [
        'openwakeword',
        'torchaudio',
        'datasets',
        'huggingface_hub',
    ]
    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_').split('[')[0])
        except ImportError:
            missing.append(pkg)

    if missing:
        log.info(f"Installing missing packages: {missing}")
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install'] + missing + ['-q'],
            check=True
        )
    log.info("Dependencies OK")


# ── HuggingFace auth ──────────────────────────────────────────────────────────

def setup_hf_auth():
    if not HF_TOKEN:
        log.error("HF_TOKEN not set in .env file.")
        log.error("Get your token at: https://huggingface.co/settings/tokens")
        log.error("Add to .env: HF_TOKEN=hf_your_token_here")
        return False
    try:
        from huggingface_hub import login
        login(token=HF_TOKEN, add_to_git_credential=False)
        log.info("HuggingFace authentication OK")
        return True
    except Exception as e:
        log.error(f"HF auth failed: {e}")
        return False


# ── Synthetic training data generation ───────────────────────────────────────

def generate_training_data():
    """
    Uses openwakeword's built-in synthetic data generation.
    Generates audio clips of "Hi Athena" + negative examples.
    """
    log.info("Generating synthetic training data for 'Hi Athena'...")
    log.info("This uses TTS to create thousands of audio variations.")
    log.info("Expected time: 15-30 minutes on first run.")

    try:
        # openwakeword provides a training script
        # We invoke it with our target phrase
        from openwakeword.train import train

        training_config = {
            "target_phrase":    [WAKE_PHRASE, "Hey Athena", "Hi Athena"],
            "output_dir":       str(MODELS_DIR / 'training_data'),
            "n_samples":        5000,       # synthetic samples per phrase
            "negative_weight":  0.5,
            "model_type":       "lightweight",
        }

        # Save config
        config_path = MODELS_DIR / 'training_config.json'
        config_path.write_text(json.dumps(training_config, indent=2))

        log.info(f"Training config saved: {config_path}")
        log.info("Starting synthetic data generation...")

        train(
            target_phrases=training_config["target_phrase"],
            output_dir=training_config["output_dir"],
            n_samples=training_config["n_samples"],
        )
        log.info("Synthetic data generation complete.")
        return True

    except ImportError:
        log.warning("openwakeword.train not available in this version.")
        log.info("Using manual training approach...")
        return manual_training_approach()
    except Exception as e:
        log.error(f"Training data generation failed: {e}")
        log.info("Falling back to manual approach...")
        return manual_training_approach()


def manual_training_approach():
    """
    Fallback: provides instructions for manual training via
    openwakeword's GitHub training notebooks.
    """
    instructions = f"""
+----------------------------------------------------------+
|  Hi Athena Custom Wake Word - Manual Training Guide      |
+----------------------------------------------------------+

The automated training pipeline requires additional setup.
Here is the manual approach (30 min, one-time setup):

STEP 1 - Use openwakeword's Colab notebook:
  https://colab.research.google.com/github/dscripka/openWakeWord/blob/main/notebooks/automatic_model_training.ipynb

  Open the notebook in Google Colab (free GPU).
  Enter "Hi Athena" as your target phrase.
  Download the output .onnx file when complete.

STEP 2 - Deploy the model (no code edit needed):
  Rename it to hi_athena.onnx and drop it here:
  {MODEL_OUT}

  voice_bridge.py auto-detects this file on startup. If absent, the system
  falls back to the built-in "alexa" wake word.

STEP 3 - Test:
  python train_wake_word.py --test
  Say "Hi Athena" to activate, then launch Athena normally.

Estimated training time in Colab: 20-40 minutes.
No cost. No GPU required on your machine.

+----------------------------------------------------------+
"""
    print(instructions)

    # Save the guide alongside the model location
    readme_path = MODELS_DIR / 'HI_ATHENA_TRAINING_GUIDE.txt'
    readme_path.write_text(instructions)
    log.info(f"Training guide saved: {readme_path}")
    return False


# ── Model testing ─────────────────────────────────────────────────────────────

def test_model(model_path: Path):
    """Test an existing Hi Athena model with microphone input."""
    if not model_path.exists():
        log.error(f"Model not found: {model_path}")
        log.error("Run training first or follow the manual guide.")
        return

    log.info(f"Testing model: {model_path}")
    log.info("Say 'Hi Athena' to test. Ctrl+C to stop.")

    try:
        import numpy as np
        import sounddevice as sd
        from openwakeword.model import Model

        model = Model(wakeword_models=[str(model_path)], inference_framework='onnx')
        detections = 0

        with sd.InputStream(samplerate=16000, channels=1, dtype='int16', blocksize=1280) as stream:
            while True:
                chunk, _ = stream.read(1280)
                pred = model.predict(chunk.flatten())
                for name, score in pred.items():
                    if score > 0.5:
                        detections += 1
                        print(f"  DETECTED: {name} (score: {score:.3f}) - detection #{detections}")

    except KeyboardInterrupt:
        print(f"\nTest complete. Total detections: {detections}")


# ── Update assistant.py ───────────────────────────────────────────────────────

def update_assistant(model_path: Path):
    """Update assistant.py to use the new Hi Athena model."""
    assistant_path = ATHENA_ROOT / 'voice' / 'assistant.py'
    if not assistant_path.exists():
        log.warning(f"assistant.py not found at {assistant_path}")
        return

    content = assistant_path.read_text(encoding='utf-8')

    # Replace wake word model line
    import re
    content = re.sub(
        r'WAKE_WORD_MODEL\s*=\s*["\'].*["\']',
        f'WAKE_WORD_MODEL   = r"{model_path}"',
        content
    )
    content = re.sub(
        r'INFERENCE_FW\s*=\s*["\'].*["\']',
        'INFERENCE_FW      = "onnx"',
        content
    )

    assistant_path.write_text(content, encoding='utf-8')
    log.info(f"Updated assistant.py to use Hi Athena model")
    log.info(f"Restart assistant.py to activate 'Hi Athena'")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test',   action='store_true', help='Test existing model')
    parser.add_argument('--update', action='store_true', help='Update assistant.py with trained model')
    args = parser.parse_args()

    print("""
+------------------------------------------+
|  Hi Athena Wake Word Trainer             |
|  Latitude MedTech Voice Assistant        |
+------------------------------------------+
""")

    if args.test:
        test_model(MODEL_OUT)
        return

    if args.update:
        if MODEL_OUT.exists():
            update_assistant(MODEL_OUT)
        else:
            log.error(f"No trained model found at {MODEL_OUT}")
            log.error("Train first or follow the manual guide.")
        return

    # Check if model already exists
    if MODEL_OUT.exists():
        print(f"Model already exists: {MODEL_OUT}")
        choice = input("Re-train? (y/n): ").strip().lower()
        if choice != 'y':
            print("\nSkipping training. To test: python train_wake_word.py --test")
            print("To update assistant: python train_wake_word.py --update")
            return

    # Check deps
    check_deps()

    # HF auth
    if not setup_hf_auth():
        log.error("Cannot proceed without HuggingFace authentication.")
        manual_training_approach()
        return

    # Train
    success = generate_training_data()

    if success and MODEL_OUT.exists():
        log.info(f"Model trained successfully: {MODEL_OUT}")
        print("\nDone. The model is in voice/wake/ — voice_bridge.py auto-detects it.")
        print("Restart Athena and say 'Hi Athena' to activate.")
    else:
        print("\nAutomated training not available in this environment.")
        print("Follow the manual guide above to train in Google Colab (free, 30 min).")


if __name__ == '__main__':
    main()
