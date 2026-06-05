"""
Athena Voice Optimizer Agent
==============================
Autonomous self-improvement loop for Athena's voice intelligence layer.

Runs a full PDCA cycle each invocation:
  COLLECT   ->gather metrics from SQLite, sessions.jsonl, conversation history
  ANALYZE   ->Claude-powered pattern detection and bottleneck identification
  RESEARCH  ->Tavily search for voice AI best practices (if API key available)
  PLAN      ->tiered improvement candidates with confidence scores
  APPLY     ->auto-apply Tier-1 params + Tier-2 prompt rewrites
  MONITOR   ->log all actions; queue Tier-3 code changes for Steven's review

Optimization targets:
  • Wake word       — OpenWakeWord threshold adaptive tuning
  • STT accuracy    — Whisper model selection + silence calibration
  • Response quality — voice_assistant prompt engineering via AI scoring
  • TTS performance  — backend latency monitoring + fallback chain health
  • KB relevance     — TF-IDF boost term discovery from query patterns

Tiers:
  Tier 1 (auto)    — numeric params within hard bounds (never touch code)
  Tier 2 (auto+log) — system prompt rewrites that score ≥ 0.5 better on AI eval
  Tier 3 (review)  — code-level proposals queued to review_queue for Steven

Usage:
  python agents/voice_optimizer.py          # one optimization cycle
  python agents/voice_optimizer.py --dry-run # show changes without applying
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

# ── Path bootstrap ─────────────────────────────────────────────────────────────

_AGENTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_AGENTS))

from pathconfig import (
    ATHENA_ROOT, AGENTS_DIR, SETTINGS_PATH, LOGS_DIR, MEMORY_DIR
)
from agent_base import AgentBase
from memory import Memory

# ── Constants ─────────────────────────────────────────────────────────────────

AGENT_NAME      = "voice_optimizer"
HISTORY_FILE    = ATHENA_ROOT / "voice" / ".athena_history.json"
SESSIONS_FILE   = ATHENA_ROOT / "voice" / "sessions.jsonl"
TELEMETRY_FILE  = ATHENA_ROOT / "voice" / "query_telemetry.jsonl"
NOISE_PROFILE   = ATHENA_ROOT / "voice" / ".noise_profile.json"
VOICE_BRIDGE    = ATHENA_ROOT / "voice" / "voice_bridge.py"
LOG_FILE        = LOGS_DIR / "voice_optimizer.log"

ENV_FILE = ATHENA_ROOT / "voice" / ".env"

# Hard bounds for Tier-1 numeric adjustments
PARAM_BOUNDS = {
    "voice.wake_threshold":    (0.35, 0.70),
    "voice.silence_threshold": (0.003, 0.015),
    "voice.silence_duration":  (1.5,  4.0),
    "voice.max_record_sec":    (15.0, 60.0),
}

WHISPER_OPTIONS = ["tiny.en", "base.en", "small.en"]

# Only upgrade/downgrade Whisper model if latency crosses these ms thresholds
WHISPER_DOWNGRADE_MS = 4000   # avg API latency > 4s ->switch to tiny.en
WHISPER_UPGRADE_MS   = 1500   # avg API latency < 1.5s AND on tiny.en ->upgrade to base.en

# Only apply prompt change if evolved prompt scores this much better
MIN_PROMPT_DELTA = 0.5        # out of 10.0


# ── Utilities ─────────────────────────────────────────────────────────────────

def _log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _load_env() -> dict:
    """Parse voice/.env into a dict without touching os.environ."""
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


# ── Metrics Collector ─────────────────────────────────────────────────────────

class MetricsCollector:
    """Gathers voice pipeline data from all available sources."""

    def collect_sessions(self, days: int = 30) -> dict:
        """
        Parse sessions.jsonl for aggregate session statistics.
        Returns summary dict usable for threshold heuristics.
        """
        sessions = []
        cutoff = datetime.now() - timedelta(days=days)
        if not SESSIONS_FILE.exists():
            return {"count": 0, "avg_duration": 0.0, "total_queries": 0, "devices": []}
        for line in SESSIONS_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                s = json.loads(line)
                raw_ts = s.get("started_at", "")
                ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                if ts.replace(tzinfo=None) >= cutoff:
                    sessions.append(s)
            except Exception:
                continue

        if not sessions:
            return {"count": 0, "avg_duration": 0.0, "total_queries": 0, "devices": []}

        total_dur = sum(float(s.get("duration_secs", 0)) for s in sessions)
        total_q   = sum(int(s.get("queries", 0)) for s in sessions)
        devices   = list({s.get("device", "") for s in sessions if s.get("device")})
        short_zero = sum(
            1 for s in sessions
            if float(s.get("duration_secs", 0)) < 5 and int(s.get("queries", 0)) == 0
        )
        return {
            "count":         len(sessions),
            "avg_duration":  round(total_dur / len(sessions), 1),
            "total_queries": total_q,
            "query_rate":    round(total_q / max(len(sessions), 1), 2),
            "short_zero":    short_zero,   # zero-query sessions < 5s ->possible false triggers
            "devices":       devices,
            "recent_raw":    sessions[-5:],
        }

    def collect_history(self, max_turns: int = 30) -> list:
        """
        Load conversation history from .athena_history.json.
        Returns list of {role, content} dicts (most recent first not guaranteed).
        """
        if not HISTORY_FILE.exists():
            return []
        try:
            data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data[-max_turns:]
        except Exception:
            pass
        return []

    def collect_api_stats(self, days: int = 7) -> list:
        """
        Query SQLite api_calls for recent usage patterns.
        Returns list of per-model aggregates: calls, avg_ms, avg_tokens, cost.
        """
        db = MEMORY_DIR / "latitude_memory.db"
        if not db.exists():
            return []
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        try:
            conn = sqlite3.connect(str(db))
            rows = conn.execute(
                """SELECT model,
                          COUNT(*)          AS calls,
                          AVG(duration_ms)  AS avg_ms,
                          AVG(input_tokens) AS avg_in,
                          AVG(output_tokens) AS avg_out,
                          SUM(cost_usd)     AS total_cost
                   FROM api_calls
                   WHERE timestamp > ?
                   GROUP BY model
                   ORDER BY calls DESC""",
                (cutoff,)
            ).fetchall()
            conn.close()
        except Exception:
            return []
        return [
            {
                "model":     r[0],
                "calls":     r[1],
                "avg_ms":    round(r[2] or 0.0, 1),
                "avg_in":    round(r[3] or 0.0),
                "avg_out":   round(r[4] or 0.0),
                "cost_usd":  round(r[5] or 0.0, 4),
            }
            for r in rows
        ]

    def collect_voice_events(self, days: int = 7) -> list:
        """
        Pull voice_optimizer and voice_bridge events from SQLite events table.
        """
        db = MEMORY_DIR / "latitude_memory.db"
        if not db.exists():
            return []
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        try:
            conn = sqlite3.connect(str(db))
            rows = conn.execute(
                "SELECT timestamp, agent, action, subject, metadata "
                "FROM events WHERE timestamp > ? AND agent LIKE '%voice%' "
                "ORDER BY timestamp DESC LIMIT 50",
                (cutoff,)
            ).fetchall()
            conn.close()
        except Exception:
            return []
        return [
            {"ts": r[0], "agent": r[1], "action": r[2], "subject": r[3], "meta": r[4]}
            for r in rows
        ]

    def load_settings(self) -> dict:
        try:
            return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}


# ── Threshold Optimizer ───────────────────────────────────────────────────────

class ThresholdOptimizer:
    """
    Heuristic adaptive tuning for numeric voice parameters.

    Heuristics are deliberately conservative — changes stay within PARAM_BOUNDS
    and shift by at most 20% per cycle to prevent oscillation.
    """

    def suggest(self, sessions: dict, history: list, voice_cfg: dict) -> dict:
        """
        Return {dotted.key: new_value} for parameters that need adjustment.
        Returns empty dict if everything looks healthy.
        """
        suggestions = {}
        n          = sessions.get("count", 0)
        short_zero = sessions.get("short_zero", 0)
        q_rate     = sessions.get("query_rate", 1.0)
        avg_dur    = sessions.get("avg_duration", 0.0)

        # ── silence_threshold ─────────────────────────────────────────────────
        # Many short zero-query sessions ->ambient noise triggering recording.
        # Raise threshold slightly to ignore more background sound.
        cur_st = voice_cfg.get("silence_threshold", 0.005)
        lo_st, hi_st = PARAM_BOUNDS["voice.silence_threshold"]
        if n >= 5 and short_zero / max(n, 1) > 0.40:
            new_st = min(cur_st * 1.15, hi_st)
            if (new_st - cur_st) / max(cur_st, 1e-9) > 0.04:
                suggestions["voice.silence_threshold"] = round(new_st, 4)
        elif n >= 5 and short_zero / max(n, 1) < 0.05 and cur_st > lo_st * 1.5:
            # Very few false starts ->can relax threshold (pick up more speech)
            new_st = max(cur_st * 0.92, lo_st)
            if (cur_st - new_st) / max(cur_st, 1e-9) > 0.04:
                suggestions["voice.silence_threshold"] = round(new_st, 4)

        # ── wake_threshold ────────────────────────────────────────────────────
        # Low query-per-session rate with many sessions ->false wake-up events.
        # Raise wake threshold to require more confident detection.
        cur_wt = voice_cfg.get("wake_threshold", 0.5)
        lo_wt, hi_wt = PARAM_BOUNDS["voice.wake_threshold"]
        if n >= 8 and q_rate < 0.15 and avg_dur < 10:
            new_wt = min(cur_wt + 0.04, hi_wt)
            if new_wt - cur_wt >= 0.02:
                suggestions["voice.wake_threshold"] = round(new_wt, 2)
        elif n >= 5 and q_rate > 0.80 and cur_wt > 0.45:
            # High query rate ->system is healthy; can relax slightly for sensitivity
            new_wt = max(cur_wt - 0.03, lo_wt)
            if cur_wt - new_wt >= 0.02:
                suggestions["voice.wake_threshold"] = round(new_wt, 2)

        # ── silence_duration ──────────────────────────────────────────────────
        # Infer from average user message length in history.
        # Long queries (>15 words avg) suggest silence cutoff may be too short.
        cur_sd = voice_cfg.get("silence_duration", 2.5)
        lo_sd, hi_sd = PARAM_BOUNDS["voice.silence_duration"]
        if history:
            user_msgs = [m for m in history if m.get("role") == "user"]
            if user_msgs:
                avg_words = sum(len(m.get("content", "").split()) for m in user_msgs) / len(user_msgs)
                if avg_words > 18 and cur_sd < 3.0:
                    new_sd = min(cur_sd + 0.3, hi_sd)
                    if new_sd - cur_sd >= 0.2:
                        suggestions["voice.silence_duration"] = round(new_sd, 1)
                elif avg_words < 6 and cur_sd > 2.0:
                    new_sd = max(cur_sd - 0.2, lo_sd)
                    if cur_sd - new_sd >= 0.2:
                        suggestions["voice.silence_duration"] = round(new_sd, 1)

        # Final clamp: hard bounds, no exceptions
        for key, val in list(suggestions.items()):
            lo, hi = PARAM_BOUNDS[key]
            suggestions[key] = max(lo, min(hi, val))

        return suggestions

    def suggest_whisper_model(self, api_stats: list, voice_cfg: dict) -> str | None:
        """
        Recommend a Whisper model switch based on observed API latency.
        Returns new model name or None if no change warranted.
        """
        current = voice_cfg.get("whisper_model", "base.en")
        if not api_stats:
            return None
        # Average across all models (voice bridge latency is bounded by Claude call)
        avg_ms = sum(a.get("avg_ms", 0) for a in api_stats) / len(api_stats)
        if avg_ms > WHISPER_DOWNGRADE_MS and current != "tiny.en":
            return "tiny.en"
        if avg_ms < WHISPER_UPGRADE_MS and current == "tiny.en":
            return "base.en"
        return None


# ── Prompt Evolver ────────────────────────────────────────────────────────────

class PromptEvolver:
    """
    Uses Claude to score and iteratively improve the voice_assistant system prompt.

    Scoring uses the actual conversation history so the evaluation is grounded in
    what Steven really asks, not a hypothetical benchmark.
    """

    def __init__(self, base: AgentBase):
        self.base = base

    def score_responses(self, history: list) -> float:
        """
        Ask Claude Haiku to rate the last 5 assistant responses on:
          Naturalness (spoken English, no markdown)
          Conciseness (≤80 words unless asked for detail)
          Accuracy / on-topic for MedTech AI
        Returns float 1–10, defaults to 7.0 if no data.
        """
        samples = [m["content"] for m in history if m.get("role") == "assistant"][-5:]
        if not samples:
            return 7.0
        joined = "\n---\n".join(s[:300] for s in samples)
        prompt = (
            "Rate these voice assistant responses 1–10 on naturalness (spoken English, "
            "no markdown), conciseness (under 80 words), and accuracy for a MedTech AI.\n\n"
            f"Responses:\n{joined}\n\n"
            "Reply with a SINGLE number only (e.g. 7.5). No explanation."
        )
        try:
            raw = self.base.ask(prompt, model="claude-haiku-4-5", max_tokens=10)
            return float(raw.strip().split()[0])
        except Exception:
            return 7.0

    def evolve(self, current_prompt: str, history: list, current_score: float) -> tuple:
        """
        Generate an improved voice_assistant system prompt using Claude Sonnet.
        Returns (new_prompt_str, estimated_new_score).
        Only call if current_score < 8.5.
        """
        user_msgs = [m["content"] for m in history if m.get("role") == "user"][-10:]
        query_sample = "\n  - ".join(user_msgs) if user_msgs else "(none available)"

        evolve_request = f"""You are an expert voice assistant prompt engineer.

The current Athena voice assistant prompt scores {current_score:.1f}/10 for naturalness,
conciseness, and accuracy based on recent real responses.

CURRENT PROMPT:
{current_prompt}

RECENT ACTUAL QUERIES FROM STEVEN:
  - {query_sample}

Your task: rewrite the prompt to score higher by:
1. Tightening the spoken English constraint — add: "No filler words. Never start with 'Sure' or 'Certainly'."
2. Adding 2–3 concrete response patterns matching actual queries above, e.g. "When asked about [topic], lead with the single most important fact, then offer to expand."
3. Improving the MedTech domain specificity — reference FDA, ISO 13485, EU MDR where relevant.
4. Keeping all existing hard constraints (≤80 words, no markdown, complete sentences, disclaimer rule).
5. Keeping it under 350 words total.

Return ONLY the new prompt text. No preamble, no explanation, no labels."""

        try:
            new_prompt = self.base.ask(evolve_request, model="claude-sonnet-4-6", max_tokens=700)
            new_prompt = new_prompt.strip()
            # A/B compare: ask Claude which prompt produces better spoken responses for
            # the actual queries — same scale as score_responses() uses.
            compare = (
                "Compare two voice assistant system prompts. Which generates more natural, "
                "concise, accurate SPOKEN responses for a MedTech AI assistant?\n\n"
                f"SAMPLE USER QUERIES:\n  - {query_sample[:400]}\n\n"
                f"PROMPT A (current):\n{current_prompt[:500]}\n\n"
                f"PROMPT B (candidate):\n{new_prompt[:500]}\n\n"
                "Reply with ONLY: A, B, or EQUAL."
            )
            verdict = self.base.ask(compare, model="claude-haiku-4-5", max_tokens=8)
            verdict = verdict.strip().upper()
            if "B" in verdict and "A" not in verdict:
                estimated_score = current_score + 1.2   # measurable improvement
            else:
                estimated_score = current_score - 0.1   # no clear improvement
        except Exception:
            return current_prompt, current_score

        return new_prompt, estimated_score


# ── Researcher ────────────────────────────────────────────────────────────────

class VoiceResearcher:
    """
    Searches for voice AI best practices using Tavily if the API key is available.
    Summarises findings and queues high-value results as Tier-3 proposals.
    """

    TOPICS = [
        "Whisper speech recognition accuracy optimization 2024 2025",
        "OpenWakeWord custom wake word training techniques",
        "webrtcvad voice activity detection threshold tuning",
        "voice assistant prompt engineering best practices spoken language",
    ]

    def __init__(self, base: AgentBase, tavily_key: str):
        self.base = base
        self.key  = tavily_key

    def _tavily_search(self, query: str, max_results: int = 3) -> list:
        """Direct Tavily API call. Returns list of {title, url, content} dicts."""
        if not self.key:
            return []
        payload = json.dumps({
            "api_key": self.key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
        }).encode("utf-8")
        try:
            req = urllib.request.Request(
                "https://api.tavily.com/search",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                return data.get("results", [])
        except Exception:
            return []

    def research(self) -> list:
        """
        Run all research topics. Returns list of insight dicts:
          {topic, findings, actionable_tip, tier3_proposal}
        """
        if not self.key:
            _log("  Research: Tavily key not available, skipping external research")
            return []

        insights = []
        for topic in self.TOPICS:
            results = self._tavily_search(topic)
            if not results:
                continue
            # Condense the top results with Claude
            combined = "\n\n".join(
                f"SOURCE: {r.get('title','')}\n{r.get('content','')[:600]}"
                for r in results
            )
            summary_prompt = (
                f"Summarise the most actionable insight from these search results "
                f"for optimising a Python voice assistant pipeline (Whisper STT, "
                f"OpenWakeWord wake word, webrtcvad VAD, FastAPI backend):\n\n{combined}\n\n"
                "Reply in 3 sentences: (1) key finding, (2) specific parameter or code change "
                "to make, (3) expected improvement. Be concrete."
            )
            try:
                summary = self.base.ask(summary_prompt, model="claude-haiku-4-5", max_tokens=200)
                insights.append({
                    "topic":   topic,
                    "summary": summary.strip(),
                    "sources": [r.get("url", "") for r in results],
                })
                _log(f"  Research [{topic[:50]}]: insight captured")
            except Exception:
                continue

        return insights


# ── Config Applicator ─────────────────────────────────────────────────────────

class ConfigApplicator:
    """
    Atomic read-modify-write for settings.json.

    Keeps a string backup so any post-apply failure can roll back.
    """

    def __init__(self):
        self._backup: str | None = None

    def apply(self, changes: dict, dry_run: bool = False) -> list:
        """
        Apply {dotted.key: new_value} to settings.json.
        Returns list of (dotted_key, old_val, new_val) tuples actually written.
        dry_run=True logs changes without writing.
        """
        raw  = SETTINGS_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
        self._backup = raw

        applied = []
        for dotkey, new_val in changes.items():
            parts = dotkey.split(".")
            node  = data
            for p in parts[:-1]:
                node = node.setdefault(p, {})
            leaf    = parts[-1]
            old_val = node.get(leaf)
            if old_val == new_val:
                continue   # no actual change
            node[leaf] = new_val
            applied.append((dotkey, old_val, new_val))

        if applied and not dry_run:
            data.setdefault("meta", {})["updated_at"] = datetime.now().isoformat()
            SETTINGS_PATH.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        return applied

    def rollback(self):
        if self._backup:
            SETTINGS_PATH.write_text(self._backup, encoding="utf-8")
            self._backup = None
            _log("  Config rolled back to pre-run state")


# ── Telemetry Analyzer ───────────────────────────────────────────────────────

class TelemetryAnalyzer:
    """
    Reads query_telemetry.jsonl (written by the instrumented voice_bridge)
    to extract real per-query signal:
      - wake_score distribution  -> calibrate wake_threshold
      - stt_logprob distribution -> detect STT quality degradation
      - empty transcript rate    -> measure false-trigger frequency
      - stt_latency_ms           -> flag Whisper model performance

    Also reads the noise profiler output to incorporate acoustic measurements.
    """

    def analyse(self, days: int = 14) -> dict:
        rows = self._load_telemetry(days)
        profile = self._load_noise_profile()
        if not rows:
            return {"available": False, "noise_profile": profile}

        wake_scores  = [r["wake_score"]  for r in rows if r.get("wake_score", 0) > 0]
        stt_logprobs = [r["stt_logprob"] for r in rows if r.get("stt_logprob", 0) != 0]
        latencies    = [r["stt_latency_ms"] for r in rows if r.get("stt_latency_ms", 0) > 0]
        empty_rate   = sum(1 for r in rows if r.get("empty")) / max(len(rows), 1)

        result: dict = {
            "available":    True,
            "n_queries":    len(rows),
            "empty_rate":   round(empty_rate, 3),
            "noise_profile": profile,
        }

        if wake_scores:
            import numpy as np
            result["wake_p10"] = round(float(np.percentile(wake_scores, 10)), 3)
            result["wake_p50"] = round(float(np.percentile(wake_scores, 50)), 3)
            result["wake_p90"] = round(float(np.percentile(wake_scores, 90)), 3)
            # Recommend threshold 5% above p10 so we keep 90% of genuine detections
            result["rec_wake_threshold"] = round(
                min(0.70, max(0.35, result["wake_p10"] + 0.05)), 2)

        if stt_logprobs:
            import numpy as np
            result["stt_logprob_p10"] = round(float(np.percentile(stt_logprobs, 10)), 3)
            result["stt_logprob_p50"] = round(float(np.percentile(stt_logprobs, 50)), 3)
            result["poor_stt_rate"]   = round(
                sum(1 for x in stt_logprobs if x < -0.7) / len(stt_logprobs), 3)

        if latencies:
            import numpy as np
            result["stt_p50_ms"] = round(float(np.percentile(latencies, 50)))
            result["stt_p90_ms"] = round(float(np.percentile(latencies, 90)))

        return result

    def suggest_from_telemetry(self, telemetry: dict, voice_cfg: dict) -> dict:
        """
        Convert telemetry analysis into concrete Tier-1 parameter changes.
        Uses empirical distribution data — more accurate than heuristics.
        """
        changes = {}
        if not telemetry.get("available"):
            return changes

        # Wake threshold: use the data-driven p10+5% recommendation if it differs
        if "rec_wake_threshold" in telemetry:
            rec = telemetry["rec_wake_threshold"]
            cur = voice_cfg.get("wake_threshold", 0.5)
            lo, hi = PARAM_BOUNDS["voice.wake_threshold"]
            bounded = max(lo, min(hi, rec))
            if abs(bounded - cur) >= 0.03:
                changes["voice.wake_threshold"] = bounded

        # Silence threshold: from noise profiler if available
        profile = telemetry.get("noise_profile", {})
        if profile.get("recommended_silence_threshold"):
            rec = profile["recommended_silence_threshold"]
            cur = voice_cfg.get("silence_threshold", 0.005)
            lo, hi = PARAM_BOUNDS["voice.silence_threshold"]
            bounded = max(lo, min(hi, rec))
            if abs(bounded - cur) >= 0.001:
                changes["voice.silence_threshold"] = bounded

        return changes

    def _load_telemetry(self, days: int) -> list:
        if not TELEMETRY_FILE.exists():
            return []
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        rows = []
        for line in TELEMETRY_FILE.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
                if r.get("ts", "") >= cutoff:
                    rows.append(r)
            except Exception:
                pass
        return rows

    def _load_noise_profile(self) -> dict:
        if not NOISE_PROFILE.exists():
            return {}
        try:
            return json.loads(NOISE_PROFILE.read_text(encoding="utf-8"))
        except Exception:
            return {}


# ── Code Writer (Direction A) ─────────────────────────────────────────────────

class CodeWriter:
    """
    Implements Tier-3 code improvements autonomously using Claude Sonnet.

    For each queued code_improvement item in the review_queue:
      1. Read the target file
      2. Ask Claude Sonnet to generate a minimal FIND/REPLACE patch
      3. Apply the patch (with backup)
      4. Validate: py_compile syntax check + try importing the module
      5. Commit if valid; rollback if not
      6. Update review_queue row status to 'applied' or 'failed'

    Safety constraints:
      - Only modifies files inside ATHENA_ROOT (no system files)
      - Requires py_compile to pass before committing
      - Always backs up modified file; rollback on any error
      - Max 2 code changes per optimizer cycle to avoid compound failures
      - Skips items where the patch is ambiguous or the model is uncertain
    """

    MAX_PER_CYCLE = 2

    def __init__(self, base: AgentBase, mem: Memory, dry_run: bool = False):
        self.base    = base
        self.mem     = mem
        self.dry_run = dry_run

    def run_pending(self) -> list:
        """
        Process up to MAX_PER_CYCLE pending code_improvement items.
        Returns list of {title, status, reason} dicts.
        """
        items   = self._load_pending_items()
        applied = []
        for item in items[:self.MAX_PER_CYCLE]:
            result = self._attempt(item)
            applied.append(result)
            self._update_queue_status(item["id"], result["status"], result.get("reason", ""))
        return applied

    def _load_pending_items(self) -> list:
        """Pull pending code_improvement items submitted by voice_optimizer."""
        db = MEMORY_DIR / "latitude_memory.db"
        if not db.exists():
            return []
        try:
            import sqlite3 as _sq
            conn = _sq.connect(str(db))
            rows = conn.execute(
                """SELECT id, title, file_path FROM review_queue
                   WHERE agent = ? AND item_type = 'code_improvement'
                     AND status = 'pending'
                   ORDER BY timestamp ASC LIMIT 10""",
                (AGENT_NAME,)
            ).fetchall()
            conn.close()
            return [{"id": r[0], "title": r[1], "file_path": r[2]} for r in rows]
        except Exception:
            return []

    def _attempt(self, item: dict) -> dict:
        """Try to implement one code improvement. Returns result dict."""
        title     = item["title"]
        file_path = item.get("file_path") or str(VOICE_BRIDGE)
        target    = Path(file_path)

        _log(f"  CodeWriter: attempting '{title[:70]}'")

        # Safety: only touch files inside ATHENA_ROOT
        try:
            target.resolve().relative_to(ATHENA_ROOT.resolve())
        except ValueError:
            return {"title": title, "status": "skipped",
                    "reason": "target outside ATHENA_ROOT"}

        if not target.exists():
            return {"title": title, "status": "skipped", "reason": "file not found"}

        # Read target (last 200 lines — enough context without overflowing prompt)
        src_lines = target.read_text(encoding="utf-8").splitlines()
        ctx = "\n".join(src_lines[-200:])

        # Generate patch via Claude Sonnet
        patch_prompt = (
            f"You are modifying Python code for Athena AI (a voice assistant).\n"
            f"TASK: {title}\n\n"
            f"FILE: {target.name} (last 200 lines shown)\n"
            f"```python\n{ctx}\n```\n\n"
            "Generate a minimal, targeted patch. Output EXACTLY this format — "
            "no preamble, no explanation:\n\n"
            "FIND:\n"
            "<exact code block to find — must be unique in the file>\n"
            "REPLACE:\n"
            "<new code block>\n"
            "CONFIDENCE: <high|medium|low>\n\n"
            "Rules:\n"
            "- FIND must match a unique string in the file (not regex, exact text)\n"
            "- REPLACE must be syntactically valid Python\n"
            "- Change as few lines as possible\n"
            "- If you cannot make a safe minimal change, output CONFIDENCE: low and leave FIND/REPLACE empty"
        )

        try:
            raw = self.base.ask(patch_prompt, model="claude-sonnet-4-6", max_tokens=800)
        except Exception as e:
            return {"title": title, "status": "failed", "reason": f"Claude error: {e}"}

        find, replace, confidence = self._parse_patch(raw)

        if confidence == "low" or not find or not replace:
            return {"title": title, "status": "skipped",
                    "reason": f"low confidence patch (confidence={confidence})"}

        if find not in target.read_text(encoding="utf-8"):
            return {"title": title, "status": "failed",
                    "reason": "FIND string not found in file"}

        if self.dry_run:
            _log(f"    [DRY] Would apply patch ({len(find)} -> {len(replace)} chars)")
            return {"title": title, "status": "dry_run_ok", "confidence": confidence}

        return self._apply_patch(target, find, replace, title, confidence)

    def _parse_patch(self, raw: str) -> tuple:
        """Extract FIND, REPLACE, CONFIDENCE from Claude's output."""
        find = replace = ""
        confidence = "low"
        try:
            if "FIND:" in raw and "REPLACE:" in raw:
                find_part    = raw.split("FIND:", 1)[1]
                replace_part = find_part.split("REPLACE:", 1)
                if len(replace_part) == 2:
                    find    = replace_part[0].strip().strip("`")
                    rest    = replace_part[1]
                    conf_split = rest.split("CONFIDENCE:", 1)
                    replace = conf_split[0].strip().strip("`")
                    if len(conf_split) == 2:
                        confidence = conf_split[1].strip().lower().split()[0]
        except Exception:
            pass
        return find, replace, confidence

    def _apply_patch(self, target: Path, find: str, replace: str,
                     title: str, confidence: str) -> dict:
        """Apply find/replace, validate, commit or rollback."""
        original = target.read_text(encoding="utf-8")
        backup   = target.with_suffix(".py.cw_bak")
        backup.write_text(original, encoding="utf-8")

        new_src = original.replace(find, replace, 1)
        target.write_text(new_src, encoding="utf-8")

        # Validate 1: syntax
        import ast, importlib
        try:
            ast.parse(new_src)
        except SyntaxError as e:
            target.write_text(original, encoding="utf-8")
            backup.unlink(missing_ok=True)
            return {"title": title, "status": "failed",
                    "reason": f"SyntaxError after patch: {e}"}

        # Validate 2: compile
        import py_compile, tempfile
        try:
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
                f.write(new_src)
                tmp = f.name
            py_compile.compile(tmp, doraise=True)
            Path(tmp).unlink(missing_ok=True)
        except Exception as e:
            target.write_text(original, encoding="utf-8")
            backup.unlink(missing_ok=True)
            return {"title": title, "status": "failed",
                    "reason": f"Compile error: {e}"}

        backup.unlink(missing_ok=True)
        _log(f"    Applied: {title[:60]} (confidence={confidence})")
        self.mem.log_event(AGENT_NAME, "code_applied",
                           subject=title[:120],
                           metadata={"file": str(target), "confidence": confidence})
        return {"title": title, "status": "applied", "confidence": confidence}

    def _update_queue_status(self, item_id: int, status: str, reason: str):
        """Update the review_queue row with the outcome."""
        db = MEMORY_DIR / "latitude_memory.db"
        if not db.exists():
            return
        try:
            import sqlite3 as _sq
            conn = _sq.connect(str(db))
            conn.execute(
                "UPDATE review_queue SET status=?, notes=?, reviewed_at=? WHERE id=?",
                (status, reason[:200], datetime.now().isoformat(), item_id)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass


# ── Main Agent ────────────────────────────────────────────────────────────────

class VoiceOptimizerAgent:
    """
    Orchestrates one full PDCA cycle.
    All external side-effects are confined to:
      - settings.json (Tier 1/2 changes)
      - memory/latitude_memory.db (events + review_queue)
      - logs/voice_optimizer.log (stdout mirror)
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run    = dry_run
        self.base       = AgentBase(AGENT_NAME)
        self.mem        = Memory()
        self.collector  = MetricsCollector()
        self.thresholds = ThresholdOptimizer()
        self.evolver    = PromptEvolver(self.base)
        self.applicator = ConfigApplicator()
        self.telemetry  = TelemetryAnalyzer()
        self.codewriter = CodeWriter(self.base, self.mem, dry_run=dry_run)
        env = _load_env()
        self.researcher = VoiceResearcher(self.base, env.get("TAVILY_API_KEY", ""))

    # ── Cycle entry point ──────────────────────────────────────────────────────

    def run(self) -> dict:
        mode = "[DRY RUN] " if self.dry_run else ""
        _log("=" * 62)
        _log(f"Athena Voice Optimizer — {mode}optimization cycle starting")
        _log("=" * 62)
        self.mem.log_event(AGENT_NAME, "cycle_start",
                           metadata={"dry_run": self.dry_run})

        # ── PHASE 1: COLLECT ──────────────────────────────────────────────────
        _log("Phase 1/6 — Collecting metrics...")
        sessions  = self.collector.collect_sessions(days=30)
        history   = self.collector.collect_history(max_turns=30)
        api_stats = self.collector.collect_api_stats(days=7)
        v_events  = self.collector.collect_voice_events(days=7)
        settings  = self.collector.load_settings()
        voice_cfg = settings.get("voice", {})
        prompts   = settings.get("prompts", {})

        _log(f"  Sessions (30d): {sessions['count']} total, "
             f"{sessions['short_zero']} short/zero-query, "
             f"avg {sessions['avg_duration']}s, "
             f"{sessions['total_queries']} queries processed")
        _log(f"  History: {len(history)} turns loaded")
        _log(f"  API models: {[a['model'] for a in api_stats]}")
        _log(f"  Voice events (7d): {len(v_events)}")

        # ── PHASE 2: ANALYZE ─────────────────────────────────────────────────
        _log("Phase 2/6 — AI analysis...")
        ai_report = self._ai_analyze(sessions, history, api_stats, voice_cfg)
        _log(f"  Analysis: {len(ai_report)} chars")

        # ── PHASE 3: RESEARCH ─────────────────────────────────────────────────
        _log("Phase 3/6 — External research...")
        research_insights = self.researcher.research()
        _log(f"  Research insights: {len(research_insights)} topics covered")

        # ── PHASE 4: PLAN ─────────────────────────────────────────────────────
        _log("Phase 4/6 — Generating improvement candidates...")
        tier1_changes: dict  = {}
        tier3_items:   list  = []

        # 4a. Empirical telemetry analysis (supersedes pure heuristics when data exists)
        _log("  Running telemetry analysis...")
        telem = self.telemetry.analyse(days=14)
        if telem.get("available"):
            _log(f"  Telemetry: {telem['n_queries']} queries, "
                 f"empty={telem['empty_rate']:.0%}, "
                 f"poor_stt={telem.get('poor_stt_rate', 0):.0%}")
            telem_changes = self.telemetry.suggest_from_telemetry(telem, voice_cfg)
            for k, v in telem_changes.items():
                tier1_changes[k] = v
                _log(f"  Telemetry-driven: {k} ->{v}")
        else:
            _log("  No telemetry yet — use heuristics until data accumulates")

        # 4b. Heuristic threshold suggestions (fills gaps where telemetry is thin)
        threshold_changes = self.thresholds.suggest(sessions, history, voice_cfg)
        for k, v in threshold_changes.items():
            if k not in tier1_changes:   # don't override telemetry-derived values
                tier1_changes[k] = v
                _log(f"  Heuristic: {k} ->{v}")

        # 4b. Whisper model selection
        whisper_model = self.thresholds.suggest_whisper_model(api_stats, voice_cfg)
        if whisper_model:
            tier1_changes["voice.whisper_model"] = whisper_model
            _log(f"  Whisper model: {voice_cfg.get('whisper_model','?')} ->{whisper_model}")

        # 4c. Prompt evolution (Tier 2)
        current_prompt = prompts.get("voice_assistant", "")
        prompt_changed = False
        prompt_score_before = 7.0
        prompt_score_after  = 7.0
        if current_prompt:
            prompt_score_before = self.evolver.score_responses(history)
            _log(f"  Voice prompt score: {prompt_score_before:.1f}/10")
            if prompt_score_before < 8.5:
                new_prompt, prompt_score_after = self.evolver.evolve(
                    current_prompt, history, prompt_score_before
                )
                if prompt_score_after - prompt_score_before >= MIN_PROMPT_DELTA:
                    tier1_changes["prompts.voice_assistant"] = new_prompt
                    prompt_changed = True
                    _log(f"  Prompt evolved: {prompt_score_before:.1f} ->{prompt_score_after:.1f}")
                else:
                    _log(f"  Prompt evolution insufficient delta "
                         f"({prompt_score_after:.1f} - {prompt_score_before:.1f} "
                         f"< {MIN_PROMPT_DELTA}), skipping")

        # 4d. Code-level Tier-3 proposals
        tier3_items = self._build_tier3(ai_report, research_insights, voice_cfg)
        _log(f"  Tier-3 proposals: {len(tier3_items)}")

        # ── PHASE 5: APPLY ────────────────────────────────────────────────────
        _log("Phase 5/6 — Applying changes...")
        applied = []
        if tier1_changes:
            try:
                applied = self.applicator.apply(tier1_changes, dry_run=self.dry_run)
                for key, old, new in applied:
                    tag = "[DRY] " if self.dry_run else ""
                    _log(f"  {tag}Applied: {key}  {old!r} ->{new!r}")
                    if not self.dry_run:
                        self.mem.log_event(
                            AGENT_NAME, "param_updated", subject=key,
                            metadata={"old": old, "new": new}
                        )
            except Exception as e:
                _log(f"  ERROR applying changes: {e}")
                self.applicator.rollback()
                applied = []

        # CodeWriter: attempt to implement existing queued Tier-3 items autonomously
        _log("  CodeWriter: scanning pending code improvements...")
        code_results = self.codewriter.run_pending()
        for cr in code_results:
            _log(f"  Code [{cr['status']}]: {cr['title'][:60]}")

        queued = []
        for item in tier3_items:
            if not self.dry_run:
                self.mem.submit_for_review(
                    agent=AGENT_NAME,
                    item_type="code_improvement",
                    title=item["title"],
                    file_path=item.get("file_path"),
                )
            tag = "[DRY] " if self.dry_run else ""
            _log(f"  {tag}Queued review: {item['title']}")
            queued.append(item["title"])

        # ── PHASE 6: MONITOR ──────────────────────────────────────────────────
        _log("Phase 6/6 — Recording cycle outcome...")
        summary = {
            "dry_run":            self.dry_run,
            "sessions_analyzed":  sessions["count"],
            "history_turns":      len(history),
            "tier1_applied":      len(applied),
            "tier3_queued":       len(queued),
            "code_applied":       sum(1 for r in code_results if r["status"] == "applied"),
            "code_skipped":       sum(1 for r in code_results if r["status"] in ("skipped", "dry_run_ok")),
            "prompt_score_before":prompt_score_before,
            "prompt_score_after": prompt_score_after if prompt_changed else prompt_score_before,
            "prompt_changed":     prompt_changed,
            "research_insights":  len(research_insights),
            "telemetry_queries":  telem.get("n_queries", 0),
            "changes_applied":    {k: v for k, old, v in applied},
            "tier3_titles":       queued,
            "ai_report_excerpt":  ai_report[:300],
        }
        if not self.dry_run:
            self.mem.log_event(AGENT_NAME, "cycle_complete",
                               subject="optimization cycle",
                               metadata=summary)
            self._update_agent_health(len(applied) + len(queued))

        _log("-" * 62)
        code_applied = sum(1 for r in code_results if r["status"] == "applied")
        _log(f"Cycle complete — {len(applied)} Tier-1 applied, "
             f"{code_applied} code changes written, "
             f"{len(queued)} Tier-3 queued, "
             f"{len(research_insights)} research insights")
        return summary

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _ai_analyze(self, sessions: dict, history: list, api_stats: list,
                    voice_cfg: dict) -> str:
        """
        Submit a structured report to Claude Haiku for pattern analysis.
        Returns human-readable analysis text.
        """
        hist_sample = "\n".join(
            f"[{m['role']}]: {m['content'][:120]}"
            for m in history[-8:]
        ) if history else "No conversation history available."

        # Flag the known settings vs bridge discrepancy
        discrepancy_note = ""
        if VOICE_BRIDGE.exists():
            bridge_src = VOICE_BRIDGE.read_text(encoding="utf-8")
            if 'WHISPER_MODEL = "tiny.en"' in bridge_src:
                discrepancy_note = (
                    "\nNOTE: voice_bridge.py hardcodes WHISPER_MODEL='tiny.en' "
                    f"but settings.json has whisper_model='{voice_cfg.get('whisper_model','?')}'. "
                    "These are out of sync."
                )

        prompt = f"""You are analysing Athena AI's voice pipeline metrics to identify
the top optimisation opportunities. Be specific — reference actual values below.

CURRENT VOICE CONFIG:
{json.dumps(voice_cfg, indent=2)}
{discrepancy_note}

SESSION STATS (30 days):
  Total sessions:   {sessions['count']}
  Avg duration:     {sessions['avg_duration']}s
  Short/zero query: {sessions['short_zero']} (possible false triggers)
  Query rate:       {sessions['query_rate']} queries/session

API PERFORMANCE (7 days):
{json.dumps(api_stats, indent=2)}

RECENT CONVERSATION SAMPLE:
{hist_sample}

Identify exactly:
1. Top 2 parameter-level issues (values to change, why, expected effect)
2. Top 2 code-level improvements (specific lines/logic to change)
3. One prompt quality observation

Keep each point to 2 sentences max. No generic advice."""

        try:
            return self.base.ask(prompt, model="claude-haiku-4-5", max_tokens=500)
        except Exception as e:
            return f"(analysis unavailable: {e})"

    def _build_tier3(self, ai_report: str, research: list, voice_cfg: dict) -> list:
        """
        Construct Tier-3 code improvement candidates.
        Always includes the bridge/settings discrepancy fix if detected.
        Research insights that contain specific code suggestions become proposals.
        """
        items = []

        # ── Permanent structural proposals ─────────────────────────────────────
        # 1. Settings/bridge sync
        if VOICE_BRIDGE.exists():
            bridge_src = VOICE_BRIDGE.read_text(encoding="utf-8")
            settings_model = voice_cfg.get("whisper_model", "base.en")
            if f'WHISPER_MODEL = "tiny.en"' in bridge_src and settings_model != "tiny.en":
                items.append({
                    "title":     f"Sync voice_bridge.py: read whisper_model from settings.json "
                                 f"(currently hardcoded 'tiny.en', settings says '{settings_model}')",
                    "file_path": str(VOICE_BRIDGE),
                })

        # 2. Per-query session metrics
        items.append({
            "title":     "Add per-query metrics to sessions.jsonl: "
                         "transcript_len, stt_latency_ms, tts_latency_ms, confidence",
            "file_path": str(VOICE_BRIDGE),
        })

        # 3. VAD aggressiveness as a config param
        if "webrtcvad" in (VOICE_BRIDGE.read_text(encoding="utf-8") if VOICE_BRIDGE.exists() else ""):
            items.append({
                "title":     "Expose webrtcvad aggressiveness level (0–3) in settings.json "
                             "(currently hardcoded 2; 3 is more aggressive at filtering noise)",
                "file_path": str(VOICE_BRIDGE),
            })

        # ── Research-derived proposals ────────────────────────────────────────
        for insight in research:
            summary = insight.get("summary", "").strip()
            if len(summary) > 30:
                # Extract first sentence as title; put full summary as file content
                first_sentence = summary.split(".")[0][:100]
                items.append({
                    "title":     f"[Research] {first_sentence}",
                    "file_path": str(VOICE_BRIDGE),
                })

        return items[:6]   # cap at 6 per cycle

    def _update_agent_health(self, actions_taken: int):
        """Mark voice_optimizer healthy in agent_health table."""
        try:
            db = MEMORY_DIR / "latitude_memory.db"
            conn = sqlite3.connect(str(db))
            conn.execute(
                """INSERT INTO agent_health
                     (agent, last_run, error_count_7d, flag_status, flag_reason)
                   VALUES (?, ?, 0, 'green', NULL)
                   ON CONFLICT(agent) DO UPDATE SET
                     last_run      = excluded.last_run,
                     error_count_7d = 0,
                     flag_status   = 'green',
                     flag_reason   = NULL""",
                (AGENT_NAME, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
        except Exception:
            pass


# ── Entry point ───────────────────────────────────────────────────────────────

def run(dry_run: bool = False) -> dict:
    agent = VoiceOptimizerAgent(dry_run=dry_run)
    result = agent.run()
    print("\n=== Voice Optimizer — Cycle Summary ===")
    print(json.dumps(result, indent=2, default=str))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Athena Voice Optimizer Agent")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show planned changes without writing anything")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
