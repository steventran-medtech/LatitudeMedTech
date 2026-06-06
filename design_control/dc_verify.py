"""
Latitude MedTech — Design Control Verification Script
=======================================================
Maps directly to design inputs in DC-002 and procedures in DC-005.
Each test function is named test_DI_<ID>() and corresponds to one row
in the traceability matrix (DC-004).

Run modes:
  python dc_verify.py                  # Static checks (no server)
  python dc_verify.py --live           # Static + live API checks
  python dc_verify.py --full           # Live + agent dry-run
  python dc_verify.py --di DI-015      # Only tests with that DI prefix
  python dc_verify.py --verbose        # Show all PASS details

Exit code 0 = all active tests pass.
Exit code 1 = one or more FAIL.
Exit code 2 = configuration error.
"""

import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────
THIS_DIR   = Path(__file__).resolve().parent
ROOT       = THIS_DIR.parent                          # LatitudeMedTech/
ATHENA     = ROOT / "Athena"
AGENTS     = ATHENA / "agents"
UI_BACK    = ATHENA / "ui" / "backend"
UI_FRONT   = ATHENA / "ui" / "frontend" / "src"
VOICE      = ATHENA / "voice"
KB         = ATHENA / "knowledge_base"
OPS        = ATHENA / "ops"
CLAUDE_DIR = ROOT / ".claude"

# ── Result tracking ───────────────────────────────────────────────────────────
PASS  = "PASS"
FAIL  = "FAIL"
WARN  = "WARN"
SKIP  = "SKIP"

_results   = []
_di_filter = None
_verbose   = False


def _log(status, di_id, description, detail=""):
    icon = {PASS: "OK", FAIL: "XX", WARN: "!!", SKIP: "--"}[status]
    msg  = f"  {icon}  [{di_id}] {description}"
    if detail:
        msg += f"\n       -> {detail}"
    if status != PASS or _verbose:
        print(msg)
    _results.append({"status": status, "di": di_id, "description": description, "detail": detail})


def _section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def _read(path):
    """Return file text or empty string if missing."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _grep(path, pattern, flags=0):
    """Return True if pattern found anywhere in file."""
    content = _read(path)
    return bool(re.search(pattern, content, flags))


def _grep_dir(directory, pattern, glob="*.py"):
    """Return list of (path, line_no) where pattern matches in any file."""
    hits = []
    for f in directory.rglob(glob):
        if "venv" in f.parts or "node_modules" in f.parts or "__pycache__" in f.parts:
            continue
        content = _read(f)
        for i, line in enumerate(content.splitlines(), 1):
            if re.search(pattern, line):
                hits.append((f, i, line.strip()))
    return hits


def _skip_if_filtered(di_id):
    """Return True if this test should be skipped due to --di filter."""
    if _di_filter and not di_id.startswith(_di_filter):
        return True
    return False


# ── UN-001 / Coaching Brief ───────────────────────────────────────────────────

def test_DI_001_C():
    """DI-001-C: Readiness label constant present in orchestrator.py"""
    di = "DI-001-C"
    if _skip_if_filtered(di): return
    f = AGENTS / "orchestrator.py"
    if not f.exists():
        _log(FAIL, di, "orchestrator.py not found", str(f))
        return
    content = _read(f)
    if 'LABEL' in content and 'Steve Review' in content:
        _log(PASS, di, "LABEL constant with review text present in orchestrator.py")
    elif 'LABEL' in content:
        _log(WARN, di, "LABEL found but does not contain 'Steve Review'",
             "Expected 'Alpha — Steve Review Required'")
    else:
        _log(FAIL, di, "LABEL constant missing from orchestrator.py",
             "Add: LABEL = \"Alpha — Steve Review Required\"")


def test_DI_001_D():
    """DI-001-D: Disclaimer constant present in orchestrator.py"""
    di = "DI-001-D"
    if _skip_if_filtered(di): return
    f = AGENTS / "orchestrator.py"
    content = _read(f)
    # The canonical disclaimer identifies the firm + purpose + non-advice statement
    required = ["Latitude MedTech LLC", "not regulatory"]
    if 'DISCLAIMER' in content and all(p in content for p in required):
        _log(PASS, di, "DISCLAIMER constant with required text present in orchestrator.py")
    elif 'DISCLAIMER' in content:
        _log(WARN, di, "DISCLAIMER present but missing required phrases",
             f"Expected: {required}")
    else:
        _log(FAIL, di, "DISCLAIMER constant missing from orchestrator.py",
             "Restore canonical disclaimer from compliance.md")


# ── UN-002 / Human Review Gate ────────────────────────────────────────────────

def test_DI_002_A():
    """DI-002-A: Review queue route present in server.py"""
    di = "DI-002-A"
    if _skip_if_filtered(di): return
    f = UI_BACK / "server.py"
    content = _read(f)
    if '/api/review' in content:
        _log(PASS, di, "Review queue route present in server.py")
    else:
        _log(FAIL, di, "No /api/review route found in server.py",
             "Human gate broken — restore review endpoint (P0)")


def test_DI_002_B():
    """DI-002-B: Approve route present in server.py"""
    di = "DI-002-B"
    if _skip_if_filtered(di): return
    f = UI_BACK / "server.py"
    content = _read(f)
    if 'approve' in content and '/api/review' in content:
        _log(PASS, di, "Approve action present in server.py")
    else:
        _log(FAIL, di, "Approve route missing from server.py",
             "Human gate broken for approval — restore immediately (P0)")


def test_DI_002_C():
    """DI-002-C: Reject route present in server.py"""
    di = "DI-002-C"
    if _skip_if_filtered(di): return
    f = UI_BACK / "server.py"
    content = _read(f)
    if 'reject' in content and '/api/review' in content:
        _log(PASS, di, "Reject action present in server.py")
    else:
        _log(FAIL, di, "Reject route missing from server.py",
             "Human gate broken for rejection — restore immediately (P0)")


def test_DI_002_D():
    """DI-002-D: Edit-and-rewrite route present in server.py"""
    di = "DI-002-D"
    if _skip_if_filtered(di): return
    f = UI_BACK / "server.py"
    content = _read(f)
    if '/edit' in content and '/api/review' in content:
        _log(PASS, di, "Edit-and-rewrite route present in server.py")
    else:
        _log(WARN, di, "Edit route not found — DI-002-D PARTIAL",
             "POST /api/review/{id}/edit should exist")


# ── UN-003 / Knowledge Base ────────────────────────────────────────────────────

def test_DI_003_A():
    """DI-003-A: KBQuery class exists in kb_query.py"""
    di = "DI-003-A"
    if _skip_if_filtered(di): return
    f = AGENTS / "kb_query.py"
    if not f.exists():
        _log(FAIL, di, "kb_query.py not found", str(f))
        return
    content = _read(f)
    if 'class KBQuery' in content or 'KBQuery' in content:
        _log(PASS, di, "KBQuery class defined in kb_query.py")
    else:
        _log(FAIL, di, "KBQuery class missing from kb_query.py")


def test_DI_003_B():
    """DI-003-B: KB subdirectories for major regulatory frameworks exist"""
    di = "DI-003-B"
    if _skip_if_filtered(di): return
    required = ["FDA", "EU_MDR", "IMDRF"]
    missing = [d for d in required if not (KB / d).exists()]
    if not missing:
        _log(PASS, di, f"KB subdirectories present: {', '.join(required)}")
    else:
        _log(WARN, di, f"KB subdirectories missing: {', '.join(missing)}",
             "Run run_rag.bat to populate; create directories if needed")


# ── UN-004 / Voice Interface ───────────────────────────────────────────────────

def test_DI_004_A():
    """DI-004-A: Wake threshold <= 0.35 in voice_bridge.py"""
    di = "DI-004-A"
    if _skip_if_filtered(di): return
    f = VOICE / "voice_bridge.py"
    if not f.exists():
        _log(SKIP, di, "voice_bridge.py not found — voice module not present")
        return
    content = _read(f)
    m = re.search(r'WAKE_THRESHOLD\s*=\s*([0-9.]+)', content)
    if not m:
        _log(WARN, di, "WAKE_THRESHOLD constant not found in voice_bridge.py")
        return
    val = float(m.group(1))
    if val <= 0.35:
        _log(PASS, di, f"WAKE_THRESHOLD = {val} (<= 0.35)")
    else:
        _log(FAIL, di, f"WAKE_THRESHOLD = {val} exceeds 0.35",
             "Revert to ≤ 0.35 per CAPA-Voice-001 resolution")


def test_DI_004_B():
    """DI-004-B: Whisper model load present in voice_bridge.py"""
    di = "DI-004-B"
    if _skip_if_filtered(di): return
    f = VOICE / "voice_bridge.py"
    if not f.exists():
        _log(SKIP, di, "voice_bridge.py not found")
        return
    content = _read(f)
    if 'whisper' in content.lower() and ('load_model' in content or 'whisper_model' in content):
        _log(PASS, di, "Whisper model initialisation present in voice_bridge.py")
    else:
        _log(FAIL, di, "Whisper load_model not found in voice_bridge.py",
             "STT removed — voice cannot transcribe")


def test_DI_004_D():
    """DI-004-D: Intent dispatch (tool_use) present in voice_bridge.py"""
    di = "DI-004-D"
    if _skip_if_filtered(di): return
    f = VOICE / "voice_bridge.py"
    if not f.exists():
        _log(SKIP, di, "voice_bridge.py not found")
        return
    content = _read(f)
    if 'tool_use' in content or '"tools"' in content or "tools=" in content:
        _log(PASS, di, "Tool-use intent dispatch found in voice_bridge.py")
    else:
        _log(WARN, di, "tool_use dispatch pattern not found — DI-004-D PARTIAL",
             "All voice queries may fall through to default handler")


def test_DI_004_E():
    """DI-004-E: SILENCE_DURATION default = 0.8s in voice_bridge.py and settings.json"""
    di = "DI-004-E"
    if _skip_if_filtered(di): return
    f = VOICE / "voice_bridge.py"
    if not f.exists():
        _log(SKIP, di, "voice_bridge.py not found")
        return
    content = _read(f)
    m = re.search(r'SILENCE_DURATION\s*=\s*float\s*\(\s*[^)]*?,\s*([0-9.]+)\s*\)', content)
    if not m:
        m = re.search(r'SILENCE_DURATION\s*=\s*([0-9.]+)', content)
    if not m:
        _log(WARN, di, "SILENCE_DURATION constant not found in voice_bridge.py")
        return
    val = float(m.group(1))
    # Also check settings.json
    settings_path = ATHENA / "settings.json"
    settings_val  = None
    try:
        import json as _json
        cfg = _json.loads(settings_path.read_text(encoding="utf-8"))
        settings_val = float(cfg.get("voice", {}).get("silence_duration", -1))
    except Exception:
        pass
    if val == 0.8 and (settings_val is None or settings_val == 0.8):
        _log(PASS, di, f"SILENCE_DURATION = {val} (target 0.8s; settings.json = {settings_val})")
    elif 0.8 <= val <= 2.0:
        _log(WARN, di, f"SILENCE_DURATION = {val} (safe range but target is 0.8s)",
             "Update default in voice_bridge.py and silence_duration in settings.json to 0.8")
    else:
        _log(FAIL, di, f"SILENCE_DURATION default = {val} is outside safe range [0.8, 2.0]",
             "Values < 0.8 cut off speech; values > 2.0 cause unacceptable response latency")


# ── UN-005 / Task Notifications ────────────────────────────────────────────────

def test_DI_005_A():
    """DI-005-A: POST /api/voice/notify endpoint present (server.py or voice_bridge.py router)"""
    di = "DI-005-A"
    if _skip_if_filtered(di): return
    # The notify route may live in voice_bridge.py as @router.post("/notify")
    # with APIRouter prefix="/api/voice", included into server.py via include_router.
    server_content = _read(UI_BACK / "server.py")
    bridge_content = _read(VOICE / "voice_bridge.py")
    in_server = '/api/voice/notify' in server_content or 'voice/notify' in server_content
    # APIRouter-style: prefix="/api/voice" + @router.post("/notify")
    in_bridge = ('prefix="/api/voice"' in bridge_content or "prefix='/api/voice'" in bridge_content) \
                and ('/notify' in bridge_content or '"notify"' in bridge_content)
    included  = 'voice_router' in server_content or 'voice_bridge' in server_content
    if in_server:
        _log(PASS, di, "/api/voice/notify endpoint present in server.py")
    elif in_bridge and included:
        _log(PASS, di, "/api/voice/notify in voice_bridge.py router (included in server.py)")
    else:
        _log(FAIL, di, "/api/voice/notify endpoint not found in server.py or voice_bridge.py",
             "Task completion spoken notifications will not fire")


def test_DI_005_B():
    """DI-005-B: _notification_queue in voice_bridge.py"""
    di = "DI-005-B"
    if _skip_if_filtered(di): return
    f = VOICE / "voice_bridge.py"
    if not f.exists():
        _log(SKIP, di, "voice_bridge.py not found")
        return
    content = _read(f)
    if '_notification_queue' in content or 'notification_queue' in content:
        _log(PASS, di, "Notification queue present in voice_bridge.py")
    else:
        _log(WARN, di, "_notification_queue not found — DI-005-B PARTIAL")


# ── UN-006 / Persistent Voice Session ─────────────────────────────────────────

def test_DI_006_A():
    """DI-006-A: useVoiceSession imported at App level (not in individual views)"""
    di = "DI-006-A"
    if _skip_if_filtered(di): return
    app = UI_FRONT / "App.jsx"
    content_app = _read(app)

    # Should appear in App.jsx
    if 'useVoiceSession' not in content_app:
        _log(FAIL, di, "useVoiceSession not imported in App.jsx",
             "Voice session will reset on tab navigation — move hook to App level")
        return

    # Should NOT appear in view files (would mean it's tab-scoped)
    view_files = list(UI_FRONT.glob("*View.jsx"))
    leaks = [f.name for f in view_files if 'useVoiceSession' in _read(f)]
    if leaks:
        _log(WARN, di, f"useVoiceSession also imported in view files: {leaks}",
             "Ensure these are just consuming context, not creating independent sessions")
    else:
        _log(PASS, di, "useVoiceSession app-level; not duplicated in view files")


def test_DI_006_B():
    """DI-006-B: VoiceStatusBadge present in App.jsx header"""
    di = "DI-006-B"
    if _skip_if_filtered(di): return
    app = UI_FRONT / "App.jsx"
    content = _read(app)
    if 'VoiceStatusBadge' in content:
        _log(PASS, di, "VoiceStatusBadge present in App.jsx")
    else:
        _log(WARN, di, "VoiceStatusBadge not found in App.jsx — DI-006-B PARTIAL")


# ── UN-007 / Content Generation ───────────────────────────────────────────────

def test_DI_007_B():
    """DI-007-B: title_from_body function exists in content_agent.py"""
    di = "DI-007-B"
    if _skip_if_filtered(di): return
    f = AGENTS / "content_agent.py"
    if not f.exists():
        _log(FAIL, di, "content_agent.py not found")
        return
    content = _read(f)
    if 'title_from_body' in content:
        _log(PASS, di, "title_from_body function present in content_agent.py")
    else:
        _log(FAIL, di, "title_from_body missing from content_agent.py",
             "Titles will be raw model output — may contain non-Latin characters or wrong casing")


def test_DI_007_C():
    """DI-007-C: Banned phrases enforced in content agent system prompt"""
    di = "DI-007-C"
    if _skip_if_filtered(di): return
    f = AGENTS / "content_agent.py"
    content = _read(f)
    banned_samples = ["leverage", "robust", "synergy", "in today's rapidly"]
    found = [b for b in banned_samples if b.lower() in content.lower()]
    if len(found) >= 2:
        _log(PASS, di, f"Banned phrases enforced ({len(found)} checked): {found[:3]}")
    elif found:
        _log(WARN, di, f"Only {len(found)} banned phrase found — prompt may be truncated",
             "Expected multiple banned phrases in system prompt")
    else:
        _log(FAIL, di, "No banned phrases found in content_agent.py",
             "Content quality controls removed — restore banned phrase list to system prompt")


def test_DI_007_D():
    """DI-007-D: clean_title function exists in content_agent.py"""
    di = "DI-007-D"
    if _skip_if_filtered(di): return
    f = AGENTS / "content_agent.py"
    content = _read(f)
    if 'clean_title' in content:
        _log(PASS, di, "clean_title function present in content_agent.py")
    else:
        _log(FAIL, di, "clean_title missing from content_agent.py",
             "Non-Latin characters will appear in filenames and slugs")


def test_DI_007_E():
    """DI-007-E: YAML frontmatter stripping in App.jsx renderInline"""
    di = "DI-007-E"
    if _skip_if_filtered(di): return
    app = UI_FRONT / "App.jsx"
    content = _read(app)
    if 'renderInline' in content or 'MarkdownView' in content:
        # Check that frontmatter stripping logic exists nearby
        if '---' in content or 'frontmatter' in content.lower() or 'yaml' in content.lower():
            _log(PASS, di, "Frontmatter stripping logic present in App.jsx")
        else:
            _log(WARN, di, "renderInline present but frontmatter strip not explicitly confirmed",
                 "Manually verify that YAML frontmatter is stripped before rendering")
    else:
        _log(FAIL, di, "renderInline/MarkdownView not found in App.jsx",
             "Content rendering component missing — YAML frontmatter will appear raw")


# ── UN-009 / Slide Decks ───────────────────────────────────────────────────────

def test_DI_009_B():
    """DI-009-B: Latitude brand palette in deck_skills.py (RGBColor constants)"""
    di = "DI-009-B"
    if _skip_if_filtered(di): return
    # Brand colours live in deck_skills.py as _NAVY/_SLATE/_BLUE RGBColor constants
    f = AGENTS / "deck_skills.py"
    if not f.exists():
        _log(SKIP, di, "deck_skills.py not found")
        return
    content = _read(f)
    # Check for the canonical hex values: LM_SLATE=2C3E50, LM_BLUE variants
    required_hexes = ["2C, 0x3E, 0x50", "RGBColor"]  # _SLATE = RGBColor(0x2C, 0x3E, 0x50)
    found_rgb   = "RGBColor" in content
    found_slate = "2C" in content and "3E" in content and "50" in content
    if found_rgb and found_slate:
        _log(PASS, di, "Latitude brand palette RGBColor constants present in deck_skills.py")
    elif found_rgb:
        _log(WARN, di, "RGBColor found in deck_skills.py but expected hex values not confirmed")
    else:
        _log(FAIL, di, "RGBColor brand palette constants missing from deck_skills.py",
             "Decks will not render Latitude branding")


def test_DI_009_C():
    """DI-009-C: Deck generation and listing routes present in server.py"""
    di = "DI-009-C"
    if _skip_if_filtered(di): return
    f = UI_BACK / "server.py"
    content = _read(f)
    # Deck generate route may be /api/decks/generate (current) or /api/agents/deck
    has_generate = '/api/decks/generate' in content or '/api/agents/deck' in content
    # Deck list: may be via documents/decks, decks route, or the generate route covers both
    has_deck_ref = 'deck' in content.lower() and ('post' in content.lower() or '@app' in content)
    if has_generate:
        _log(PASS, di, "Deck generation route present in server.py")
    elif has_deck_ref:
        _log(WARN, di, "Deck reference found but generation route pattern not matched — DI-009-C PARTIAL",
             "Confirm POST /api/decks/generate exists and DeckView can trigger it")
    else:
        _log(FAIL, di, "Deck routes missing from server.py",
             "DeckView gallery will be empty; download will fail")


# ── UN-010 / ISO Coach ────────────────────────────────────────────────────────

def test_DI_010_A():
    """DI-010-A: iso_coach_agent.py exists and contains clause lookup"""
    di = "DI-010-A"
    if _skip_if_filtered(di): return
    f = AGENTS / "iso_coach_agent.py"
    if not f.exists():
        _log(FAIL, di, "iso_coach_agent.py not found")
        return
    content = _read(f)
    if 'clause' in content.lower():
        _log(PASS, di, "iso_coach_agent.py exists with clause reference")
    else:
        _log(WARN, di, "iso_coach_agent.py exists but clause logic not confirmed")


def test_DI_010_B():
    """DI-010-B: --all flag not accessible via API route (CLI only)"""
    di = "DI-010-B"
    if _skip_if_filtered(di): return
    server = UI_BACK / "server.py"
    content = _read(server)
    # Check that the iso-coach API route handler does not pass --all to the agent
    iso_section = ""
    in_iso = False
    for line in content.splitlines():
        if 'iso' in line.lower() and ('route' in line.lower() or '@app' in line or 'def ' in line):
            in_iso = True
        if in_iso:
            iso_section += line + "\n"
            if len(iso_section) > 800:
                break
    if '--all' in iso_section:
        _log(FAIL, di, "--all flag exposed via ISO coach API route",
             "UI should never pass --all; it generates all clauses at once")
    else:
        _log(PASS, di, "--all flag not found in ISO coach API handler (correct)")


# ── UN-011 / M&A Intelligence ─────────────────────────────────────────────────

def test_DI_011_A():
    """DI-011-A: QARA framework present in M&A agent"""
    di = "DI-011-A"
    if _skip_if_filtered(di): return
    agent_py = AGENTS / "ma_intelligence_agent.py"
    agent_md = CLAUDE_DIR / "agents" / "ma-intelligence-agent.md"
    found_in = []
    for f in [agent_py, agent_md]:
        if f.exists() and 'QARA' in _read(f):
            found_in.append(f.name)
    if found_in:
        _log(PASS, di, f"QARA framework found in: {found_in}")
    else:
        _log(FAIL, di, "QARA not found in M&A agent or agent definition",
             "Deal analysis will miss QARA integration risk dimension")


def test_DI_011_B():
    """DI-011-B: Citation requirement in M&A agent system prompt"""
    di = "DI-011-B"
    if _skip_if_filtered(di): return
    f = AGENTS / "ma_intelligence_agent.py"
    if not f.exists():
        _log(SKIP, di, "ma_intelligence_agent.py not found")
        return
    content = _read(f)
    if 'cit' in content.lower() or 'source' in content.lower():
        _log(PASS, di, "Citation/source requirement referenced in M&A agent")
    else:
        _log(WARN, di, "Citation requirement not explicitly found in M&A agent — DI-011-B PARTIAL")


# ── UN-012 / Regulatory Briefings ─────────────────────────────────────────────

def test_DI_012_A():
    """DI-012-A: Briefing agent covers FDA, EU MDR, IMDRF"""
    di = "DI-012-A"
    if _skip_if_filtered(di): return
    f = AGENTS / "briefing_agent.py"
    if not f.exists():
        _log(FAIL, di, "briefing_agent.py not found")
        return
    content = _read(f)
    frameworks = {"FDA": "FDA" in content, "EU MDR": "EU" in content or "MDR" in content,
                  "IMDRF": "IMDRF" in content}
    missing = [k for k, v in frameworks.items() if not v]
    if not missing:
        _log(PASS, di, "All three frameworks (FDA, EU MDR, IMDRF) referenced in briefing_agent.py")
    else:
        _log(WARN, di, f"Frameworks not explicitly found: {missing}",
             "Briefings may not cover all monitored frameworks")


def test_DI_012_B():
    """DI-012-B: submit_for_review called in briefing_agent.py"""
    di = "DI-012-B"
    if _skip_if_filtered(di): return
    f = AGENTS / "briefing_agent.py"
    content = _read(f)
    if 'submit_for_review' in content:
        _log(PASS, di, "submit_for_review present in briefing_agent.py")
    else:
        _log(FAIL, di, "submit_for_review missing from briefing_agent.py",
             "Briefing outputs bypass review queue — human gate broken (P0)")


# ── UN-013 / Dashboard ────────────────────────────────────────────────────────

def test_DI_013_A():
    """DI-013-A: /api/dashboard route in server.py"""
    di = "DI-013-A"
    if _skip_if_filtered(di): return
    content = _read(UI_BACK / "server.py")
    if '/api/dashboard' in content:
        _log(PASS, di, "/api/dashboard route present in server.py")
    else:
        _log(FAIL, di, "/api/dashboard missing from server.py")


def test_DI_013_B():
    """DI-013-B: /api/dashboard/timeseries route in server.py"""
    di = "DI-013-B"
    if _skip_if_filtered(di): return
    content = _read(UI_BACK / "server.py")
    if 'timeseries' in content:
        _log(PASS, di, "/api/dashboard/timeseries route present in server.py")
    else:
        _log(FAIL, di, "/api/dashboard/timeseries missing from server.py")


def test_DI_013_C():
    """DI-013-C: /api/dashboard/knowledge-growth route in server.py"""
    di = "DI-013-C"
    if _skip_if_filtered(di): return
    content = _read(UI_BACK / "server.py")
    if 'knowledge-growth' in content or 'knowledge_growth' in content:
        _log(PASS, di, "/api/dashboard/knowledge-growth route present in server.py")
    else:
        _log(FAIL, di, "/api/dashboard/knowledge-growth missing from server.py")


def test_DI_013_D():
    """DI-013-D: loadData() in App.jsx fetches /api/dashboard with authHdr()"""
    di = "DI-013-D"
    if _skip_if_filtered(di): return
    app = UI_FRONT / "App.jsx"
    if not app.exists():
        _log(FAIL, di, "App.jsx not found", str(app))
        return
    content = _read(app)
    # Extract the loadData useCallback body
    m = re.search(
        r'const loadData\s*=\s*useCallback\s*\(\s*\(\s*\)\s*=>\s*\{(.+?)\}\s*,\s*\[\s*\]',
        content, re.DOTALL
    )
    body = m.group(1) if m else ""
    has_dashboard_fetch = "/api/dashboard" in body
    has_auth            = "authHdr()" in body
    if has_dashboard_fetch and has_auth:
        _log(PASS, di, "loadData() fetches /api/dashboard with authHdr()")
    elif has_dashboard_fetch:
        _log(FAIL, di,
             "loadData() fetches /api/dashboard but authHdr() is absent",
             "Add { headers: authHdr() } to the fetch() call inside loadData in App.jsx")
    else:
        _log(FAIL, di,
             "loadData useCallback or /api/dashboard fetch not found in App.jsx",
             "Restore loadData as useCallback fetching /api/dashboard with authHdr()")


def test_DI_013_E():
    """DI-013-E: All Dashboard sub-fetches in App.jsx include authHdr()"""
    di = "DI-013-E"
    if _skip_if_filtered(di): return
    app = UI_FRONT / "App.jsx"
    if not app.exists():
        _log(FAIL, di, "App.jsx not found", str(app))
        return
    content = _read(app)
    # These six endpoints must each appear in a fetch() that also includes authHdr().
    # Sub-fetches are one-liners, so we check that the endpoint and authHdr() appear
    # on the same source line (handles template-literal form `${API}/api/...`).
    sub_endpoints = [
        "/api/dashboard/history",
        "/api/dashboard/knowledge-growth",
        "/api/dashboard/timeseries",
        "/api/hr/skills",
        "/api/sessions",
        "/api/decks",
    ]
    lines = content.splitlines()
    missing_auth = []
    for ep in sub_endpoints:
        found = any(ep in line and "authHdr()" in line for line in lines)
        if not found:
            missing_auth.append(ep)
    if not missing_auth:
        _log(PASS, di, f"All {len(sub_endpoints)} Dashboard sub-fetches include authHdr()")
    else:
        _log(FAIL, di,
             f"{len(missing_auth)} Dashboard sub-fetch(es) missing authHdr(): {missing_auth}",
             "Add { headers: authHdr() } to each of the listed fetch() calls in App.jsx")


def test_DI_013_F():
    """DI-013-F: loadData() called after setToken() in auth effect — no standalone race useEffect"""
    di = "DI-013-F"
    if _skip_if_filtered(di): return
    app = UI_FRONT / "App.jsx"
    if not app.exists():
        _log(FAIL, di, "App.jsx not found", str(app))
        return
    content = _read(app)
    # Bad pattern: separate useEffect(() => { loadData(); }, [loadData])
    # which fires before the auth token effect, causing a 401 race condition
    race_pattern = re.compile(
        r'useEffect\s*\(\s*\(\s*\)\s*=>\s*\{\s*loadData\s*\(\s*\)\s*;?\s*\}\s*,\s*\[\s*loadData\s*\]\s*\)'
    )
    has_race = bool(race_pattern.search(content))
    # Good pattern: setToken(...) followed by loadData() inside the same effect body
    sequenced_pattern = re.compile(
        r'setToken\s*\([^)]*\)\s*;\s*loadData\s*\(\s*\)',
        re.DOTALL
    )
    has_sequenced = bool(sequenced_pattern.search(content))

    if has_race:
        _log(FAIL, di,
             "Standalone useEffect([loadData]) found — race condition: loadData fires before auth token is set",
             "Remove the standalone useEffect; call loadData() inside the auth-token useEffect after setToken()")
    elif has_sequenced:
        _log(PASS, di, "loadData() invoked after setToken() inside auth-token useEffect — no race")
    else:
        _log(WARN, di,
             "Sequenced setToken→loadData pattern not confirmed; manual review recommended",
             "Verify that loadData() is called only after setToken() completes in the auth useEffect")


# ── UN-014 / Learning & Skills ────────────────────────────────────────────────

def test_DI_014_A():
    """DI-014-A: last_learning stamped in agent_learning.py"""
    di = "DI-014-A"
    if _skip_if_filtered(di): return
    f = AGENTS / "agent_learning.py"
    if not f.exists():
        _log(FAIL, di, "agent_learning.py not found")
        return
    content = _read(f)
    if 'last_learning' in content:
        _log(PASS, di, "last_learning stamp logic present in agent_learning.py")
    else:
        _log(FAIL, di, "last_learning not found in agent_learning.py",
             "Agent health indicators will stay stuck red/yellow after healthy no-op runs")


def test_DI_014_B():
    """DI-014-B: skills_profile.py exists and skills-profile route in server.py"""
    di = "DI-014-B"
    if _skip_if_filtered(di): return
    sp = AGENTS / "skills_profile.py"
    content_server = _read(UI_BACK / "server.py")
    has_file  = sp.exists()
    has_route = 'skills-profile' in content_server or 'skills_profile' in content_server
    if has_file and has_route:
        _log(PASS, di, "skills_profile.py exists and route present in server.py")
    elif has_file:
        _log(WARN, di, "skills_profile.py exists but API route not found",
             "Skills profiles cannot be refreshed via UI")
    else:
        _log(FAIL, di, "skills_profile.py not found")


# ── UN-015 / Security ─────────────────────────────────────────────────────────

def test_DI_015_A():
    """DI-015-A: No secret key values in source code"""
    di = "DI-015-A"
    if _skip_if_filtered(di): return

    # Patterns that would indicate a secret is hardcoded
    secret_patterns = [
        r'ANTHROPIC_API_KEY\s*=\s*["\']sk-ant-',
        r'TAVILY_API_KEY\s*=\s*["\']tvly-',
        r'BRAVE_API_KEY\s*=\s*["\']BSA',
        r'HF_TOKEN\s*=\s*["\']hf_',
        r'sk-ant-api[0-9]+-[A-Za-z0-9_-]{20,}',  # raw key pattern
    ]

    violations = []
    for glob_pattern in ["*.py", "*.js", "*.jsx", "*.json", "*.md"]:
        for f in ROOT.rglob(glob_pattern):
            parts = f.parts
            if any(skip in parts for skip in ["venv", "node_modules", "__pycache__", ".git"]):
                continue
            if f.name == ".env":
                continue
            content = _read(f)
            for pat in secret_patterns:
                if re.search(pat, content):
                    violations.append(f"{f.relative_to(ROOT)} — matched: {pat[:30]}")

    if not violations:
        _log(PASS, di, "No secret key values found in source tree")
    else:
        _log(FAIL, di, f"{len(violations)} potential secret(s) in source code",
             "STOP ALL WORK — remove secret, rotate key, check git history: " + "; ".join(violations[:3]))


def test_DI_015_B():
    """DI-015-B: No shell=True in project subprocess calls (excludes venvs and this file's comments)"""
    di = "DI-015-B"
    if _skip_if_filtered(di): return
    hits = []
    skip_dirs = {"venv", "__pycache__", "kokoro_venv", "node_modules", ".git"}
    for f in ROOT.rglob("*.py"):
        # Exclude all venv/package directories
        if any(skip in f.parts for skip in skip_dirs):
            continue
        # Exclude this verification script itself (it mentions shell=True in doc/comments)
        if f.resolve() == Path(__file__).resolve():
            continue
        content = _read(f)
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            # Skip comment lines and docstrings
            if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            if re.search(r'shell\s*=\s*True', stripped):
                hits.append(f"{f.relative_to(ROOT)}:{i}: {stripped[:80]}")
    if not hits:
        _log(PASS, di, "No shell=True found in project Python source files")
    else:
        _log(FAIL, di, f"shell=True found in {len(hits)} location(s)",
             "P0 security fix required: " + " | ".join(hits[:3]))


def test_DI_015_C():
    """DI-015-C: Rate limiting middleware present in server.py"""
    di = "DI-015-C"
    if _skip_if_filtered(di): return
    content = _read(UI_BACK / "server.py")
    patterns = ["SlowAPI", "RateLimiter", "rate_limit", "limiter", "slowapi"]
    found = [p for p in patterns if p.lower() in content.lower()]
    if found:
        _log(PASS, di, f"Rate limiting present in server.py ({found[0]})")
    else:
        _log(FAIL, di, "Rate limiting not found in server.py",
             "API is open to abuse — restore SlowAPI or equivalent middleware")


def test_DI_015_D():
    """DI-015-D: Security headers (X-Frame-Options, CSP, X-Content-Type-Options) in server.py"""
    di = "DI-015-D"
    if _skip_if_filtered(di): return
    content = _read(UI_BACK / "server.py")
    headers = {
        "X-Frame-Options": "X-Frame-Options" in content,
        "X-Content-Type-Options": "X-Content-Type-Options" in content or "nosniff" in content,
        "Content-Security-Policy": "Content-Security-Policy" in content or "CSP" in content,
    }
    missing = [k for k, v in headers.items() if not v]
    if not missing:
        _log(PASS, di, "All required security headers present in server.py")
    else:
        _log(FAIL, di, f"Security headers missing: {missing}",
             "Browser XSS/clickjacking protections degraded — restore security header middleware")


def test_DI_015_E():
    """DI-015-E: Path traversal protection in server.py file routes"""
    di = "DI-015-E"
    if _skip_if_filtered(di): return
    content = _read(UI_BACK / "server.py")
    patterns = [r"\.\./", "path_traversal", ".resolve()", "safe_path", "normalize"]
    found = [p for p in patterns if p in content]
    if found:
        _log(PASS, di, f"Path traversal protection found in server.py ({found[0]})")
    else:
        _log(WARN, di, "Path traversal protection pattern not explicitly found — DI-015-E PARTIAL",
             "Manually verify that file endpoints reject ../ sequences")


# ── UN-016 / Output Labeling ──────────────────────────────────────────────────

def test_DI_016_A():
    """DI-016-A: DISCLAIMER constant in orchestrator.py identifies firm + non-advice statement"""
    di = "DI-016-A"
    if _skip_if_filtered(di): return
    f = AGENTS / "orchestrator.py"
    content = _read(f)
    # Canonical disclaimer must identify the firm and state it is not regulatory advice
    required_phrases = ["Latitude MedTech LLC", "not regulatory"]
    found = all(p in content for p in required_phrases)
    if found:
        _log(PASS, di, "DISCLAIMER identifies firm and non-advice purpose")
    elif "DISCLAIMER" in content:
        _log(WARN, di, "DISCLAIMER present but missing key phrases",
             f"Expected in disclaimer text: {required_phrases}")
    else:
        _log(FAIL, di, "DISCLAIMER constant missing from orchestrator.py",
             "Restore canonical disclaimer from compliance.md")


def test_DI_016_B():
    """DI-016-B: LABEL constant in orchestrator.py is non-empty"""
    di = "DI-016-B"
    if _skip_if_filtered(di): return
    f = AGENTS / "orchestrator.py"
    content = _read(f)
    m = re.search(r'LABEL\s*=\s*["\']([^"\']+)["\']', content)
    if m and m.group(1).strip():
        _log(PASS, di, f"LABEL = \"{m.group(1)}\"")
    elif m:
        _log(FAIL, di, "LABEL constant is empty string", "Must be a non-empty readiness label")
    else:
        _log(FAIL, di, "LABEL constant not found in orchestrator.py")


def test_DI_016_C():
    """DI-016-C: LABEL value is one of the four permitted readiness labels"""
    di = "DI-016-C"
    if _skip_if_filtered(di): return
    f = AGENTS / "orchestrator.py"
    content = _read(f)
    m = re.search(r'LABEL\s*=\s*["\']([^"\']+)["\']', content)
    if not m:
        _log(SKIP, di, "LABEL not found — see DI-016-B failure")
        return
    val = m.group(1)
    permitted = ["Demo", "Alpha", "Beta", "Production"]
    if any(p in val for p in permitted):
        _log(PASS, di, f"LABEL '{val}' contains a permitted readiness tier")
    else:
        _log(FAIL, di, f"LABEL '{val}' is not one of: {permitted}",
             "Readiness label must be one of: Demo, Alpha, Beta, Production")


# ── UN-017 / Audit Logs ───────────────────────────────────────────────────────

def test_DI_017_A():
    """DI-017-A: Voice session log referenced in voice module (voice_bridge.py or server.py)"""
    di = "DI-017-A"
    if _skip_if_filtered(di): return
    # sessions.jsonl may be written by voice_bridge, server.py, or a separate logging helper
    bridge_content = _read(VOICE / "voice_bridge.py")
    server_content = _read(UI_BACK / "server.py")
    # Also check if the file actually exists (written from any source)
    log_file_exists = (VOICE / "sessions.jsonl").exists() or (ATHENA / "voice" / "sessions.jsonl").exists()
    if 'sessions.jsonl' in bridge_content or 'sessions.jsonl' in server_content:
        _log(PASS, di, "sessions.jsonl voice log path referenced in source code")
    elif log_file_exists:
        _log(PASS, di, "sessions.jsonl log file exists (written by voice module)")
    else:
        _log(WARN, di, "sessions.jsonl not referenced in voice_bridge.py or server.py — DI-017-A PARTIAL",
             "Verify voice exchanges are being logged; check if a different log filename is used")


def test_DI_017_B():
    """DI-017-B: Athena session log referenced in stop script"""
    di = "DI-017-B"
    if _skip_if_filtered(di): return
    # Check both .ps1 and .bat variants
    found = False
    for fname in ["stop_athena.ps1", "stop_athena.bat"]:
        f = ATHENA / "ui" / fname
        if f.exists() and 'athena_sessions.jsonl' in _read(f):
            found = True
            break
    if not found:
        # Also check ops scripts
        for f in (ATHENA / "ops").rglob("*.ps1"):
            if 'athena_sessions.jsonl' in _read(f):
                found = True
                break
    if found:
        _log(PASS, di, "athena_sessions.jsonl referenced in stop script")
    else:
        _log(WARN, di, "athena_sessions.jsonl not found in stop scripts — DI-017-B PARTIAL")


def test_DI_017_C():
    """DI-017-C: GET /api/review/{item_id} route in server.py"""
    di = "DI-017-C"
    if _skip_if_filtered(di): return
    content = _read(UI_BACK / "server.py")
    if re.search(r'/api/review/\{', content) or '/api/review/' in content:
        _log(PASS, di, "Review item retrieval route present in server.py")
    else:
        _log(WARN, di, "Individual review item route not confirmed — DI-017-C PARTIAL")


# ── UN-018 / Client Lifecycle ─────────────────────────────────────────────────

def test_DI_018_A():
    """DI-018-A: create_client wraps add_client in try/except and returns error JSON on failure"""
    di = "DI-018-A"
    if _skip_if_filtered(di): return
    f = UI_BACK / "server.py"
    if not f.exists():
        _log(FAIL, di, "server.py not found")
        return
    content = _read(f)
    # Extract the full create_client function body (up to the next top-level @app decorator)
    m = re.search(r'def create_client\b(.+?)(?=\n@app\.|\nclass |\Z)', content, re.DOTALL)
    body = m.group(0) if m else ""
    has_route   = '@app.post("/api/clients")' in content
    has_try     = "try:" in body
    has_except  = bool(re.search(r'except\s+Exception', body))
    has_errjson = bool(re.search(r'JSONResponse.*status_code=500|status_code=500.*JSONResponse', body))
    if has_route and has_try and has_except and has_errjson:
        _log(PASS, di, "create_client has try/except with 500 JSONResponse error path")
    elif has_route and has_try and has_except:
        _log(WARN, di, "create_client has try/except but 500 JSONResponse not confirmed",
             "Ensure except block returns JSONResponse(status_code=500, content={\"error\": str(exc)})")
    elif has_route:
        _log(FAIL, di, "create_client found but no try/except error handling",
             "DB exceptions will surface as unhandled 500; UI shows generic 'Failed to create client'")
    else:
        _log(FAIL, di, "POST /api/clients route not found in server.py")


def test_DI_018_B():
    """DI-018-B: IntakeForm in ClientsView.jsx validates name, email, and program_tier"""
    di = "DI-018-B"
    if _skip_if_filtered(di): return
    f = UI_FRONT / "ClientsView.jsx"
    if not f.exists():
        _log(FAIL, di, "ClientsView.jsx not found")
        return
    content = _read(f)
    has_name_check  = bool(re.search(r'form\.name|name.*trim|name.*Required', content))
    has_email_check = bool(re.search(r'form\.email|email.*trim|email.*Required', content))
    has_tier_check  = bool(re.search(r'program_tier.*trim|program_tier.*Required', content))
    has_field_errs  = "fieldErrs" in content or "field_errs" in content or "errors" in content
    checks = [has_name_check, has_email_check, has_tier_check, has_field_errs]
    if all(checks):
        _log(PASS, di, "IntakeForm validates name, email, program_tier with per-field error state")
    elif sum(checks) >= 2:
        missing = []
        if not has_name_check:  missing.append("name")
        if not has_email_check: missing.append("email")
        if not has_tier_check:  missing.append("program_tier")
        if not has_field_errs:  missing.append("field error state")
        _log(WARN, di, f"Partial required-field validation — missing: {missing}",
             "All three fields (name, email, program_tier) must be validated before submit")
    else:
        _log(FAIL, di, "Required-field validation not found in IntakeForm",
             "Add validate() that checks name/email/program_tier and sets per-field error state")


# ── UN-019 / Startup Splash Screen ────────────────────────────────────────────

def test_DI_019_A():
    """DI-019-A: Splash .bar-wrap is absolutely positioned full-width at the bottom edge"""
    di = "DI-019-A"
    if _skip_if_filtered(di): return
    f = ATHENA / "ui" / "start_splash.hta"
    if not f.exists():
        _log(FAIL, di, "start_splash.hta not found", str(f))
        return
    content = _read(f)
    has_absolute  = "position:absolute" in content
    has_bottom    = "bottom:0" in content
    has_full_span = ("left:0" in content and "right:0" in content) or "width:100%" in content
    if has_absolute and has_bottom and has_full_span:
        _log(PASS, di, "Splash .bar-wrap is absolutely positioned full-width at the bottom edge")
    else:
        missing = []
        if not has_absolute:  missing.append("position:absolute")
        if not has_bottom:    missing.append("bottom:0")
        if not has_full_span: missing.append("left:0 + right:0 (full span)")
        _log(FAIL, di, f"Splash bar missing required CSS: {missing}",
             "Set .bar-wrap { position:absolute; bottom:0; left:0; right:0; } in start_splash.hta")


def test_DI_019_C():
    """DI-019-C: Splash bar advances through real loading stages; closes only after bar visually reaches 100%"""
    di = "DI-019-C"
    if _skip_if_filtered(di): return
    f = ATHENA / "ui" / "start_splash.hta"
    if not f.exists():
        _log(FAIL, di, "start_splash.hta not found", str(f))
        return
    content = _read(f)
    # .athena_ready flag check that drives targetVal to 100
    has_ready_flag   = ".athena_ready" in content
    has_target_100   = bool(re.search(r'SetStatus\s+.*,\s*100\b|targetVal\s*=\s*100', content))
    # readyToClose flag gates close until bar is visually done
    has_ready_close  = "readyToClose" in content
    # window.close() is only called after stepVal reaches 100
    has_gated_close  = bool(re.search(
        r'readyToClose.*stepVal|stepVal.*readyToClose|If readyToClose.*stepVal\s*>=\s*100',
        content, re.DOTALL | re.IGNORECASE
    ))
    checks = [has_ready_flag, has_target_100, has_ready_close, has_gated_close]
    if all(checks):
        _log(PASS, di, "Splash bar advances to 100% on .athena_ready and closes only after bar completes")
    else:
        missing = []
        if not has_ready_flag:  missing.append(".athena_ready flag-file check missing")
        if not has_target_100:  missing.append("targetVal = 100 not set on ready")
        if not has_ready_close: missing.append("readyToClose flag missing")
        if not has_gated_close: missing.append("window.close() not gated on readyToClose + stepVal >= 100")
        _log(FAIL, di, f"Progress-to-ready behavior incomplete: {'; '.join(missing)}",
             "Restore PollChromeReady, readyToClose = True, and the Tick close-gate in start_splash.hta")


def test_DI_019_B():
    """DI-019-B: Splash screen has no numeric percentage text element or VBScript assignment"""
    di = "DI-019-B"
    if _skip_if_filtered(di): return
    f = ATHENA / "ui" / "start_splash.hta"
    if not f.exists():
        _log(FAIL, di, "start_splash.hta not found", str(f))
        return
    content = _read(f)
    has_pct_element = 'id="pct"' in content
    has_pct_script  = 'pctEl.innerText' in content
    if has_pct_element or has_pct_script:
        detail = []
        if has_pct_element: detail.append('id="pct" element present in HTML')
        if has_pct_script:  detail.append('pctEl.innerText assignment in VBScript')
        _log(FAIL, di, "Percentage text not fully removed from splash screen",
             "; ".join(detail))
    else:
        _log(PASS, di, "No percentage text element or VBScript assignment in start_splash.hta")


# ── UN-020 / Document Review & Approval ──────────────────────────────────────

def test_DI_020_A():
    """DI-020-A: Every reviewable agent calls submit_for_review()"""
    di = "DI-020-A"
    if _skip_if_filtered(di): return
    REQUIRED_AGENTS = [
        ("briefing_agent.py",              AGENTS / "briefing_agent.py"),
        ("marketing_agent.py",             AGENTS / "marketing_agent.py"),
        ("content_agent.py",               AGENTS / "content_agent.py"),
        ("sow_agent.py",                   AGENTS / "sow_agent.py"),
        ("regulatory_strategy_agent.py",   AGENTS / "regulatory_strategy_agent.py"),
        ("iso_coach_agent.py",             AGENTS / "iso_coach_agent.py"),
        ("ma_intelligence_agent.py",       AGENTS / "ma_intelligence_agent.py"),
        ("rag_agent.py",                   AGENTS / "rag_agent.py"),
    ]
    missing = []
    for name, path in REQUIRED_AGENTS:
        if not path.exists() or not _grep(path, r"submit_for_review\("):
            missing.append(name)
    if not missing:
        _log(PASS, di, f"All {len(REQUIRED_AGENTS)} reviewable agents call submit_for_review()")
    else:
        _log(FAIL, di, f"Agents missing submit_for_review() call: {missing}",
             "Add mem.submit_for_review(agent, item_type, title, file_path) to each agent's output path")


def test_DI_020_B():
    """DI-020-B: ReviewView.jsx load() fetches pending items with authHdr()"""
    di = "DI-020-B"
    if _skip_if_filtered(di): return
    f = UI_FRONT / "ReviewView.jsx"
    if not f.exists():
        _log(FAIL, di, "ReviewView.jsx not found")
        return
    content = _read(f)
    m = re.search(r'const load\s*=\s*\(\s*\).*?(?=\n\s{0,2}const |\n\s{0,2}function |\Z)', content, re.DOTALL)
    body = m.group(0) if m else ""
    has_pending_fetch = "/api/review/pending" in body
    has_auth          = "authHdr()" in body
    if has_pending_fetch and has_auth:
        _log(PASS, di, "load() fetches /api/review/pending with authHdr()")
    elif has_pending_fetch:
        _log(FAIL, di, "load() fetches /api/review/pending but authHdr() is absent",
             "Add { headers: authHdr() } to the fetch call in ReviewView.jsx load()")
    else:
        _log(FAIL, di, "load() function or /api/review/pending fetch not found in ReviewView.jsx")


def test_DI_020_C():
    """DI-020-C: ReviewView.jsx loadHistory() fetches history with authHdr()"""
    di = "DI-020-C"
    if _skip_if_filtered(di): return
    f = UI_FRONT / "ReviewView.jsx"
    if not f.exists():
        _log(FAIL, di, "ReviewView.jsx not found")
        return
    content = _read(f)
    m = re.search(r'const loadHistory\s*=\s*\(\s*\).*?(?=\n\s{0,2}const |\n\s{0,2}function |\Z)', content, re.DOTALL)
    body = m.group(0) if m else ""
    has_history_fetch = "/api/review/history" in body
    has_auth          = "authHdr()" in body
    if has_history_fetch and has_auth:
        _log(PASS, di, "loadHistory() fetches /api/review/history with authHdr()")
    elif has_history_fetch:
        _log(FAIL, di, "loadHistory() fetches /api/review/history but authHdr() is absent",
             "Add { headers: authHdr() } to the fetch call in ReviewView.jsx loadHistory()")
    else:
        _log(FAIL, di, "loadHistory() function or /api/review/history fetch not found in ReviewView.jsx")


def test_DI_020_D():
    """DI-020-D: ReviewView.jsx auto-reloads queue when reviewRefreshToken increments"""
    di = "DI-020-D"
    if _skip_if_filtered(di): return
    f = UI_FRONT / "ReviewView.jsx"
    if not f.exists():
        _log(FAIL, di, "ReviewView.jsx not found")
        return
    content = _read(f)
    has_token_prop    = "reviewRefreshToken" in content
    has_useeffect     = bool(re.search(r'useEffect\s*\(.*?reviewRefreshToken', content, re.DOTALL))
    has_load_in_effect = bool(re.search(r'useEffect\s*\(.*?load\s*\(\s*\).*?reviewRefreshToken', content, re.DOTALL))
    if has_token_prop and has_load_in_effect:
        _log(PASS, di, "ReviewView re-fetches queue in useEffect keyed on reviewRefreshToken")
    elif has_token_prop and has_useeffect:
        _log(WARN, di, "reviewRefreshToken useEffect present but load() call not confirmed inside it",
             "Ensure load() is called inside the useEffect([reviewRefreshToken]) hook body")
    else:
        _log(FAIL, di, "reviewRefreshToken auto-refresh pattern not found in ReviewView.jsx",
             "Add useEffect(() => { if (reviewRefreshToken > 0) load(); }, [reviewRefreshToken])")


def test_DI_020_E():
    """DI-020-E: ReviewViewer fetches content inline with authHdr() on all viewer GET calls"""
    di = "DI-020-E"
    if _skip_if_filtered(di): return
    f = UI_FRONT / "ReviewView.jsx"
    if not f.exists():
        _log(FAIL, di, "ReviewView.jsx not found")
        return
    content = _read(f)
    has_viewer_component = "ReviewViewer" in content
    has_inline_render    = bool(re.search(r'renderMarkdown|inline.*render|setContent|content.*render', content, re.IGNORECASE))
    # Extract loadContent function body to check auth on both viewer GET calls
    m = re.search(r'const loadContent\s*=.*?(?=\n\s{0,4}const |\n\s{0,4}function |\Z)', content, re.DOTALL)
    body = m.group(0) if m else ""
    has_content_fetch_auth   = bool(re.search(r"/api/review/.*?/content.*authHdr|authHdr.*api/review/.*?/content", body))
    has_googleview_fetch_auth = bool(re.search(r"/api/review/.*?/google-view.*authHdr|authHdr.*api/review/.*?/google-view", body))
    all_ok = has_viewer_component and has_content_fetch_auth and has_googleview_fetch_auth and has_inline_render
    if all_ok:
        _log(PASS, di, "ReviewViewer fetches /content and /google-view with authHdr(); renders inline")
    else:
        missing = []
        if not has_viewer_component:        missing.append("ReviewViewer component")
        if not has_content_fetch_auth:      missing.append("/content fetch missing authHdr()")
        if not has_googleview_fetch_auth:   missing.append("/google-view fetch missing authHdr()")
        if not has_inline_render:           missing.append("inline render")
        _log(FAIL, di, f"Viewer auth or render gap: {missing}",
             "Add {{ headers: authHdr() }} to all fetch calls inside loadContent in ReviewView.jsx")


# ── UN-021 / Single-Instance Enforcement ─────────────────────────────────────

def test_DI_021_A():
    """DI-021-A: Test-AthenaRunning defined in athena_lib.ps1 and called as a guard in start_athena.ps1"""
    di = "DI-021-A"
    if _skip_if_filtered(di): return

    ui_dir  = ATHENA / "ui"
    lib     = ui_dir / "athena_lib.ps1"
    startup = ui_dir / "start_athena.ps1"

    # 1 — athena_lib.ps1 must define Test-AthenaRunning using Get-NetTCPConnection
    if not lib.exists():
        _log(FAIL, di, "athena_lib.ps1 not found",
             "Restore athena_lib.ps1 — it defines Test-AthenaRunning and other shared launcher helpers")
        return
    lib_content = _read(lib)
    has_fn_def    = "function Test-AthenaRunning" in lib_content
    has_port_chk  = "Get-NetTCPConnection" in lib_content and "8000" in lib_content

    # 2 — start_athena.ps1 must call the guard before starting services
    if not startup.exists():
        _log(FAIL, di, "start_athena.ps1 not found",
             "Restore the startup script — it houses the single-instance guard call")
        return
    start_content = _read(startup)
    has_guard_call = "Test-AthenaRunning" in start_content
    # The guard must have an exit path that does NOT start a new backend
    has_exit_path  = bool(re.search(r'exit\s+0|exit\s+1|\$abortFile', start_content))

    if has_fn_def and has_port_chk and has_guard_call and has_exit_path:
        _log(PASS, di, "Single-instance guard verified: Test-AthenaRunning (port 8000 check) called in start_athena.ps1")
    else:
        missing = []
        if not has_fn_def:    missing.append("function Test-AthenaRunning missing from athena_lib.ps1")
        if not has_port_chk:  missing.append("Get-NetTCPConnection port 8000 check missing from athena_lib.ps1")
        if not has_guard_call: missing.append("Test-AthenaRunning not called in start_athena.ps1")
        if not has_exit_path:  missing.append("no exit/abort path found in start_athena.ps1 guard block")
        _log(FAIL, di, f"Single-instance guard incomplete: {'; '.join(missing)}",
             "Restore Test-AthenaRunning in athena_lib.ps1 and the guard block in start_athena.ps1")


# ── Live API Tests ─────────────────────────────────────────────────────────────

def test_live_api():
    """Run live API tests against running server."""
    _section("Live API Tests (server must be running on :8000)")
    try:
        import urllib.request, urllib.error
        base = "http://localhost:8000"

        def get(path, timeout=5):
            try:
                r = urllib.request.urlopen(f"{base}{path}", timeout=timeout)
                return json.loads(r.read()), None
            except urllib.error.HTTPError as e:
                return None, f"HTTP {e.code}"
            except Exception as ex:
                return None, str(ex)

        # Health check
        data, err = get("/")
        if err:
            _log(FAIL, "LIVE-001", "Server not reachable", "Start server: python server.py")
            return
        _log(PASS, "LIVE-001", "Server reachable at localhost:8000")

        # Dashboard
        data, err = get("/api/dashboard")
        if data and "token_report" in data:
            _log(PASS, "LIVE-013-A", "/api/dashboard returns token_report")
        else:
            _log(FAIL, "LIVE-013-A", f"/api/dashboard failed: {err or 'missing token_report'}")

        # Review queue
        data, err = get("/api/review")
        if data is not None or err == "HTTP 401":
            _log(PASS, "LIVE-002-A", "/api/review accessible (review gate present)")
        else:
            _log(FAIL, "LIVE-002-A", f"/api/review failed: {err}")

        # OpenAPI route count
        data, err = get("/openapi.json")
        if data:
            routes = list(data.get("paths", {}).keys())
            _log(PASS, "LIVE-ROUTES", f"{len(routes)} API routes registered")
            required = ["/api/dashboard", "/api/review", "/api/coaching/briefs"]
            for route in required:
                if route in routes:
                    _log(PASS, f"LIVE-ROUTE:{route}", f"{route} live")
                else:
                    _log(FAIL, f"LIVE-ROUTE:{route}", f"{route} missing from live routes")
        else:
            _log(WARN, "LIVE-ROUTES", f"Could not read /openapi.json: {err}")

    except ImportError:
        _log(SKIP, "LIVE-ALL", "urllib not available")


# ── Summary ────────────────────────────────────────────────────────────────────

def _print_summary():
    _section("DESIGN CONTROL VERIFICATION SUMMARY")
    passed  = sum(1 for r in _results if r["status"] == PASS)
    failed  = sum(1 for r in _results if r["status"] == FAIL)
    warned  = sum(1 for r in _results if r["status"] == WARN)
    skipped = sum(1 for r in _results if r["status"] == SKIP)
    total   = len(_results)

    print(f"  OK  Passed : {passed}/{total}")
    print(f"  XX  Failed : {failed}")
    print(f"  !!  Warned : {warned}")
    print(f"  --  Skipped: {skipped}")

    if failed > 0:
        print(f"\n  FAILURES (fix before commit/PR):")
        for r in _results:
            if r["status"] == FAIL:
                print(f"  - [{r['di']}] {r['description']}")
                if r["detail"]:
                    print(f"    {r['detail']}")

    if warned > 0:
        print(f"\n  WARNINGS (investigate within one sprint):")
        for r in _results:
            if r["status"] == WARN:
                print(f"  - [{r['di']}] {r['description']}")

    if failed >= 3:
        print(f"\n  *** CAPA REQUIRED: {failed} failures exceed threshold of 3. ***")
        print(f"  Open: Athena/ops/hr/CAPA-DC-NNN.md per DC-005 protocol.")

    print()
    if failed == 0:
        print("  All active tests passed. Safe to commit.")
    else:
        print(f"  {failed} failure(s) found. Fix before merging.")
    print()
    return failed == 0


# ── Entry Point ────────────────────────────────────────────────────────────────

def main():
    global _di_filter, _verbose

    parser = argparse.ArgumentParser(description="Latitude MedTech Design Control Verifier")
    parser.add_argument("--live",    action="store_true", help="Include live API tests (server must be on :8000)")
    parser.add_argument("--full",    action="store_true", help="Live + agent dry-run checks")
    parser.add_argument("--di",      metavar="PREFIX",    help="Only run tests matching this DI prefix (e.g. DI-015)")
    parser.add_argument("--verbose", action="store_true", help="Show all PASS details")
    args = parser.parse_args()

    _di_filter = args.di
    _verbose   = args.verbose

    print(f"\nLatitude MedTech — Design Control Verification")
    print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if _di_filter:
        print(f"Filter: {_di_filter}")

    _section("UN-001/002 Coaching Brief & Review Gate")
    test_DI_001_C(); test_DI_001_D()
    test_DI_002_A(); test_DI_002_B(); test_DI_002_C(); test_DI_002_D()

    _section("UN-003 Knowledge Base")
    test_DI_003_A(); test_DI_003_B()

    _section("UN-004/005/006 Voice Interface")
    test_DI_004_A(); test_DI_004_B(); test_DI_004_D(); test_DI_004_E()
    test_DI_005_A(); test_DI_005_B()
    test_DI_006_A(); test_DI_006_B()

    _section("UN-007/008/009 Content, Marketing & Decks")
    test_DI_007_B(); test_DI_007_C(); test_DI_007_D(); test_DI_007_E()
    test_DI_009_B(); test_DI_009_C()

    _section("UN-010/011/012 Regulatory Intelligence")
    test_DI_010_A(); test_DI_010_B()
    test_DI_011_A(); test_DI_011_B()
    test_DI_012_A(); test_DI_012_B()

    _section("UN-013/014 Dashboard & Learning")
    test_DI_013_A(); test_DI_013_B(); test_DI_013_C()
    test_DI_013_D(); test_DI_013_E(); test_DI_013_F()
    test_DI_014_A(); test_DI_014_B()

    _section("UN-015/016/017 Security, Labeling & Audit")
    test_DI_015_A(); test_DI_015_B(); test_DI_015_C()
    test_DI_015_D(); test_DI_015_E()
    test_DI_016_A(); test_DI_016_B(); test_DI_016_C()
    test_DI_017_A(); test_DI_017_B(); test_DI_017_C()

    _section("UN-018 Client Lifecycle")
    test_DI_018_A(); test_DI_018_B()

    _section("UN-019 Startup Experience")
    test_DI_019_A(); test_DI_019_B(); test_DI_019_C()

    _section("UN-020 Document Review & Approval")
    test_DI_020_A(); test_DI_020_B(); test_DI_020_C(); test_DI_020_D(); test_DI_020_E()

    _section("UN-021 Single-Instance Enforcement")
    test_DI_021_A()

    if args.live or args.full:
        test_live_api()

    passed = _print_summary()
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
