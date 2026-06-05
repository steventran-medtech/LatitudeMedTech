"""
Latitude MedTech — Settings Manager
=====================================
All agents import this to read their configuration.
Settings are stored in ~/Athena/settings.json and editable
from the Athena UI without touching code.

Usage:
    from settings_manager import settings

    # Read agent config
    threshold = settings.get("rag.silence_threshold", 0.005)
    prompt    = settings.get_prompt("content_agent")
    template  = settings.get("documents.disclaimer")

    # Settings auto-reload if file changes
"""

import json
import os
from datetime import datetime

from pathconfig import SETTINGS_PATH

# ── Default settings ──────────────────────────────────────────────────────────
DEFAULTS = {
    "meta": {
        "version":    "1.0",
        "updated_at": datetime.now().isoformat(),
        "company":    "Latitude MedTech LLC",
        "location":   "San Diego, CA",
        "website":    "latitudemedtech.com",
    },

    # ── Voice assistant ────────────────────────────────────────────────────────
    "voice": {
        "wake_word":         "alexa",
        "wake_threshold":    0.5,
        "silence_threshold": 0.005,
        "silence_duration":  2.5,
        "max_record_sec":    30,
        "whisper_model":     "base.en",
        "tts_enabled":       True,
    },

    # ── RAG agent ─────────────────────────────────────────────────────────────
    "rag": {
        "chunk_size":         512,
        "chunk_overlap":      64,
        "max_rss_items":      20,
        "tavily_results":     3,
        "schedule_time":      "02:00",
    },

    # ── Briefing agent ────────────────────────────────────────────────────────
    "briefing": {
        "max_items":          30,
        "schedule_time":      "07:00",
        "brave_queries":      6,
        "seen_item_days":     30,
    },

    # ── Content agent ─────────────────────────────────────────────────────────
    "content": {
        "schedule_day":       "MON",
        "schedule_time":      "06:00",
        "topic_dedup_days":   60,
        "max_article_tokens": 1500,
        "word_count_target":  "800-1200",
        "publication":        "MedTech Meridian",
    },

    # ── Coaching ──────────────────────────────────────────────────────────────
    "coaching": {
        "programs": {
            "career_prep":    {"name": "Career Preparation",      "price": "$699",   "duration": "1 month"},
            "early_career":   {"name": "Early Career QA/RA",       "price": "$1,499", "duration": "3 months"},
            "mid_career":     {"name": "Mid-Career Acceleration",  "price": "$1,899", "duration": "3 months"},
            "transition":     {"name": "Career Transition",        "price": "$2,299", "duration": "4 months"},
        },
        "alacarte": {
            "resume":         "$199",
            "linkedin":       "$199",
            "interview":      "$199",
            "qms_session":    "$199",
            "inperson":       "$199",
            "resume_linkedin_bundle": "$349",
        },
    },

    # ── Document generation ───────────────────────────────────────────────────
    "documents": {
        "company_name":   "Latitude MedTech LLC",
        "tagline":        "Navigating compliance. Accelerating innovation.",
        "location":       "San Diego, CA",
        "website":        "latitudemedtech.com",
        "email":          "hello@latitudemedtech.com",
        "font":           "Calibri",
        "font_size_body": 10.5,
        "font_size_h1":   18,
        "font_size_h2":   14,
        "colors": {
            "black":  "1A1A1A",
            "slate":  "2C3E50",
            "blue":   "5B7FA6",
            "teal":   "4A7C6F",
            "warm":   "C8956C",
            "muted":  "8A8680",
        },
        "disclaimer": (
            "DISCLAIMER: This document is produced by Latitude MedTech LLC for educational "
            "and planning purposes only. Nothing herein constitutes formal regulatory, legal, "
            "or compliance advice. Always defer to official regulations and guidance from the "
            "FDA, ISO, EU Commission, and applicable regulatory bodies."
        ),
        "footer_text": (
            "Latitude MedTech LLC  ·  San Diego, CA  ·  latitudemedtech.com  ·  "
            "Educational purposes only — not regulatory advice"
        ),
    },

    # ── Agent prompts ─────────────────────────────────────────────────────────
    "prompts": {
        "voice_assistant": (
            "You are Athena, the Latitude MedTech voice assistant for the founder of "
            "Latitude MedTech LLC, a San Diego-based medical device regulatory coaching "
            "and consulting company.\n\n"
            "You assist with:\n"
            "- Career coaching for early-career QA/RA professionals\n"
            "- Medical device regulatory knowledge (FDA, EU MDR, ISO 13485, MDSAP)\n"
            "- MedTech Meridian Substack content strategy\n"
            "- Business development and strategic planning\n\n"
            "VOICE RESPONSE RULES:\n"
            "- Natural spoken English only. No markdown or bullets.\n"
            "- Under 80 words unless asked for detail.\n"
            "- Complete sentences. No filler phrases.\n\n"
            "DISCLAIMER: Regulatory content is educational only. Not licensed regulatory advice."
        ),
        "content_agent": (
            "You are writing for MedTech Meridian, a Substack publication by the founder "
            "of Latitude MedTech LLC.\n\n"
            "Audience: early-to-mid career QA/RA professionals (0-7 years experience).\n\n"
            "Voice: conversational but authoritative. Practical and actionable. "
            "First person singular. No corporate speak.\n\n"
            "Structure: hook → core insight → practical takeaway → closing thought.\n\n"
            "Length: 600-900 words.\n\n"
            "IMPORTANT: Educational content only. Not regulatory advice. "
            "Add a brief disclaimer at the end."
        ),
        "coaching_brief": (
            "You are preparing a discovery call brief for the founder of Latitude MedTech LLC. "
            "Generate a concise, practical brief covering: what we know, likely profile, "
            "recommended program match, discovery call objectives, suggested opening questions, "
            "watch-outs, and pricing talking points.\n\n"
            "Keep it tight. Under 2 minutes to read. Like a smart colleague prepping you."
        ),
        "iso_coach": (
            "You are a medical device QMS expert writing coaching content for Latitude MedTech LLC. "
            "Audience: early-career QA/RA professionals (0-3 years) learning ISO 13485:2016.\n\n"
            "Rules: plain English, practical examples, honest about complexity, "
            "conversational but authoritative.\n\n"
            "IMPORTANT: Educational content only. Not regulatory advice."
        ),
        "briefing_agent": (
            "You are preparing a daily intelligence briefing for the founder of "
            "Latitude MedTech LLC — a QA/RA professional and MedTech coach in San Diego.\n\n"
            "Write a clean, scannable briefing with sections: Breaking, Need to Know, "
            "Industry Pulse, QA/RA Learning, SoCal Watch, Worth Reading Later.\n\n"
            "Rules: every item needs a URL, skip empty sections, no filler, under 450 words."
        ),
    },
}


class SettingsManager:
    def __init__(self):
        self._path    = SETTINGS_PATH
        self._data    = {}
        self._mtime   = 0
        self._load()

    def _load(self):
        """Load settings from file, creating with defaults if missing."""
        if not self._path.exists():
            self._data  = DEFAULTS.copy()
            self._save()
        else:
            try:
                mtime = self._path.stat().st_mtime
                if mtime != self._mtime:
                    raw         = json.loads(self._path.read_text(encoding='utf-8'))
                    self._data  = self._merge(DEFAULTS, raw)
                    self._mtime = mtime
            except Exception:
                self._data = DEFAULTS.copy()

    def _merge(self, base: dict, override: dict) -> dict:
        """Deep merge override into base, preserving base keys not in override."""
        result = base.copy()
        for k, v in override.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = self._merge(result[k], v)
            else:
                result[k] = v
        return result

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data['meta']['updated_at'] = datetime.now().isoformat()
        self._path.write_text(json.dumps(self._data, indent=2), encoding='utf-8')

    def get(self, key_path: str, default=None):
        """Get a setting by dot-notation path. e.g. 'rag.chunk_size'"""
        self._load()  # Auto-reload if file changed
        keys  = key_path.split('.')
        value = self._data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key_path: str, value):
        """Set a setting by dot-notation path and save."""
        self._load()
        keys = key_path.split('.')
        d    = self._data
        for k in keys[:-1]:
            if k not in d or not isinstance(d[k], dict):
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value
        self._save()
        self._mtime = self._path.stat().st_mtime

    def get_prompt(self, agent_name: str) -> str:
        return self.get(f"prompts.{agent_name}", "")

    def set_prompt(self, agent_name: str, prompt: str):
        self.set(f"prompts.{agent_name}", prompt)

    def get_all(self) -> dict:
        self._load()
        return self._data.copy()

    def reset_to_defaults(self):
        self._data = DEFAULTS.copy()
        self._save()

    def export_json(self) -> str:
        self._load()
        return json.dumps(self._data, indent=2)


# Singleton instance — all agents import this
settings = SettingsManager()
