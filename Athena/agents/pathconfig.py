"""
Latitude MedTech Athena — Canonical Path Configuration
=======================================================
Single source of truth for every file-system path used by Athena agents,
the voice bridge, and the API server.

Derivation: all paths resolve from this file's location
  agents/pathconfig.py  →  parent  →  agents/
                         →  parent  →  Athena/   ← ATHENA_ROOT

This means paths are correct regardless of username, machine, or checkout
location — no hardcoded user directories, no Path.home() assumptions.
"""

from pathlib import Path

# Code root — one level up from agents/
ATHENA_ROOT   = Path(__file__).resolve().parent.parent

# --- Config + code assets (all inside code root) ------------------------------
ENV_FILE      = ATHENA_ROOT / "voice" / ".env"
AGENTS_DIR    = ATHENA_ROOT / "agents"
VOICE_DIR     = ATHENA_ROOT / "voice"
KB_DIR        = ATHENA_ROOT / "knowledge_base"

# --- Runtime data — canonical location = code root ---------------------------
MEMORY_DIR    = ATHENA_ROOT / "memory"
BRIEFS_DIR    = ATHENA_ROOT / "coaching" / "briefs"
ISO_DIR       = ATHENA_ROOT / "coaching" / "iso13485"
BRIEFINGS_DIR = ATHENA_ROOT / "briefings"
DRAFTS_DIR    = ATHENA_ROOT / "content" / "drafts"
PUBLISHED_DIR = ATHENA_ROOT / "content" / "published"
LOGS_DIR      = ATHENA_ROOT / "logs"
OPS_DIR       = ATHENA_ROOT / "ops"
SETTINGS_PATH = ATHENA_ROOT / "settings.json"

# --- Firm-level context (LatitudeMedTech/ — parent of code root) --------------
FIRM_ROOT  = ATHENA_ROOT.parent
RULES_DIR  = FIRM_ROOT / ".claude" / "agents"
CLAUDE_MD  = FIRM_ROOT / "CLAUDE.md"
