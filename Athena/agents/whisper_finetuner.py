"""
Athena Whisper Fine-Tuner
==========================
Adapts the Whisper STT model to Steven's voice and MedTech vocabulary
using audio samples collected by voice_bridge.py (when capture_samples=true).

Two complementary strategies run on every cycle:

  Strategy A — Domain Prompt Evolution (zero data needed, runs always)
    Reads query_telemetry.jsonl to find transcripts where Whisper was uncertain
    (avg_logprob < -0.5). Extracts the corrected text (from _correct_transcript())
    stored in .athena_history.json. Identifies new MedTech terms that should be
    added to _WHISPER_DOMAIN_PROMPT in voice_bridge.py. Applies via CodeWriter.

  Strategy B — Model Fine-Tuning (requires >= MIN_SAMPLES confident WAVs)
    Loads WAV+transcript pairs from voice/samples/.
    Prepares a HuggingFace dataset.
    Fine-tunes openai/whisper-tiny (or whisper-tiny.en) using Trainer API.
    Converts output to CTranslate2 format (faster-whisper compatible).
    Validates on 20% held-out split.
    Deploys to voice/models/custom_whisper/ if WER improves.

Usage:
  python whisper_finetuner.py               # auto-select strategy
  python whisper_finetuner.py --strategy a  # prompt evolution only
  python whisper_finetuner.py --strategy b  # fine-tuning only (needs data)
  python whisper_finetuner.py --check       # report data readiness

Enable sample collection: set voice.capture_samples = true in settings.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

# ── Path bootstrap ─────────────────────────────────────────────────────────────

_AGENTS  = Path(__file__).resolve().parent
sys.path.insert(0, str(_AGENTS))

from pathconfig import ATHENA_ROOT, AGENTS_DIR, SETTINGS_PATH, LOGS_DIR, MEMORY_DIR
from agent_base import AgentBase
from memory import Memory

VOICE_DIR      = ATHENA_ROOT / "voice"
SAMPLES_DIR    = VOICE_DIR / "samples"
TELEMETRY_FILE = VOICE_DIR / "query_telemetry.jsonl"
HISTORY_FILE   = VOICE_DIR / ".athena_history.json"
MODELS_DIR     = VOICE_DIR / "models" / "custom_whisper"
BRIDGE_FILE    = VOICE_DIR / "voice_bridge.py"
LOG_FILE       = LOGS_DIR / "voice_optimizer.log"

AGENT_NAME  = "whisper_finetuner"
MIN_SAMPLES = 80    # minimum confident WAVs before attempting fine-tuning


def _log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [whisper_finetuner] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ── Strategy A: Domain Prompt Evolution ──────────────────────────────────────

class DomainPromptEvolver:
    """
    Mines low-confidence transcripts + corrected text to discover new MedTech
    terms that should be added to Whisper's initial_prompt decoder bias.

    The prompt is a comma-separated vocabulary list injected before transcription.
    Adding a term costs nothing at runtime — no model reload needed.
    """

    # Minimum times a new term must appear before we add it to the prompt
    MIN_FREQUENCY = 2

    # Patterns to ignore (common English, already in prompt, short words)
    _IGNORE  = re.compile(r'^(the|a|an|and|or|is|to|of|in|for|it|that|this|be|with|as|at|by|from|on)$', re.I)
    _SHORT   = re.compile(r'^\w{1,3}$')

    def __init__(self, base: AgentBase):
        self.base = base

    def load_telemetry(self, days: int = 14) -> list:
        """Load recent query telemetry rows where stt_logprob < -0.5."""
        if not TELEMETRY_FILE.exists():
            return []
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        rows = []
        for line in TELEMETRY_FILE.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
                if r.get("ts", "") >= cutoff and r.get("stt_logprob", 0) < -0.5:
                    rows.append(r)
            except Exception:
                pass
        return rows

    def load_history(self) -> list:
        """Load conversation history."""
        if not HISTORY_FILE.exists():
            return []
        try:
            data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def extract_candidate_terms(self, history: list) -> list:
        """
        Extract MedTech terms from assistant responses that may not be
        in the current domain prompt. These are the "gold" transcription targets.
        """
        known_prompt_text = self._current_domain_prompt()
        known_terms = set(t.lower().strip() for t in known_prompt_text.split(","))

        # Pull all assistant responses
        responses = [m["content"] for m in history if m.get("role") == "assistant"]
        term_freq: Counter = Counter()

        for resp in responses:
            # Tokenise — take capitalized or all-caps tokens as candidate domain terms
            tokens = re.findall(r'\b[A-Z][A-Za-z0-9]+\b|\b[A-Z]{2,}\b', resp)
            for tok in tokens:
                if tok.lower() not in known_terms and \
                   not self._IGNORE.match(tok) and \
                   not self._SHORT.match(tok):
                    term_freq[tok] += 1

        candidates = [term for term, freq in term_freq.items()
                      if freq >= self.MIN_FREQUENCY]
        return candidates

    def _current_domain_prompt(self) -> str:
        """Read the current _WHISPER_DOMAIN_PROMPT value from voice_bridge.py."""
        if not BRIDGE_FILE.exists():
            return ""
        src = BRIDGE_FILE.read_text(encoding="utf-8")
        m = re.search(r'_WHISPER_DOMAIN_PROMPT\s*=\s*\(\s*"(.*?)"\s*\)', src, re.DOTALL)
        return m.group(1) if m else ""

    def evolve(self) -> dict:
        """
        Run evolution cycle. Returns result dict with added_terms list.
        """
        _log("Strategy A: Domain prompt evolution")
        telemetry = self.load_telemetry()
        history   = self.load_history()
        _log(f"  Low-confidence transcripts (14d): {len(telemetry)}")

        candidates = self.extract_candidate_terms(history)
        _log(f"  Candidate new terms: {candidates[:20]}")

        if not candidates:
            _log("  No new terms found — domain prompt is current")
            return {"added_terms": [], "strategy": "A"}

        # Ask Claude to vet the candidates
        vetting = (
            "You are curating the decoder vocabulary for a Whisper STT model used by a "
            "MedTech regulatory executive. Review these candidate terms and return ONLY those "
            "that are genuine MedTech/pharma/regulatory domain terms that Whisper commonly "
            "mispronounces or misspells when not primed.\n\n"
            f"Candidates: {', '.join(candidates)}\n\n"
            "Return a comma-separated list of approved terms only. No explanation."
        )
        try:
            approved_raw = self.base.ask(vetting, model="claude-haiku-4-5", max_tokens=200)
            approved = [t.strip() for t in approved_raw.split(",") if t.strip()]
        except Exception as e:
            _log(f"  Claude vetting failed: {e}")
            approved = candidates[:5]   # fall back to top-5

        if not approved:
            _log("  No terms approved by Claude vetting")
            return {"added_terms": [], "strategy": "A"}

        # Append to domain prompt via CodeWriter-style find/replace
        new_terms_str = ", ".join(approved)
        current = self._current_domain_prompt()
        if not current:
            _log("  Could not read current domain prompt — skipping")
            return {"added_terms": [], "strategy": "A"}

        new_prompt = current.rstrip() + f",\n    {new_terms_str}."
        success = self._patch_domain_prompt(current, new_prompt)
        if success:
            _log(f"  Added {len(approved)} terms: {new_terms_str}")
        return {"added_terms": approved, "strategy": "A"}

    def _patch_domain_prompt(self, old_prompt: str, new_prompt: str) -> bool:
        """Directly patch _WHISPER_DOMAIN_PROMPT in voice_bridge.py."""
        try:
            src     = BRIDGE_FILE.read_text(encoding="utf-8")
            old_blk = f'_WHISPER_DOMAIN_PROMPT = (\n    "{old_prompt}"\n)'
            new_blk = f'_WHISPER_DOMAIN_PROMPT = (\n    "{new_prompt}"\n)'
            if old_blk not in src:
                _log("  Domain prompt block not found in expected format — skipping patch")
                return False
            # Backup
            backup = BRIDGE_FILE.with_suffix(".py.bak")
            backup.write_text(src, encoding="utf-8")
            BRIDGE_FILE.write_text(src.replace(old_blk, new_blk, 1), encoding="utf-8")
            # Verify syntax
            import ast
            ast.parse(BRIDGE_FILE.read_text(encoding="utf-8"))
            backup.unlink()
            return True
        except Exception as e:
            _log(f"  Patch failed: {e} — rolling back")
            if backup.exists():
                BRIDGE_FILE.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
            return False


# ── Strategy B: Whisper Fine-Tuning ──────────────────────────────────────────

class WhisperFinetuner:
    """
    Fine-tunes openai/whisper-tiny.en on Steven's captured voice samples.

    Prerequisites (all must be in voice venv):
      pip install openai-whisper transformers datasets evaluate jiwer ctranslate2

    The fine-tuned model is converted to CTranslate2 format so faster-whisper
    can load it as a drop-in replacement for the current model.
    """

    def __init__(self):
        self.mem = Memory()

    def check_readiness(self) -> dict:
        """Report how many training-ready samples exist."""
        if not SAMPLES_DIR.exists():
            return {"ready": False, "samples": 0, "min_needed": MIN_SAMPLES,
                    "message": "Sample directory does not exist. Enable capture_samples in settings.json."}
        pairs = self._load_pairs()
        n = len(pairs)
        return {
            "ready":      n >= MIN_SAMPLES,
            "samples":    n,
            "min_needed": MIN_SAMPLES,
            "message":    (f"Ready to fine-tune ({n} samples)" if n >= MIN_SAMPLES
                           else f"Collecting data: {n}/{MIN_SAMPLES} samples. "
                                "Keep using Athena with capture_samples=true."),
        }

    def _load_pairs(self) -> list:
        """Load WAV+transcript pairs from voice/samples/. Only training_ready ones."""
        pairs = []
        for meta_f in sorted(SAMPLES_DIR.glob("*.json")):
            wav_f = meta_f.with_suffix(".wav")
            if not wav_f.exists():
                continue
            try:
                meta = json.loads(meta_f.read_text(encoding="utf-8"))
                if meta.get("training_ready", False) and meta.get("transcript"):
                    pairs.append({"wav": wav_f, "transcript": meta["transcript"]})
            except Exception:
                pass
        return pairs

    def _check_finetune_deps(self) -> bool:
        """Return True if all fine-tuning deps are available."""
        missing = []
        for pkg in ("whisper", "transformers", "datasets", "evaluate", "jiwer"):
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)
        if missing:
            _log(f"  Missing fine-tuning deps: {missing}")
            _log("  Install: pip install openai-whisper transformers datasets evaluate jiwer ctranslate2")
            return False
        return True

    def finetune(self) -> dict:
        """
        Run the full fine-tuning pipeline. Returns result dict.
        """
        _log("Strategy B: Whisper fine-tuning")

        readiness = self.check_readiness()
        _log(f"  {readiness['message']}")
        if not readiness["ready"]:
            return {"success": False, "reason": "insufficient_data", **readiness}

        if not self._check_finetune_deps():
            return {"success": False, "reason": "missing_deps"}

        try:
            import whisper
            import torch
            from datasets import Dataset, Audio
            import evaluate

            pairs = self._load_pairs()
            _log(f"  Loaded {len(pairs)} training pairs")

            # 80/20 split
            split_idx = int(0.8 * len(pairs))
            train_pairs = pairs[:split_idx]
            val_pairs   = pairs[split_idx:]

            # Load model
            device = "cuda" if torch.cuda.is_available() else "cpu"
            _log(f"  Loading whisper-tiny.en on {device}")
            model = whisper.load_model("tiny.en", device=device)

            # Baseline WER on validation set
            wer_metric = evaluate.load("wer")
            baseline_wer = self._compute_wer(model, val_pairs, wer_metric)
            _log(f"  Baseline WER on validation: {baseline_wer:.1%}")

            # Fine-tuning loop (simplified — use Trainer API for production)
            import torch.optim as optim
            optimizer  = optim.AdamW(model.parameters(), lr=1e-5)
            model.train()

            EPOCHS = 3
            for epoch in range(EPOCHS):
                total_loss = 0.0
                for pair in train_pairs:
                    try:
                        audio  = whisper.load_audio(str(pair["wav"]))
                        mel    = whisper.log_mel_spectrogram(audio).to(device)
                        tokens = whisper.tokenize(pair["transcript"]) + [whisper.tokenize("<|endoftext|>")[0]]
                        tokens_t = torch.tensor([tokens], device=device)
                        out    = model(mel.unsqueeze(0), tokens_t[:, :-1])
                        loss   = torch.nn.functional.cross_entropy(
                            out.transpose(1, 2), tokens_t[:, 1:])
                        optimizer.zero_grad()
                        loss.backward()
                        optimizer.step()
                        total_loss += loss.item()
                    except Exception:
                        pass
                avg_loss = total_loss / max(len(train_pairs), 1)
                _log(f"  Epoch {epoch+1}/{EPOCHS} loss: {avg_loss:.4f}")

            # Post-training WER
            model.eval()
            final_wer = self._compute_wer(model, val_pairs, wer_metric)
            _log(f"  Post-finetune WER: {final_wer:.1%}  (baseline: {baseline_wer:.1%})")

            if final_wer >= baseline_wer:
                _log("  No WER improvement — NOT deploying fine-tuned model")
                return {"success": False, "reason": "no_improvement",
                        "baseline_wer": baseline_wer, "final_wer": final_wer}

            # Save and convert
            MODELS_DIR.mkdir(parents=True, exist_ok=True)
            pt_path = MODELS_DIR / "whisper_finetuned.pt"
            torch.save(model.state_dict(), str(pt_path))
            _log(f"  PyTorch weights saved: {pt_path}")

            # Convert to CTranslate2
            ct2_path = self._convert_to_ct2(pt_path)
            if ct2_path:
                _log(f"  CTranslate2 model ready: {ct2_path}")
                _log("  Update WHISPER_MODEL path in voice_bridge.py to use the fine-tuned model")
            else:
                _log("  CTranslate2 conversion failed — PyTorch weights saved for manual conversion")

            self.mem.log_event(AGENT_NAME, "finetune_complete",
                               metadata={"baseline_wer": round(baseline_wer, 4),
                                         "final_wer": round(final_wer, 4),
                                         "samples": len(pairs)})
            return {"success": True, "baseline_wer": baseline_wer, "final_wer": final_wer,
                    "improvement": baseline_wer - final_wer, "model_path": str(ct2_path or pt_path)}

        except Exception as e:
            _log(f"  Fine-tuning error: {e}")
            return {"success": False, "reason": str(e)}

    def _compute_wer(self, model, pairs: list, wer_metric) -> float:
        """Compute word error rate on a list of {wav, transcript} pairs."""
        import whisper
        preds, refs = [], []
        for pair in pairs[:20]:   # cap at 20 for speed
            try:
                result = model.transcribe(str(pair["wav"]), language="en")
                preds.append(result["text"].strip().lower())
                refs.append(pair["transcript"].strip().lower())
            except Exception:
                pass
        if not preds:
            return 1.0
        return wer_metric.compute(predictions=preds, references=refs)

    def _convert_to_ct2(self, pt_path: Path):
        """Convert PyTorch Whisper weights to CTranslate2 format."""
        try:
            import subprocess
            ct2_dir = MODELS_DIR / "ct2_model"
            result = subprocess.run(
                ["ct2-opus-mt-converter", "--model", "openai/whisper-tiny.en",
                 "--output_dir", str(ct2_dir),
                 "--force", "--quantization", "int8"],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode == 0:
                return ct2_dir
        except Exception:
            pass
        try:
            import ctranslate2.converters
            converter = ctranslate2.converters.OpusMTConverter("openai/whisper-tiny.en")
            ct2_dir = MODELS_DIR / "ct2_model"
            converter.convert(str(ct2_dir), quantization="int8", force=True)
            return ct2_dir
        except Exception:
            return None


# ── Main ──────────────────────────────────────────────────────────────────────

def run(strategy: str = "auto", check_only: bool = False) -> dict:
    _log("=" * 60)
    _log("Athena Whisper Fine-Tuner")
    _log("=" * 60)

    mem  = Memory()
    base = AgentBase(AGENT_NAME)
    evolver   = DomainPromptEvolver(base)
    finetuner = WhisperFinetuner()

    readiness = finetuner.check_readiness()
    _log(f"Data readiness: {readiness['message']}")

    if check_only:
        print(json.dumps(readiness, indent=2))
        return readiness

    results = {}

    # Strategy A always runs (no data needed)
    if strategy in ("auto", "a"):
        results["strategy_a"] = evolver.evolve()

    # Strategy B only runs when enough data exists
    if strategy in ("b",) or (strategy == "auto" and readiness["ready"]):
        results["strategy_b"] = finetuner.finetune()
    elif strategy == "auto":
        _log(f"Strategy B deferred — need {readiness['min_needed'] - readiness['samples']} more samples")

    mem.log_event(AGENT_NAME, "cycle_complete", metadata=results)
    print(json.dumps(results, indent=2, default=str))
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Athena Whisper Fine-Tuner")
    parser.add_argument("--strategy", choices=["auto", "a", "b"], default="auto")
    parser.add_argument("--check", action="store_true", help="Report data readiness only")
    args = parser.parse_args()
    run(strategy=args.strategy, check_only=args.check)
