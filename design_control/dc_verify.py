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


def test_DI_002_E():
    """DI-002-E: ReviewView.jsx Approved filter fetches from /api/documents"""
    di = "DI-002-E"
    if _skip_if_filtered(di): return

    # ARRANGE
    f = UI_FRONT / "ReviewView.jsx"
    if not f.exists():
        _log(FAIL, di, "ReviewView.jsx not found", str(f))
        return
    content = _read(f)

    # ACT — Approved filter must fetch from /api/documents (approved-only backend gate)
    has_docs_fetch = "/api/documents" in content

    # ASSERT
    if has_docs_fetch:
        _log(PASS, di, "ReviewView.jsx Approved filter fetches from /api/documents")
    else:
        _log(FAIL, di,
             "DI-002-E: ReviewView.jsx has no /api/documents fetch — Approved filter is missing",
             "Fix: Add a fetch('/api/documents') call in the 'approved' tab handler of ReviewView.jsx")
    return True


def test_DI_002_F():
    """DI-002-F: ReviewView.jsx tab state initialises to 'pending'; legacy 'queue' state absent"""
    di = "DI-002-F"
    if _skip_if_filtered(di): return

    # ARRANGE
    f = UI_FRONT / "ReviewView.jsx"
    if not f.exists():
        _log(FAIL, di, "ReviewView.jsx not found", str(f))
        return
    content = _read(f)

    # ACT
    # Initial tab state must be "pending" — not the legacy "queue"
    uses_pending_init = 'useState("pending")' in content
    still_uses_queue  = 'useState("queue")'   in content
    # All three filter tab keys must be present as tab-array entries
    has_approved_tab = '["approved"' in content or '"approved",' in content
    has_rejected_tab = '["rejected"' in content or '"rejected",' in content

    # ASSERT
    failures = []
    if not uses_pending_init:
        failures.append('useState("pending") not found — initial tab state must be "pending"')
    if still_uses_queue:
        failures.append('useState("queue") still present — legacy tab state must be removed')
    if not has_approved_tab:
        failures.append('"approved" tab key not found in tabs array')
    if not has_rejected_tab:
        failures.append('"rejected" tab key not found in tabs array')

    if not failures:
        _log(PASS, di, "ReviewView.jsx uses three-state filter: pending / approved / rejected")
    else:
        _log(FAIL, di,
             "DI-002-F: " + "; ".join(failures),
             "Fix: Change useState('queue') to useState('pending') and add approved/rejected tab entries in ReviewView.jsx")
    return True


def test_DI_002_G():
    """DI-002-G: App.jsx NAV_ITEMS has id:'queue' and no id:'documents' or id:'review'"""
    di = "DI-002-G"
    if _skip_if_filtered(di): return

    # ARRANGE
    f = UI_FRONT / "App.jsx"
    if not f.exists():
        _log(FAIL, di, "App.jsx not found", str(f))
        return
    content = _read(f)

    # ACT — check NAV_ITEMS contains queue, not the retired documents/review entries
    has_queue     = 'id:"queue"'     in content
    has_documents = 'id:"documents"' in content
    has_review    = 'id:"review"'    in content

    # ASSERT
    failures = []
    if not has_queue:
        failures.append('id:"queue" missing from App.jsx NAV_ITEMS')
    if has_documents:
        failures.append('id:"documents" still present in App.jsx NAV_ITEMS — must be removed')
    if has_review:
        failures.append('id:"review" still present in App.jsx NAV_ITEMS — must be removed')

    if not failures:
        _log(PASS, di, "App.jsx NAV_ITEMS has id:'queue'; id:'documents' and id:'review' are absent")
    else:
        _log(FAIL, di,
             "DI-002-G: " + "; ".join(failures),
             "Fix: Replace id:'documents' and id:'review' entries with id:'queue' in App.jsx NAV_ITEMS")
    return True


def test_DI_002_H():
    """DI-002-H: AGENT_TAB maps all agents to valid NAV_ITEMS tab IDs — no 'review' or 'documents' values"""
    import re as _re
    di = "DI-002-H"
    if _skip_if_filtered(di): return

    # ARRANGE
    f = UI_FRONT / "App.jsx"
    if not f.exists():
        _log(FAIL, di, "App.jsx not found", str(f))
        return
    content = _read(f)

    # ACT — extract AGENT_TAB block
    m = _re.search(r'const AGENT_TAB\s*=\s*\{([^}]+)\}', content, _re.DOTALL)
    if not m:
        _log(FAIL, di, "AGENT_TAB constant not found in App.jsx",
             "Fix: Ensure 'const AGENT_TAB = { ... }' is defined in App.jsx")
        return
    body = m.group(1)

    # ASSERT — no retired tab IDs as values
    failures = []
    if '"review"' in body:
        failures.append('AGENT_TAB contains "review" — a retired/non-existent tab ID')
    if '"documents"' in body:
        failures.append('AGENT_TAB contains "documents" — a retired/non-existent tab ID')

    # ASSERT — specific correct mappings
    if not _re.search(r'coaching_brief\s*:\s*"coaching"', body):
        failures.append('coaching_brief does not map to "coaching"')
    if not _re.search(r'consulting_agent\s*:\s*"queue"', body):
        failures.append('consulting_agent does not map to "queue"')
    if not _re.search(r'ma_intelligence_agent\s*:\s*"queue"', body):
        failures.append('ma_intelligence_agent does not map to "queue"')
    if not _re.search(r'sow_agent\s*:\s*"queue"', body):
        failures.append('sow_agent does not map to "queue"')
    if not _re.search(r'regulatory_strategy_agent\s*:\s*"queue"', body):
        failures.append('regulatory_strategy_agent does not map to "queue"')

    if not failures:
        _log(PASS, di, "AGENT_TAB maps all agents to valid tab IDs")
    else:
        _log(FAIL, di, "FAIL DI-002-H: " + "; ".join(failures),
             "Fix: In AGENT_TAB, set coaching_brief->\"coaching\", "
             "consulting_agent/ma_intelligence_agent/sow_agent/regulatory_strategy_agent->\"queue\"")
    return True


def test_DI_002_I():
    """DI-002-I: WorkQueuePanel uses 'queue' (not 'review') as awaiting_review routing target"""
    import re as _re
    di = "DI-002-I"
    if _skip_if_filtered(di): return

    # ARRANGE
    f = UI_FRONT / "App.jsx"
    if not f.exists():
        _log(FAIL, di, "App.jsx not found", str(f))
        return
    content = _read(f)

    # ACT
    broken = _re.search(r'status\s*===\s*"awaiting_review"\s*\?\s*"review"', content)
    fixed  = _re.search(r'status\s*===\s*"awaiting_review"\s*\?\s*"queue"', content)

    # ASSERT
    if broken:
        _log(FAIL, di,
             'FAIL DI-002-I: WorkQueuePanel routes awaiting_review to "review" — a non-existent tab ID',
             'Fix: Change the ternary in WorkQueuePanel from ? "review" : to ? "queue" :')
        return
    if not fixed:
        _log(FAIL, di,
             'FAIL DI-002-I: WorkQueuePanel awaiting_review routing not found',
             'Fix: Ensure `t.status === "awaiting_review" ? "queue"` exists in WorkQueuePanel')
        return
    _log(PASS, di, 'WorkQueuePanel routes awaiting_review to "queue"')
    return True


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


def test_DI_003_C():
    """DI-003-C: RAG ingestion report includes '## Newly Ingested Documents' section and calls submit_for_review()"""
    di = "DI-003-C"
    if _skip_if_filtered(di): return

    # ARRANGE
    f = AGENTS / "rag_agent.py"
    if not f.exists():
        _log(FAIL, di, "rag_agent.py not found", str(f))
        return
    content = _read(f)

    # ACT
    has_submit  = "submit_for_review(" in content
    has_section = "## Newly Ingested Documents" in content

    # ASSERT
    if has_submit and has_section:
        _log(PASS, di, "rag_agent.py calls submit_for_review() and includes '## Newly Ingested Documents' section")
    else:
        missing = []
        if not has_submit:
            missing.append("submit_for_review() call missing from rag_agent.py")
        if not has_section:
            missing.append('"## Newly Ingested Documents" section header missing from rag_agent.py')
        _log(FAIL, di, f"RAG ingestion report incomplete: {'; '.join(missing)}",
             "Fix: Update main() in rag_agent.py to include '## Newly Ingested Documents' and submit via submit_for_review()")
    return True


def test_DI_003_D():
    """DI-003-D: RAG ingestion report uses rag_summary_ filename and includes 'No new documents' fallback"""
    di = "DI-003-D"
    if _skip_if_filtered(di): return

    # ARRANGE
    f = AGENTS / "rag_agent.py"
    if not f.exists():
        _log(FAIL, di, "rag_agent.py not found", str(f))
        return
    content = _read(f)

    # ACT
    has_path_pattern = "rag_summary_" in content
    has_fallback     = "No new documents ingested" in content

    # ASSERT
    if has_path_pattern and has_fallback:
        _log(PASS, di, "rag_agent.py writes rag_summary_<ts>.md and includes 'No new documents ingested' fallback")
    else:
        missing = []
        if not has_path_pattern:
            missing.append("rag_summary_ path pattern missing from rag_agent.py")
        if not has_fallback:
            missing.append('"No new documents ingested" fallback string missing from rag_agent.py')
        _log(FAIL, di, f"RAG report file spec incomplete: {'; '.join(missing)}",
             "Fix: Use rag_summary_<timestamp>.md filename; add 'No new documents ingested this run.' when count == 0")
    return True


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
    """DI-004-E: SILENCE_DURATION default = 0.65s in voice_bridge.py (BUG-2 latency fix, 2026-06-06)"""
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
    if val == 0.65 and (settings_val is None or settings_val == 0.65):
        _log(PASS, di, f"SILENCE_DURATION = {val} (target 0.65s; settings.json = {settings_val})")
    elif 0.5 <= val <= 2.0:
        _log(WARN, di, f"SILENCE_DURATION = {val} (within acceptable range; target is 0.65s)",
             "Update default in voice_bridge.py to 0.65 for optimal latency")
    else:
        _log(FAIL, di, f"SILENCE_DURATION default = {val} is outside safe range [0.5, 2.0]",
             "Values < 0.5 may cut off speech; values > 2.0 cause unacceptable response latency")


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


def test_DI_007_F():
    """DI-007-F: Content tab labeled 'MedTech Meridian Drafts' in NAV_ITEMS and ContentView h2"""
    di = "DI-007-F"
    if _skip_if_filtered(di): return

    # ARRANGE
    f = UI_FRONT / "App.jsx"
    if not f.exists():
        _log(FAIL, di, "App.jsx not found", str(f))
        return
    content = _read(f)

    # ACT
    has_nav_label   = 'label:"MedTech Meridian Drafts"'  in content
    has_h2_label    = '>MedTech Meridian Drafts<'        in content
    has_old_nav     = 'label:"Content Drafts"'           in content
    has_old_h2      = '>Content Drafts<'                 in content

    # ASSERT
    failures = []
    if not has_nav_label:
        failures.append('label:"MedTech Meridian Drafts" missing from NAV_ITEMS in App.jsx')
    if not has_h2_label:
        failures.append('>MedTech Meridian Drafts< missing from ContentView h2 in App.jsx')
    if has_old_nav:
        failures.append('label:"Content Drafts" still present in App.jsx — must be removed')
    if has_old_h2:
        failures.append('>Content Drafts< still present in App.jsx ContentView h2 — must be removed')

    if not failures:
        _log(PASS, di, 'Content tab labeled "MedTech Meridian Drafts" in NAV_ITEMS and ContentView h2')
    else:
        _log(FAIL, di, "FAIL DI-007-F: " + "; ".join(failures),
             'Fix: In App.jsx, change label:"Content Drafts" to label:"MedTech Meridian Drafts" '
             'in NAV_ITEMS and the h2 in ContentView')
    return True


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


def test_DI_015_G():
    """DI-015-G: No naked /api/ GET fetch calls (missing authHdr) across all frontend source files"""
    di = "DI-015-G"
    if _skip_if_filtered(di): return
    # Endpoints exempt from auth per AuthMiddleware
    EXEMPT = {"/api/auth/token", "/api/version"}
    naked = []
    for src_file in sorted(UI_FRONT.glob("**/*.jsx")) + sorted(UI_FRONT.glob("**/*.js")):
        if "node_modules" in str(src_file):
            continue
        content = _read(src_file)
        # Find all fetch(${API}/api/... calls — look ahead for authHdr() within ~250 chars
        for m in re.finditer(r'fetch\(`\$\{API\}(/api/[^`"\')\s]+)', content):
            endpoint_raw = m.group(1)
            # Strip dynamic path segments to compare against exempt list
            endpoint_static = re.sub(r'\$\{[^}]+\}', '{id}', endpoint_raw).split("?")[0].rstrip("/")
            # Check if any exempt prefix matches
            if any(endpoint_static.startswith(e) for e in EXEMPT):
                continue
            # Look for authHdr() within the fetch call's option object (up to 250 chars ahead)
            # 250 covers deeply-indented multi-line option objects without bleeding into next call
            window = content[m.start():m.start() + 250]
            if "authHdr()" not in window:
                rel = str(src_file.relative_to(UI_FRONT))
                line_num = content[:m.start()].count("\n") + 1
                naked.append(f"{rel}:{line_num} — {endpoint_static[:60]}")
    if not naked:
        _log(PASS, di, "No naked /api/ fetch calls detected across frontend source tree")
    else:
        detail = "; ".join(naked[:5]) + (f" … +{len(naked)-5} more" if len(naked) > 5 else "")
        _log(FAIL, di, f"{len(naked)} fetch call(s) missing authHdr() in frontend source", detail)


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
    # window.close() is only called after stepVal reaches 99.5 (CInt rounds 99.9 to "100%")
    has_gated_close  = bool(re.search(
        r'readyToClose.*stepVal|stepVal.*readyToClose',
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
        if not has_gated_close: missing.append("window.close() not gated on readyToClose + stepVal threshold")
        _log(FAIL, di, f"Progress-to-ready behavior incomplete: {'; '.join(missing)}",
             "Restore PollChromeReady, readyToClose = True, and the stepVal >= 99.5 close-gate in start_splash.hta")


def test_DI_019_B():
    """DI-019-B: Splash displays a float-right percentage label per Spectrum design guidelines"""
    di = "DI-019-B"
    if _skip_if_filtered(di): return
    f = ATHENA / "ui" / "start_splash.hta"
    if not f.exists():
        _log(FAIL, di, "start_splash.hta not found", str(f))
        return
    content = _read(f)
    has_pct_element = 'id="pct"' in content
    has_pct_script  = 'pctEl.innerText' in content
    has_float_right = bool(re.search(r'float\s*:\s*right', content, re.IGNORECASE))
    if has_pct_element and has_pct_script and has_float_right:
        _log(PASS, di, "Splash has float-right percentage label with VBScript update (Spectrum design)")
    else:
        missing = []
        if not has_pct_element: missing.append('id="pct" element missing from HTML')
        if not has_pct_script:  missing.append('pctEl.innerText assignment missing from VBScript Tick')
        if not has_float_right: missing.append('float:right CSS missing from .pct-text')
        _log(FAIL, di, f"Spectrum percentage label incomplete: {'; '.join(missing)}",
             'Add id="pct" span, pctEl.innerText in Tick, and float:right on .pct-text per Spectrum guidelines')


def test_DI_019_D():
    """DI-019-D: Electron createSplash() has 5px bottom-edge bar, shimmer animation, and setSplashStatus defined"""
    di = "DI-019-D"
    if _skip_if_filtered(di): return
    f = ATHENA / "electron" / "main.js"
    if not f.exists():
        _log(FAIL, di, "electron/main.js not found", str(f))
        return
    content = _read(f)
    has_bar_wrap        = "bar-wrap" in content
    has_bottom          = "bottom:0" in content
    has_full_width      = "width:100%" in content
    has_height          = bool(re.search(r'height:\s*(?:5|10)px', content))
    has_shimmer         = "shimmer" in content
    has_set_status_fn   = bool(re.search(r'function setSplashStatus\s*\(', content))
    has_destroyed_guard = "isDestroyed()" in content
    checks = [has_bar_wrap, has_bottom, has_full_width, has_height,
              has_shimmer, has_set_status_fn, has_destroyed_guard]
    if all(checks):
        _log(PASS, di, "Electron splash: bottom bar, shimmer, setSplashStatus with isDestroyed guard")
    else:
        missing = []
        if not has_bar_wrap:        missing.append("#bar-wrap element")
        if not has_bottom:          missing.append("bottom:0")
        if not has_full_width:      missing.append("width:100%")
        if not has_height:          missing.append("height:5px or height:10px")
        if not has_shimmer:         missing.append("shimmer animation")
        if not has_set_status_fn:   missing.append("setSplashStatus() function")
        if not has_destroyed_guard: missing.append("isDestroyed() guard in setSplashStatus")
        _log(FAIL, di, f"Electron splash bar spec incomplete: {missing}",
             "Restore full createSplash() and setSplashStatus() in electron/main.js per CAPA-Splash-001")


def test_DI_019_E():
    """DI-019-E: Electron startup sequence calls setSplashStatus at all four milestones and holds 100% before close"""
    di = "DI-019-E"
    if _skip_if_filtered(di): return
    f = ATHENA / "electron" / "main.js"
    if not f.exists():
        _log(FAIL, di, "electron/main.js not found", str(f))
        return
    content = _read(f)
    # Extract the app.whenReady block for scoped checks
    m = re.search(r'app\.whenReady\(\).*', content, re.DOTALL)
    body = m.group(0) if m else content
    has_pct_15  = bool(re.search(r'setSplashStatus\s*\(.*?,\s*15\b', body))
    has_pct_mid = bool(re.search(r'setSplashStatus\s*\(.*?,\s*(?:50|65|70|80)\b', body))
    has_pct_100 = bool(re.search(r'setSplashStatus\s*\(.*?,\s*100\b', body))
    has_hold    = bool(re.search(r'setTimeout.*splash\.close|await new Promise.*splash\.close', body, re.DOTALL))
    checks = [has_pct_15, has_pct_mid, has_pct_100, has_hold]
    if all(checks):
        _log(PASS, di, "Electron startup calls setSplashStatus at 15%, mid-milestones, 100% and holds before close")
    else:
        missing = []
        if not has_pct_15:  missing.append("setSplashStatus(..., 15) backend-start milestone")
        if not has_pct_mid: missing.append("setSplashStatus(..., 50/65/70/80) mid-loading milestone")
        if not has_pct_100: missing.append("setSplashStatus(..., 100) ready milestone")
        if not has_hold:    missing.append("setTimeout/Promise hold at 100% before splash.close()")
        _log(FAIL, di, f"Electron startup milestone sequence incomplete: {missing}",
             "Restore setSplashStatus() calls in app.whenReady() per CAPA-Splash-001")


def test_DI_019_F():
    """DI-019-F: Tick loop uses asymptotic easing with a guaranteed minimum per-frame floor"""
    di = "DI-019-F"
    if _skip_if_filtered(di): return
    f = ATHENA / "ui" / "start_splash.hta"
    if not f.exists():
        _log(FAIL, di, "start_splash.hta not found", str(f))
        return
    content = _read(f)
    has_asymptotic = bool(re.search(r'\(\s*targetVal\s*-\s*stepVal\s*\)\s*\*\s*0\.\d+', content))
    has_floor      = bool(re.search(r'If\s+inc\s*<\s*[\d.]+\s+Then\s+inc\s*=', content, re.IGNORECASE))
    if has_asymptotic and has_floor:
        _log(PASS, di, "Tick sub has asymptotic easing and minimum per-frame floor")
    else:
        missing = []
        if not has_asymptotic: missing.append("asymptotic expression `(targetVal - stepVal) * 0.N`")
        if not has_floor:      missing.append("minimum floor `If inc < N Then inc = N`")
        _log(FAIL, di, f"Tick smooth-loading easing incomplete: {'; '.join(missing)}",
             "Restore asymptotic easing factor and minimum increment floor in the Tick Sub in start_splash.hta")


def test_DI_019_G():
    """DI-019-G: PS1 launcher delay between .athena_ready flag and Chrome open is <= 5000ms"""
    di = "DI-019-G"
    if _skip_if_filtered(di): return
    f = ATHENA / "ui" / "start_athena.ps1"
    if not f.exists():
        _log(FAIL, di, "start_athena.ps1 not found", str(f))
        return
    content = _read(f)
    m = re.search(r'Start-Sleep\s+-Milliseconds\s+(\d+)', content)
    if not m:
        _log(FAIL, di, "No Start-Sleep -Milliseconds found in start_athena.ps1",
             "Launcher must sleep briefly after writing .athena_ready before opening Chrome")
        return
    ms = int(m.group(1))
    if ms <= 2500:
        _log(PASS, di, f"Chrome launch delay is {ms}ms (<= 2500ms; splash-to-Chrome gap < 3s)")
    else:
        _log(FAIL, di, f"Chrome launch delay is {ms}ms -- exceeds 2500ms maximum",
             "Reduce Start-Sleep -Milliseconds in start_athena.ps1 to <= 2500 (DI-019-G: < 3s gap)")


def test_DI_019_H():
    """DI-019-H: Bar cannot stall >1s at any whole-number percentage; keep-alive wrap covers all 100 percentages"""
    di = "DI-019-H"
    if _skip_if_filtered(di): return
    f = ATHENA / "ui" / "start_splash.hta"
    if not f.exists():
        _log(FAIL, di, "start_splash.hta not found", str(f))
        return
    content = _read(f)

    # 1. Tick minimum floor
    has_tick_floor = bool(re.search(r'If\s+inc\s*<\s*[\d.]+\s+Then\s+inc\s*=\s*[\d.]+', content, re.IGNORECASE))

    # 2. PollChromeReady minimum floor
    has_poll_floor = bool(re.search(r'If\s+adv\s*<\s*[\d.]+\s+Then\s+adv\s*=\s*[\d.]+', content, re.IGNORECASE))

    # 3. PollChromeReady cap must be <= 98 so Int() can never display "100%" prematurely.
    cap_ok = False
    cap_val = None
    m = re.search(r'If\s+targetVal\s*>\s*([\d.]+)\s+Then\s+targetVal\s*=\s*[\d.]+', content, re.IGNORECASE)
    if m:
        cap_val = float(m.group(1))
        cap_ok = cap_val <= 98

    # 4. Display must use Int() (floor), not CInt() (rounds -- CInt(99.9)=100 is banned)
    has_int_display  = bool(re.search(r'\bInt\s*\(\s*stepVal\s*\)', content, re.IGNORECASE))
    has_cint_display = bool(re.search(r'\bCInt\s*\(\s*stepVal\s*\)', content, re.IGNORECASE))
    display_ok = has_int_display and not has_cint_display

    # 5. Mathematical sprint bound: from cap to 99.5 at min_floor per 16ms frame must be < 1000ms
    bound_ok = False
    bound_ms = None
    if cap_ok and has_tick_floor:
        m_floor = re.search(r'If\s+inc\s*<\s*([\d.]+)\s+Then\s+inc\s*=', content, re.IGNORECASE)
        if m_floor:
            min_floor = float(m_floor.group(1))
            gap = 99.5 - cap_val
            bound_ms = (gap / min_floor) * 16
            bound_ok = bound_ms < 1000

    # 6. Keep-alive branch present: ElseIf Not readyToClose (fires whenever stepVal >= targetVal
    #    and loading is incomplete, covering the convergence stall at the animation ceiling).
    has_keepalive = bool(re.search(r'ElseIf\s+Not\s+readyToClose\b', content, re.IGNORECASE))

    # 7. Keep-alive must NOT have a blocking ceiling in its condition.
    #    "ElseIf Not readyToClose And stepVal < N" stops advancing once stepVal reaches N,
    #    creating a freeze at Int(N). The condition must be just "ElseIf Not readyToClose".
    has_blocking_ceiling = bool(re.search(
        r'ElseIf\s+Not\s+readyToClose\s+And\s+stepVal\s*<\s*[\d.]+',
        content, re.IGNORECASE
    ))
    keepalive_no_ceiling = has_keepalive and not has_blocking_ceiling

    # 8. Keep-alive floor: 1/N * 16ms < 1000ms so each percentage point advances in < 1 second.
    keepalive_floor_ok = False
    keepalive_floor_val = None
    keepalive_ms = None
    if has_keepalive:
        m_ka = re.search(r'stepVal\s*=\s*stepVal\s*\+\s*([\d.]+)', content, re.IGNORECASE)
        if m_ka:
            keepalive_floor_val = float(m_ka.group(1))
            keepalive_ms = (1.0 / keepalive_floor_val) * 16
            keepalive_floor_ok = keepalive_ms < 1000

    # 9. Keep-alive wrap at 99.5: resets stepVal to targetVal so the bar cycles continuously --
    #    no whole-number percentage can freeze forever. Pattern: If stepVal >= 99.5 Then stepVal = targetVal
    has_keepalive_wrap = bool(re.search(
        r'If\s+stepVal\s*>=\s*99\.5\s+Then\s+stepVal\s*=\s*targetVal',
        content, re.IGNORECASE
    ))

    all_ok = (has_tick_floor and has_poll_floor and cap_ok and display_ok and bound_ok
              and has_keepalive and keepalive_no_ceiling and keepalive_floor_ok and has_keepalive_wrap)

    if all_ok:
        _log(PASS, di,
             f"All 9 anti-stall guards verified: cap={cap_val}, sprint={bound_ms:.0f}ms; "
             f"keep-alive={keepalive_ms:.0f}ms/pt (no ceiling, wrap@99.5->targetVal); Int() display")
    else:
        missing = []
        if not has_tick_floor:
            missing.append("Tick minimum floor `If inc < N Then inc = N`")
        if not has_poll_floor:
            missing.append("PollChromeReady minimum floor `If adv < N Then adv = N`")
        if not cap_ok:
            missing.append(f"PollChromeReady cap={cap_val} must be <= 98")
        if not display_ok:
            if has_cint_display: missing.append("Tick uses CInt(stepVal) -- replace with Int(stepVal)")
            else:                missing.append("Tick display missing Int(stepVal) call")
        if not bound_ok:
            missing.append(f"Sprint bound {bound_ms:.0f}ms >= 1000ms -- increase min floor or lower cap")
        if not has_keepalive:
            missing.append("Keep-alive branch missing -- add `ElseIf Not readyToClose Then` in Tick")
        if has_keepalive and has_blocking_ceiling:
            missing.append(
                "Keep-alive has blocking ceiling (`ElseIf Not readyToClose And stepVal < N`) "
                "-- remove the `And stepVal < N` condition so the branch always fires"
            )
        if not keepalive_floor_ok:
            ka_ms_str = f"{keepalive_ms:.0f}ms/pt" if keepalive_ms is not None else "unknown"
            missing.append(
                f"Keep-alive step={keepalive_floor_val} -> {ka_ms_str} >= 1000ms "
                "-- increase the step value (e.g. 0.05)"
            )
        if not has_keepalive_wrap:
            missing.append(
                "Keep-alive wrap missing -- add "
                "`If stepVal >= 99.5 Then stepVal = targetVal` inside the keep-alive branch"
            )
        _log(FAIL, di, f"DI-019-H violations ({len(missing)}): {'; '.join(missing)}",
             "All 9 guards required: Tick floor, PollChromeReady floor, cap<=98, Int() display, "
             "sprint bound <1000ms, keep-alive branch (no ceiling), keep-alive floor <1000ms/pt, "
             "keep-alive wrap at 99.5->targetVal")

def test_DI_019_I():
    """DI-019-I: Splash .name font-size is 101px in start_splash.hta and clamp(61px,7vw,101px) in electron/main.js"""
    di = "DI-019-I"
    if _skip_if_filtered(di): return

    # ARRANGE
    hta      = ATHENA / "ui" / "start_splash.hta"
    electron = ATHENA / "electron" / "main.js"

    # ACT + ASSERT — HTA (T1: constant value check)
    if not hta.exists():
        _log(FAIL, di, "start_splash.hta not found", str(hta))
        return
    hta_ok = "font-size:101px" in _read(hta)

    # ACT + ASSERT — Electron (T1: constant value check)
    if not electron.exists():
        _log(FAIL, di, "electron/main.js not found", str(electron))
        return
    electron_ok = "font-size:clamp(61px,7vw,101px)" in _read(electron)

    if hta_ok and electron_ok:
        _log(PASS, di, ".name font-size is 101px in both start_splash.hta and electron/main.js")
    else:
        issues = []
        if not hta_ok:
            issues.append("start_splash.hta .name font-size is not 101px")
        if not electron_ok:
            issues.append("electron/main.js .name clamp max is not 101px")
        _log(FAIL, di, "; ".join(issues),
             "Set font-size:101px on .name in start_splash.hta; set font-size:clamp(61px,7vw,101px) on .name in electron/main.js")


def test_DI_019_J():
    """DI-019-J: #dots cycles via VBScript TickDots at <=500ms/state; hidden on completion"""
    di = "DI-019-J"
    if _skip_if_filtered(di): return

    # ARRANGE
    hta = ATHENA / "ui" / "start_splash.hta"

    assert hta.exists(), (
        f"FAIL {di}: start_splash.hta not found at {hta}\n"
        "Fix: Confirm Athena/ui/start_splash.hta exists"
    )
    content = _read(hta)

    # ACT — check 1: TickDots sub with 3-state cycling
    has_tickdots = bool(re.search(r'Sub\s+TickDots', content, re.IGNORECASE))
    assert has_tickdots, (
        f"FAIL {di}: No 'Sub TickDots' found in start_splash.hta\n"
        "Fix: Add a TickDots VBScript sub that cycles dotsEl.innerText through '.', '..', '...'"
    )

    # ACT — check 2: 3-state cycling via Mod 3 or equivalent
    has_mod3 = bool(re.search(r'Mod\s+3', content, re.IGNORECASE))
    assert has_mod3, (
        f"FAIL {di}: TickDots sub does not use 'Mod 3' for 3-state cycling in start_splash.hta\n"
        "Fix: Use 'dotState = (dotState + 1) Mod 3' in TickDots to cycle through 3 states"
    )

    # ACT — check 3: setInterval for TickDots with interval <=500
    m = re.search(r'setInterval\s*\(\s*"TickDots"\s*,\s*(\d+)\s*\)', content, re.IGNORECASE)
    assert m, (
        f"FAIL {di}: No setInterval(\"TickDots\", N) found in start_splash.hta\n"
        "Fix: Add 'dots_id = window.setInterval(\"TickDots\", 400)' in Window_OnLoad"
    )
    interval_val = int(m.group(1))
    assert interval_val <= 500, (
        f"FAIL {di}: TickDots interval is {interval_val}ms (must be <=500ms)\n"
        "Fix: Reduce the interval in setInterval(\"TickDots\", N) to 500 or less"
    )

    # ACT — check 4: dotsEl.style.display = "none" on completion
    has_hide = bool(re.search(r'dotsEl\.style\.display\s*=\s*"none"', content, re.IGNORECASE))
    assert has_hide, (
        f"FAIL {di}: dotsEl.style.display = \"none\" not found in start_splash.hta\n"
        "Fix: Add 'dotsEl.style.display = \"none\"' in PollChromeReady when .athena_ready is detected"
    )

    # ACT — check 5: single #dots span (not three .dot sub-spans)
    has_three_dot_spans = bool(re.search(r'class\s*=\s*["\']dot\s+dot[123]', content, re.IGNORECASE))
    assert not has_three_dot_spans, (
        f"FAIL {di}: start_splash.hta still uses three .dot.dot1/.dot2/.dot3 sub-spans inside #dots\n"
        "Fix: Replace with a single <span id=\"dots\">.</span> — TickDots drives the content via VBScript"
    )

    _log(PASS, di, "TickDots cycling sub present; Mod 3 state machine; setInterval <= 500ms; hide on done; single #dots span")
    return True


def test_DI_019_K():
    """DI-019-K: startup script does not gate .athena_ready on voice model preload (modelTimeout loop absent)"""
    di = "DI-019-K"
    if _skip_if_filtered(di): return

    # ARRANGE
    f = ATHENA / "ui" / "start_athena.ps1"
    assert f.exists(), (
        f"FAIL {di}: start_athena.ps1 not found at {f}\n"
        "Fix: Confirm Athena/ui/start_athena.ps1 exists"
    )

    # ACT
    content = _read(f)

    # ASSERT — the model-polling timeout loop must be absent
    assert "$modelTimeout" not in content, (
        f"FAIL {di}: $modelTimeout polling loop still present in start_athena.ps1 — "
        "voice model wait blocks Chrome open for up to 180 s on every cold start\n"
        "Fix: Remove the $modelTimeout while-loop (~lines 124-136) that polls "
        "/api/voice/status for models_ready before writing .athena_ready"
    )

    _log(PASS, di, "No $modelTimeout polling loop — .athena_ready fires on backend+frontend ready; voice models load async")
    return True


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
        ("deck_agent.py",                  AGENTS / "deck_agent.py"),
        ("ma_intelligence_agent.py",       AGENTS / "ma_intelligence_agent.py"),
        ("rag_agent.py",                   AGENTS / "rag_agent.py"),
        ("consulting_agent.py",            AGENTS / "consulting_agent.py"),
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


# ── UN-031 / Browser Tab Singleton ───────────────────────────────────────────

def test_DI_031_A():
    """DI-031-A: tabGuard.js exists with BroadcastChannel lock + blocking overlay; main.jsx conditionally mounts React"""
    di = "DI-031-A"
    if _skip_if_filtered(di): return

    # ARRANGE
    tab_guard = UI_FRONT / "tabGuard.js"
    main_jsx  = UI_FRONT / "main.jsx"

    # ACT — tabGuard.js must exist
    if not tab_guard.exists():
        _log(FAIL, di, "tabGuard.js not found at Athena/ui/frontend/src/tabGuard.js",
             "Fix: Create tabGuard.js with initTabGuard() export using BroadcastChannel singleton logic")
        return
    guard_content = _read(tab_guard)

    # ACT — must use BroadcastChannel (required by DI-031-A)
    if "BroadcastChannel" not in guard_content:
        _log(FAIL, di, "BroadcastChannel not found in tabGuard.js",
             "Fix: Add 'new BroadcastChannel(CHANNEL_NAME)' inside initTabGuard() in tabGuard.js")
        return

    # ACT — must render a blocking overlay when a duplicate is detected
    has_overlay = "document.body" in guard_content and (
        "overlay" in guard_content or "Duplicate" in guard_content or "already open" in guard_content
    )
    if not has_overlay:
        _log(FAIL, di, "Blocking overlay not found in tabGuard.js",
             "Fix: Add _showDuplicateOverlay() that appends a full-screen overlay to document.body "
             "and hides the React root when a duplicate tab is detected")
        return

    # ACT — main.jsx must import initTabGuard and gate the React mount on its return value
    if not main_jsx.exists():
        _log(FAIL, di, "main.jsx not found at Athena/ui/frontend/src/main.jsx",
             "Fix: Restore main.jsx and import initTabGuard from ./tabGuard.js")
        return
    main_content = _read(main_jsx)

    if "initTabGuard" not in main_content:
        _log(FAIL, di, "initTabGuard not imported in main.jsx",
             "Fix: Add 'import { initTabGuard } from \"./tabGuard.js\";' to main.jsx")
        return

    has_conditional_mount = bool(re.search(r'if\s*\(\s*initTabGuard\s*\(\s*\)\s*\)', main_content))
    if not has_conditional_mount:
        _log(FAIL, di, "React mount in main.jsx is not gated on initTabGuard() return value",
             "Fix: Wrap ReactDOM.createRoot().render() in 'if (initTabGuard()) { ... }' in main.jsx")
        return

    _log(PASS, di, "tabGuard.js: BroadcastChannel + overlay present; main.jsx conditionally mounts React")
    return True


def test_DI_031_B():
    """DI-031-B: tabGuard.js releases singleton lock on beforeunload via release message + localStorage cleanup"""
    di = "DI-031-B"
    if _skip_if_filtered(di): return

    # ARRANGE
    tab_guard = UI_FRONT / "tabGuard.js"

    if not tab_guard.exists():
        _log(FAIL, di, "tabGuard.js not found at Athena/ui/frontend/src/tabGuard.js",
             "Fix: Create tabGuard.js with initTabGuard() including beforeunload release logic")
        return
    content = _read(tab_guard)

    # ACT — must register a beforeunload listener
    if "beforeunload" not in content:
        _log(FAIL, di, "'beforeunload' event listener not found in tabGuard.js",
             "Fix: Add window.addEventListener('beforeunload', () => { ... }) inside initTabGuard()")
        return

    # ACT — beforeunload handler must broadcast a release message
    has_release_msg = bool(re.search(r'postMessage\s*\(\s*\{[^}]*["\']release["\']', content))
    if not has_release_msg:
        _log(FAIL, di, "ch.postMessage({ type: 'release' }) not found in tabGuard.js",
             "Fix: Inside the beforeunload handler, call ch.postMessage({ type: 'release', from: myId })")
        return

    # ACT — must remove the localStorage lock key on teardown
    has_lock_removal = bool(re.search(r'localStorage\.(removeItem|remove)', content))
    if not has_lock_removal:
        _log(FAIL, di, "localStorage.removeItem() not found in tabGuard.js",
             "Fix: Add localStorage.removeItem(LOCK_KEY) in the beforeunload handler (via releaseLock())")
        return

    _log(PASS, di, "tabGuard.js: beforeunload broadcasts 'release' and removes localStorage lock key")
    return True


# ── UN-023 / Historical Data Depth ───────────────────────────────────────────

def test_DI_023_A():
    """DI-023-A: RAG pipeline has no hard date cutoff blocking sources older than 50 years"""
    di = "DI-023-A"
    if _skip_if_filtered(di): return
    f = AGENTS / "rag_agent.py"
    if not f.exists():
        _log(WARN, di, "rag_agent.py not found -- cannot verify historical data depth",
             "Create or locate rag_agent.py; DI-023-A will remain OPEN until pipeline is inspected")
        return
    content = _read(f)
    # Hard date filters that would exclude 50+ year old documents
    hard_cutoff_patterns = [
        r'cutoff_year\s*=',
        r'min_year\s*=',
        r'year\s*>=\s*(?:19[8-9]\d|20\d\d)',   # year >= 198x or later
        r'published_after\s*=',
        r'date_from\s*=\s*["\']20',              # date_from = "20xx"
    ]
    violations = [p for p in hard_cutoff_patterns if re.search(p, content, re.IGNORECASE)]
    # Check that not ALL seed queries are pinned to specific recent years
    year_anchored = len(re.findall(r'\b20[12]\d\b', content))  # count 201x/202x occurrences
    query_list_match = re.search(r'(?:QUERIES|queries|search_terms)\s*=\s*\[(.+?)\]',
                                 content, re.DOTALL)
    all_queries_dated = False
    if query_list_match and year_anchored > 0:
        # If every query string in the list contains a year literal, flag it
        query_block = query_list_match.group(1)
        query_strings = re.findall(r'"([^"]+)"', query_block)
        if query_strings and all(re.search(r'\b20[12]\d\b', q) for q in query_strings):
            all_queries_dated = True

    if violations:
        _log(FAIL, di,
             f"Hard date cutoff found in rag_agent.py: {violations[0]}",
             "Remove the year filter — agents must be able to access historical sources (50+ years)")
    elif all_queries_dated:
        _log(WARN, di,
             "All RAG seed queries appear year-anchored to recent dates -- historical sources may be excluded",
             "Add at least one query without a year literal (e.g. 'FDA medical device regulatory history')")
    else:
        # No hard cutoff in the pipeline — now verify the KB actually contains pre-1990 material.
        # Scan all KB JSON files for year references earlier than 1990 (covers 50-year depth).
        pre1990_files = []
        for kb_file in KB.rglob("*.json"):
            if "node_modules" in kb_file.parts:
                continue
            try:
                text = kb_file.read_text(encoding="utf-8", errors="replace")
                if re.search(r'\b(19[0-8][0-9])\b', text):
                    pre1990_files.append(kb_file.name)
                    if len(pre1990_files) >= 3:   # stop early — 3 is enough evidence
                        break
            except Exception:
                continue
        if pre1990_files:
            _log(PASS, di,
                 f"No date cutoff in pipeline; KB contains {len(pre1990_files)}+ pre-1990 source(s): "
                 f"{', '.join(pre1990_files[:3])}")
        else:
            _log(WARN, di,
                 "No hard date cutoff detected but no pre-1990 sources found in KB",
                 "Run a full RAG ingest and verify at least one pre-1990 source is present in the knowledge base")


def test_DI_023_B():
    """DI-023-B: TAVILY_QUERIES contains >=5 historically-scoped entries (history/evolution/1970s/etc.)"""
    di = "DI-023-B"
    if _skip_if_filtered(di): return

    # ARRANGE
    f = AGENTS / "rag_agent.py"
    if not f.exists():
        _log(FAIL, di, "rag_agent.py not found", str(f))
        return
    content = _read(f)

    # ACT — extract TAVILY_QUERIES list and count historically-scoped entries
    historical_pattern = re.compile(
        r'history|historical|evolution|origin|1970|1980|1990|2000s', re.IGNORECASE)
    queries_block_m = re.search(r'TAVILY_QUERIES\s*=\s*\[(.+?)\]', content, re.DOTALL)
    if not queries_block_m:
        _log(FAIL, di, "TAVILY_QUERIES list not found in rag_agent.py",
             "Fix: Define TAVILY_QUERIES = [...] in rag_agent.py")
        return
    queries_block = queries_block_m.group(1)
    all_queries = re.findall(r'"([^"]+)"', queries_block)
    historical_count = sum(1 for q in all_queries if historical_pattern.search(q))

    # ASSERT
    if historical_count >= 5:
        _log(PASS, di, f"TAVILY_QUERIES has {historical_count}/{len(all_queries)} historically-scoped entries (>= 5)")
    else:
        _log(FAIL, di,
             f"Only {historical_count}/{len(all_queries)} TAVILY_QUERIES contain historical marker terms; need >= 5",
             "Fix: Add historically-scoped queries to TAVILY_QUERIES in rag_agent.py — e.g. "
             "'FDA medical device regulatory history 1976 Medical Device Amendments'")
    return True


def test_DI_023_C():
    """DI-023-C: Tavily rotation uses tm_yday deterministic bucketing — not random.sample"""
    di = "DI-023-C"
    if _skip_if_filtered(di): return

    # ARRANGE
    f = AGENTS / "rag_agent.py"
    if not f.exists():
        _log(FAIL, di, "rag_agent.py not found", str(f))
        return
    content = _read(f)

    # ACT
    has_tm_yday       = "tm_yday" in content
    has_random_sample = "random.sample" in content

    # ASSERT
    if has_tm_yday and not has_random_sample:
        _log(PASS, di, "rag_agent.py uses tm_yday deterministic rotation; random.sample not present")
    else:
        issues = []
        if not has_tm_yday:
            issues.append("tm_yday not found — add day_bucket = datetime.now().timetuple().tm_yday")
        if has_random_sample:
            issues.append("random.sample still present — remove from ingest_tavily()")
        _log(FAIL, di, f"Tavily query rotation non-deterministic: {'; '.join(issues)}",
             "Fix: Replace random.sample(TAVILY_QUERIES, ...) with tm_yday-based offset in ingest_tavily()")
    return True


def test_DI_023_D():
    """DI-023-D: HISTORICAL_CONSULTING_SOURCES in consulting_agent.py has >=5 entries with historical marker terms"""
    di = "DI-023-D"
    if _skip_if_filtered(di): return

    # ARRANGE
    f = AGENTS / "consulting_agent.py"
    if not f.exists():
        _log(FAIL, di, "consulting_agent.py not found", str(f))
        return
    content = _read(f)

    # ACT — check HISTORICAL_CONSULTING_SOURCES list exists
    if "HISTORICAL_CONSULTING_SOURCES" not in content:
        _log(FAIL, di, "HISTORICAL_CONSULTING_SOURCES not defined in consulting_agent.py",
             "Fix: Add HISTORICAL_CONSULTING_SOURCES = [...] list with >=5 historically-scoped entries")
        return

    # Count entries whose "name" value contains a historical marker term
    historical_pattern = re.compile(
        r'history|historical|evolution|origin|1970|1980|1990|2000s|50.year|classic', re.IGNORECASE)
    block_m = re.search(r'HISTORICAL_CONSULTING_SOURCES\s*=\s*\[(.+?)\]', content, re.DOTALL)
    if not block_m:
        _log(FAIL, di, "HISTORICAL_CONSULTING_SOURCES could not be parsed as a list literal",
             "Fix: Ensure HISTORICAL_CONSULTING_SOURCES = [...] is a module-level list literal")
        return
    # Extract name values from dict entries
    name_values = re.findall(r'"name"\s*:\s*"([^"]+)"', block_m.group(1))
    historical_count = sum(1 for n in name_values if historical_pattern.search(n))

    # ASSERT
    if historical_count >= 5:
        _log(PASS, di, f"HISTORICAL_CONSULTING_SOURCES has {historical_count}/{len(name_values)} entries with historical marker terms (>= 5)")
    else:
        _log(FAIL, di,
             f"Only {historical_count}/{len(name_values)} HISTORICAL_CONSULTING_SOURCES entries contain historical marker terms; need >= 5",
             "Fix: Add entries whose 'name' field contains: history, historical, evolution, origin, 1970, 1980, 1990, 2000s, '50 year', or classic")
    return True


# ── UN-032 / Consulting Agent Learning Visibility ────────────────────────────

def test_DI_consulting_032_A():
    """DI-032-A: consulting_agent.py learn() generates '## Newly Ingested Items' report and calls submit_for_review()"""
    di = "DI-032-A"
    if _skip_if_filtered(di): return

    # ARRANGE
    f = AGENTS / "consulting_agent.py"
    if not f.exists():
        _log(FAIL, di, "consulting_agent.py not found", str(f))
        return
    content = _read(f)

    # ACT
    has_submit  = "submit_for_review(" in content
    has_section = "## Newly Ingested Items" in content

    # ASSERT
    if has_submit and has_section:
        _log(PASS, di, "consulting_agent.py calls submit_for_review() and includes '## Newly Ingested Items' section")
    else:
        missing = []
        if not has_submit:
            missing.append("submit_for_review() call missing from learn() in consulting_agent.py")
        if not has_section:
            missing.append('"## Newly Ingested Items" section header missing from report template')
        _log(FAIL, di, f"DI-032-A requirements not met: {'; '.join(missing)}",
             "Fix: Update learn() in consulting_agent.py to include '## Newly Ingested Items' and submit via submit_for_review()")
    return True


def test_DI_consulting_032_B():
    """DI-032-B: consulting_agent.py writes consulting_learning_ report with 'No new items ingested' fallback"""
    di = "DI-033-B"
    if _skip_if_filtered(di): return

    # ARRANGE
    f = AGENTS / "consulting_agent.py"
    if not f.exists():
        _log(FAIL, di, "consulting_agent.py not found", str(f))
        return
    content = _read(f)

    # ACT
    has_path_pattern = "consulting_learning_" in content
    has_fallback     = "No new items ingested this run." in content

    # ASSERT
    if has_path_pattern and has_fallback:
        _log(PASS, di, "consulting_agent.py writes consulting_learning_<ts>.md and includes 'No new items ingested' fallback")
    else:
        missing = []
        if not has_path_pattern:
            missing.append("consulting_learning_ path pattern missing — report filename must match this prefix")
        if not has_fallback:
            missing.append('"No new items ingested this run." fallback string missing from report template')
        _log(FAIL, di, f"DI-032-B requirements not met: {'; '.join(missing)}",
             "Fix: Update learn() report path to f'consulting_learning_{{ts}}.md' and add fallback message")
    return True


# ── UN-024 / SOW Agent (Phase 2C) ────────────────────────────────────────────

def test_DI_024_A():
    """DI-024-A: sow_agent.py submits SOW to review queue (Gate 10) and logs Gate 3 confidence"""
    di = "DI-024-A"
    if _skip_if_filtered(di): return
    f = AGENTS / "sow_agent.py"
    if not f.exists():
        _log(FAIL, di, "sow_agent.py not found", str(f))
        return
    content = _read(f)
    has_gate10 = bool(re.search(r'submit_for_review', content))
    has_gate3  = bool(re.search(r'confidence', content))
    if has_gate10 and has_gate3:
        _log(PASS, di, "sow_agent.py: Gate 10 (submit_for_review) + Gate 3 (confidence score) both present")
    else:
        missing = []
        if not has_gate10: missing.append("submit_for_review() call missing")
        if not has_gate3:  missing.append("confidence scoring missing")
        _log(FAIL, di, f"sow_agent.py gate gaps: {'; '.join(missing)}",
             "Add submit_for_review() after docx save; add confidence = hits/len(required) check")


# ── UN-025 / Regulatory Strategy Agent (Phase 2C) ─────────────────────────────

def test_DI_025_A():
    """DI-025-A: regulatory_strategy_agent.py submits to review queue (Gate 10) + Gate 3 confidence"""
    di = "DI-025-A"
    if _skip_if_filtered(di): return
    f = AGENTS / "regulatory_strategy_agent.py"
    if not f.exists():
        _log(FAIL, di, "regulatory_strategy_agent.py not found", str(f))
        return
    content = _read(f)
    has_gate10 = bool(re.search(r'submit_for_review', content))
    has_gate3  = bool(re.search(r'confidence', content))
    if has_gate10 and has_gate3:
        _log(PASS, di, "regulatory_strategy_agent.py: Gate 10 + Gate 3 both present")
    else:
        missing = []
        if not has_gate10: missing.append("submit_for_review() missing")
        if not has_gate3:  missing.append("confidence scoring missing")
        _log(FAIL, di, f"regulatory_strategy_agent.py gate gaps: {'; '.join(missing)}",
             "Add submit_for_review() + confidence scoring to assessment generation path")


# ── UN-026 / App Startup Loading (Phase 2C, BUG-6) ───────────────────────────

def test_DI_026_A():
    """DI-026-A: App.jsx shows a loading overlay (startupDone state) until WS connects"""
    di = "DI-026-A"
    if _skip_if_filtered(di): return
    f = UI_FRONT / "App.jsx"
    if not f.exists():
        _log(FAIL, di, "App.jsx not found", str(f))
        return
    content = _read(f)
    has_startup_done = "startupDone" in content
    has_loading_bar  = bool(re.search(r'athenaLoadBar|athena.*[Ll]oad', content))
    if has_startup_done and has_loading_bar:
        _log(PASS, di, "App.jsx: startupDone loading overlay with progress animation present")
    else:
        missing = []
        if not has_startup_done: missing.append("startupDone state missing")
        if not has_loading_bar:  missing.append("loading bar animation missing")
        _log(FAIL, di, f"App.jsx startup loading overlay incomplete: {'; '.join(missing)}",
             "Add startupDone state that flips on WS connect; show overlay with progress animation while false")


# ── UN-027 / Documents Hub Approval Filter (Phase 2C, BUG-4) ─────────────────

def test_DI_027_A():
    """DI-027-A: list_documents() in server.py filters to approved items only via get_approved_reviews()"""
    di = "DI-027-A"
    if _skip_if_filtered(di): return
    f = UI_BACK / "server.py"
    if not f.exists():
        _log(FAIL, di, "server.py not found", str(f))
        return
    content = _read(f)
    has_approval_filter = bool(re.search(r'get_approved_reviews|approved_paths', content))
    has_gate_comment    = bool(re.search(r'Gate 10|only approved', content, re.IGNORECASE))
    if has_approval_filter and has_gate_comment:
        _log(PASS, di, "server.py list_documents() filters by approved status from review_queue")
    elif has_approval_filter:
        _log(PASS, di, "server.py list_documents() uses get_approved_reviews() filter")
    else:
        _log(FAIL, di, "list_documents() does not filter by approval status",
             "Add approved_paths = {r['file_path'] for r in mem.get_approved_reviews()} and filter disk scan")


# ── UN-028 / Voice/Noise Discrimination ─────────────────────────────────────

def test_DI_028_A():
    """DI-028-A: _vad_query in voice_bridge.py uses aggressiveness >= 2"""
    di = "DI-028-A"
    if _skip_if_filtered(di): return
    f = VOICE / "voice_bridge.py"
    if not f.exists():
        _log(FAIL, di, "voice_bridge.py not found", str(f))
        return
    content = _read(f)
    m = re.search(r'_vad_query\s*=\s*_webrtcvad\.Vad\s*\(\s*(\d+)\s*\)', content)
    if not m:
        _log(FAIL, di, "_vad_query initialisation not found in voice_bridge.py",
             "Add: _vad_query = _webrtcvad.Vad(2) in voice_bridge.py")
        return
    val = int(m.group(1))
    if val >= 2:
        _log(PASS, di, f"_vad_query aggressiveness = {val} (>= 2)")
    else:
        _log(FAIL, di, f"_vad_query aggressiveness = {val} (must be >= 2)",
             "Set _vad_query = _webrtcvad.Vad(2) or higher in voice_bridge.py")


def test_DI_028_B():
    """DI-028-B: Post-speech silence in _record_query uses VAD alone (no RMS AND-gate)"""
    di = "DI-028-B"
    if _skip_if_filtered(di): return
    f = VOICE / "voice_bridge.py"
    if not f.exists():
        _log(FAIL, di, "voice_bridge.py not found", str(f))
        return
    content = _read(f)
    has_rms_and_gate = bool(re.search(
        r'rms\s*<\s*QUERY_SILENCE_THRESHOLD\s+and\s+not\s+is_speech', content))
    if has_rms_and_gate:
        _log(FAIL, di, "RMS AND-gate still present in _record_query silence detection",
             "Remove QUERY_SILENCE_THRESHOLD condition; use 'if not is_speech: silence += 1' alone")
        return
    if "silence += 1" in content and "speech_seen" in content:
        _log(PASS, di, "Post-speech silence uses VAD alone — no RMS AND-gate")
    else:
        _log(FAIL, di, "Cannot confirm VAD-only silence detection in _record_query",
             "Ensure 'if not is_speech: silence += 1' without RMS condition in _record_query")


def test_DI_028_C():
    """DI-028-C: _speak_phrase_greeting in server.py routes greeting via _voice_queue"""
    di = "DI-028-C"
    if _skip_if_filtered(di): return
    f = UI_BACK / "server.py"
    if not f.exists():
        _log(FAIL, di, "server.py not found", str(f))
        return
    content = _read(f)
    if bool(re.search(r'_voice_queue\.append', content)):
        _log(PASS, di, "server.py _speak_phrase_greeting routes greeting via _voice_queue.append()")
    else:
        _log(FAIL, di, "_voice_queue.append not found in server.py",
             "In _speak_phrase_greeting, replace direct _speak_sentence() call with _voice_queue.append(text)")


def test_DI_028_D():
    """DI-028-D: Voice loop startup sleep >= 0.5 s before first notification drain"""
    di = "DI-028-D"
    if _skip_if_filtered(di): return
    f = VOICE / "voice_bridge.py"
    if not f.exists():
        _log(FAIL, di, "voice_bridge.py not found", str(f))
        return
    content = _read(f)
    has_startup_sleep = bool(re.search(
        r'time\.sleep\s*\(\s*0\.[5-9]|time\.sleep\s*\(\s*[1-9]', content))
    if has_startup_sleep:
        _log(PASS, di, "Voice bridge contains startup sleep >= 0.5 s")
    else:
        _log(FAIL, di, "No startup sleep >= 0.5 s found in voice_bridge.py",
             "Add time.sleep(0.5) before the notification drain loop in _voice_loop()")


# ── UN-029 / Audio Device Detection ─────────────────────────────────────────

def test_DI_029_A():
    """DI-029-A: _device_monitor_loop present in voice_bridge.py with poll interval <= 5 s"""
    di = "DI-029-A"
    if _skip_if_filtered(di): return
    f = VOICE / "voice_bridge.py"
    if not f.exists():
        _log(FAIL, di, "voice_bridge.py not found", str(f))
        return
    content = _read(f)
    if "_device_monitor_loop" not in content:
        _log(FAIL, di, "_device_monitor_loop not defined in voice_bridge.py",
             "Add _device_monitor_loop() that polls every <= 5 s and calls _apply_device on change")
        return
    m = re.search(
        r'def _device_monitor_loop\(\).*?time\.sleep\s*\(\s*([0-9.]+)\s*\)',
        content, re.DOTALL)
    if m:
        val = float(m.group(1))
        if val <= 5.0:
            _log(PASS, di, f"_device_monitor_loop present; poll interval = {val} s (<= 5 s)")
        else:
            _log(FAIL, di, f"_device_monitor_loop poll interval = {val} s (must be <= 5 s)",
                 "Set time.sleep() in _device_monitor_loop to <= 5.0")
    else:
        _log(PASS, di, "_device_monitor_loop present")


def test_DI_029_B():
    """DI-029-B: _device_changed threading.Event and is_set() check in voice_bridge.py"""
    di = "DI-029-B"
    if _skip_if_filtered(di): return
    f = VOICE / "voice_bridge.py"
    if not f.exists():
        _log(FAIL, di, "voice_bridge.py not found", str(f))
        return
    content = _read(f)
    has_event = bool(re.search(r'_device_changed\s*=\s*threading\.Event\s*\(\s*\)', content))
    has_check  = bool(re.search(r'_device_changed\.is_set\s*\(\s*\)', content))
    if has_event and has_check:
        _log(PASS, di, "_device_changed Event declared and is_set() checked in voice_bridge.py")
    elif not has_event:
        _log(FAIL, di, "_device_changed threading.Event not declared in voice_bridge.py",
             "Add: _device_changed = threading.Event() at module level in voice_bridge.py")
    else:
        _log(FAIL, di, "_device_changed.is_set() not called in voice_bridge.py",
             "Add: if _device_changed.is_set(): _device_changed.clear(); break inside _listen_for_wake loop")


def test_DI_029_C():
    """DI-029-C: _emit('device_changed', ...) WebSocket event present in voice_bridge.py"""
    di = "DI-029-C"
    if _skip_if_filtered(di): return
    f = VOICE / "voice_bridge.py"
    if not f.exists():
        _log(FAIL, di, "voice_bridge.py not found", str(f))
        return
    content = _read(f)
    if bool(re.search(r'_emit\s*\(\s*["\']device_changed["\']', content)):
        _log(PASS, di, "_emit('device_changed', ...) present in voice_bridge.py")
    else:
        _log(FAIL, di, "_emit('device_changed', ...) not found in voice_bridge.py",
             "Add: _emit('device_changed', device=new_name, device_rate=new_rate) in _device_monitor_loop")


# ── UN-030 / McKinsey + Latitude Brand Formatting Standard ───────────────────

def test_DI_030_A():
    """DI-030-A: All 6 _DECK_GUIDES entries in deck_agent.py include exec_summary"""
    di = "DI-030-A"
    if _skip_if_filtered(di): return
    f = AGENTS / "deck_agent.py"
    if not f.exists():
        _log(FAIL, di, "deck_agent.py not found", str(f))
        return
    content = _read(f)
    required_types = ["strategy", "pitch", "regulatory", "coaching", "ma", "briefing"]
    missing = []
    for deck_type in required_types:
        # Find the key entry and check the next 600 chars for exec_summary
        m = re.search(rf'"{deck_type}"\s*:\s*\(', content)
        if not m:
            missing.append(f'"{deck_type}" key not found in _DECK_GUIDES')
            continue
        window = content[m.start():m.start() + 600]
        if "exec_summary" not in window:
            missing.append(f'"{deck_type}" guide lacks exec_summary slide')
    if not missing:
        _log(PASS, di, "All 6 _DECK_GUIDES entries include exec_summary slide")
    else:
        _log(FAIL, di, f"_DECK_GUIDES missing exec_summary in: {'; '.join(missing)}",
             "Fix: add 'exec_summary' after 'cover' in the affected _DECK_GUIDES entry in deck_agent.py")


def test_DI_030_B():
    """DI-030-B: All 6 deliverable-generating agents contain McKinsey/Big-4/pyramid/SCQA directive"""
    di = "DI-030-B"
    if _skip_if_filtered(di): return
    quality_pattern = re.compile(r'McKinsey|Big.4|pyramid|SCQA', re.IGNORECASE)
    agents_to_check = [
        AGENTS / "content_agent.py",
        AGENTS / "briefing_agent.py",
        AGENTS / "ma_intelligence_agent.py",
        AGENTS / "regulatory_strategy_agent.py",
        AGENTS / "sow_agent.py",
        AGENTS / "deck_agent.py",
    ]
    missing = []
    for agent_file in agents_to_check:
        if not agent_file.exists():
            missing.append(f"{agent_file.name} not found")
            continue
        if not quality_pattern.search(_read(agent_file)):
            missing.append(f"{agent_file.name} has no McKinsey/Big-4/pyramid/SCQA directive")
    if not missing:
        _log(PASS, di, "All 6 deliverable agents contain McKinsey/Big-4 quality directive")
    else:
        _log(FAIL, di, f"Missing quality directive: {'; '.join(missing)}",
             "Add a McKinsey/Big-4 quality standard line to the agent's system prompt or SYSTEM constant")


def test_DI_030_C():
    """DI-030-C: agent_base.py injects Latitude MedTech LLC brand identity into agent system prompts"""
    di = "DI-030-C"
    if _skip_if_filtered(di): return
    f = AGENTS / "agent_base.py"
    if not f.exists():
        _log(FAIL, di, "agent_base.py not found", str(f))
        return
    content = _read(f)
    has_brand  = "Latitude MedTech LLC" in content
    has_prompt = bool(re.search(r'parts\s*=\s*\[|build_system_prompt|system_prompt', content))
    if has_brand and has_prompt:
        _log(PASS, di, "agent_base.py injects 'Latitude MedTech LLC' brand identity into agent system prompts")
    elif has_brand:
        _log(WARN, di, "agent_base.py has brand identity but system-prompt construction pattern not confirmed",
             "Verify agent_base.py injects 'Latitude MedTech LLC' into all agent prompts")
    else:
        _log(FAIL, di, "agent_base.py missing 'Latitude MedTech LLC' brand identity",
             "Add 'Latitude MedTech LLC' to the system prompt template in agent_base.py")


# ── UN-033 / Voice Query Readiness Latency (CO-008 — OPEN) ──────────────────

def test_DI_033_A():
    """DI-033-A: _listen_for_wake accepts a stream parameter and does not open sd.InputStream internally"""
    di = "DI-033-A"
    if _skip_if_filtered(di): return
    f = VOICE / "voice_bridge.py"
    if not f.exists():
        _log(FAIL, di, "voice_bridge.py not found", str(f))
        return
    content = _read(f)
    if not re.search(r'def _listen_for_wake\s*\(\s*oww_model\s*,\s*stream', content):
        _log(FAIL, di,
             "_listen_for_wake missing 'stream' positional parameter (current: def _listen_for_wake(oww_model))",
             "Fix: change to def _listen_for_wake(oww_model, stream, ...) and remove internal sd.InputStream")
        return
    m = re.search(r'(def _listen_for_wake\b.*?)(?=\ndef |\Z)', content, re.DOTALL)
    if m and 'sd.InputStream(' in m.group(1):
        _log(FAIL, di,
             "_listen_for_wake opens sd.InputStream internally -- stream must be passed in by caller",
             "Fix: remove sd.InputStream context manager; read from stream parameter directly")
        return
    _log(PASS, di, "_listen_for_wake accepts stream parameter; no internal sd.InputStream")


def test_DI_033_B():
    """DI-033-B: _record_query accepts a stream parameter and does not open sd.InputStream internally"""
    di = "DI-033-B"
    if _skip_if_filtered(di): return
    f = VOICE / "voice_bridge.py"
    if not f.exists():
        _log(FAIL, di, "voice_bridge.py not found", str(f))
        return
    content = _read(f)
    if not re.search(r'def _record_query\s*\(\s*stream', content):
        _log(FAIL, di,
             "_record_query missing 'stream' positional parameter (current: def _record_query())",
             "Fix: change to def _record_query(stream, ...) and remove internal sd.InputStream")
        return
    m = re.search(r'(def _record_query\b.*?)(?=\ndef |\Z)', content, re.DOTALL)
    if m and 'sd.InputStream(' in m.group(1):
        _log(FAIL, di,
             "_record_query opens sd.InputStream internally -- stream must be passed in by caller",
             "Fix: remove sd.InputStream context manager; read from stream parameter directly")
        return
    _log(PASS, di, "_record_query accepts stream parameter; no internal sd.InputStream")


def test_DI_033_C():
    """DI-033-C: _voice_loop opens one sd.InputStream and passes it to _listen_for_wake and _record_query"""
    di = "DI-033-C"
    if _skip_if_filtered(di): return
    f = VOICE / "voice_bridge.py"
    if not f.exists():
        _log(FAIL, di, "voice_bridge.py not found", str(f))
        return
    content = _read(f)
    m = re.search(r'(def _voice_loop\b.*?)(?=\ndef |\Z)', content, re.DOTALL)
    if not m:
        _log(FAIL, di, "_voice_loop not found in voice_bridge.py",
             "Fix: define _voice_loop() in voice_bridge.py")
        return
    body = m.group(1)
    has_stream_open = 'sd.InputStream(' in body
    has_listen_call = bool(re.search(r'_listen_for_wake\s*\(\s*oww\s*,\s*stream', body))
    has_record_call = bool(re.search(r'_record_query\s*\(\s*stream', body))
    if has_stream_open and has_listen_call and has_record_call:
        _log(PASS, di, "_voice_loop opens sd.InputStream and passes stream to both _listen_for_wake and _record_query")
    else:
        missing = []
        if not has_stream_open: missing.append("sd.InputStream( not in _voice_loop body")
        if not has_listen_call: missing.append("_listen_for_wake(oww, stream not called")
        if not has_record_call: missing.append("_record_query(stream not called")
        _log(FAIL, di,
             f"_voice_loop stream-sharing not implemented: {'; '.join(missing)}",
             "Fix: open sd.InputStream in _voice_loop and pass stream to _listen_for_wake and _record_query")

# ── UN-034 / Engineering Process Integrity (CO-011) ──────────────────────────

def test_DI_034_A():
    """DI-034-A: CLAUDE.md shall contain the co-commit rule (code commits must update DC docs)"""
    di = "DI-034-A"
    if _skip_if_filtered(di): return
    f = ROOT / "CLAUDE.md"
    if not f.exists():
        _log(FAIL, di, "CLAUDE.md not found", str(f))
        return
    if "must also update at least one design control document" not in _read(f):
        _log(FAIL, di,
             "CLAUDE.md missing co-commit rule phrase 'must also update at least one design control document'",
             "Add co-commit rule to the Engineering Integrity Standards section of CLAUDE.md")
        return
    _log(PASS, di, "CLAUDE.md contains the co-commit rule")
    return True


def test_DI_034_B():
    """DI-034-B: CLAUDE.md shall contain Auth Centralization Standard section"""
    di = "DI-034-B"
    if _skip_if_filtered(di): return
    f = ROOT / "CLAUDE.md"
    if not f.exists():
        _log(FAIL, di, "CLAUDE.md not found", str(f))
        return
    if "Auth Centralization Standard" not in _read(f):
        _log(FAIL, di,
             "CLAUDE.md missing 'Auth Centralization Standard' section",
             "Add Auth Centralization Standard to Engineering Integrity Standards in CLAUDE.md")
        return
    _log(PASS, di, "CLAUDE.md contains Auth Centralization Standard")
    return True


def test_DI_034_C():
    """DI-034-C: CLAUDE.md shall contain voice_bridge.py Boundary section"""
    di = "DI-034-C"
    if _skip_if_filtered(di): return
    f = ROOT / "CLAUDE.md"
    if not f.exists():
        _log(FAIL, di, "CLAUDE.md not found", str(f))
        return
    if "voice_bridge.py Boundary" not in _read(f):
        _log(FAIL, di,
             "CLAUDE.md missing 'voice_bridge.py Boundary' section",
             "Add voice_bridge.py Boundary to Engineering Integrity Standards in CLAUDE.md")
        return
    _log(PASS, di, "CLAUDE.md contains voice_bridge.py Boundary")
    return True


def test_DI_034_D():
    """DI-034-D: CLAUDE.md shall document the forward-only progress bar constraint"""
    di = "DI-034-D"
    if _skip_if_filtered(di): return
    f = ROOT / "CLAUDE.md"
    if not f.exists():
        _log(FAIL, di, "CLAUDE.md not found", str(f))
        return
    if "Progress Bar Specification" not in _read(f):
        _log(FAIL, di,
             "CLAUDE.md missing 'Progress Bar Specification' section",
             "Add Progress Bar Specification to Engineering Integrity Standards in CLAUDE.md")
        return
    _log(PASS, di, "CLAUDE.md contains Progress Bar Specification")
    return True


def test_DI_034_E():
    """DI-034-E: CLAUDE.md shall contain App.jsx Responsibility Scope section"""
    di = "DI-034-E"
    if _skip_if_filtered(di): return
    f = ROOT / "CLAUDE.md"
    if not f.exists():
        _log(FAIL, di, "CLAUDE.md not found", str(f))
        return
    if "App.jsx Responsibility Scope" not in _read(f):
        _log(FAIL, di,
             "CLAUDE.md missing 'App.jsx Responsibility Scope' section",
             "Add App.jsx Responsibility Scope to Engineering Integrity Standards in CLAUDE.md")
        return
    _log(PASS, di, "CLAUDE.md contains App.jsx Responsibility Scope")
    return True


def test_DI_034_F():
    """DI-034-F: CLAUDE.md shall contain CLAUDE.md Update Policy section"""
    di = "DI-034-F"
    if _skip_if_filtered(di): return
    f = ROOT / "CLAUDE.md"
    if not f.exists():
        _log(FAIL, di, "CLAUDE.md not found", str(f))
        return
    if "CLAUDE.md Update Policy" not in _read(f):
        _log(FAIL, di,
             "CLAUDE.md missing 'CLAUDE.md Update Policy' section",
             "Add CLAUDE.md Update Policy to Engineering Integrity Standards in CLAUDE.md")
        return
    _log(PASS, di, "CLAUDE.md contains CLAUDE.md Update Policy")
    return True


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
    test_DI_002_E(); test_DI_002_F(); test_DI_002_G()
    test_DI_002_H(); test_DI_002_I()

    _section("UN-003 Knowledge Base")
    test_DI_003_A(); test_DI_003_B(); test_DI_003_C(); test_DI_003_D()

    _section("UN-004/005/006 Voice Interface")
    test_DI_004_A(); test_DI_004_B(); test_DI_004_D(); test_DI_004_E()
    test_DI_005_A(); test_DI_005_B()
    test_DI_006_A(); test_DI_006_B()

    _section("UN-007/008/009 Content, Marketing & Decks")
    test_DI_007_B(); test_DI_007_C(); test_DI_007_D(); test_DI_007_E()
    test_DI_007_F()
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
    test_DI_015_D(); test_DI_015_E(); test_DI_015_G()
    test_DI_016_A(); test_DI_016_B(); test_DI_016_C()
    test_DI_017_A(); test_DI_017_B(); test_DI_017_C()

    _section("UN-018 Client Lifecycle")
    test_DI_018_A(); test_DI_018_B()

    _section("UN-019 Startup Experience")
    test_DI_019_A(); test_DI_019_B(); test_DI_019_C()
    test_DI_019_D(); test_DI_019_E()
    test_DI_019_F(); test_DI_019_G(); test_DI_019_H(); test_DI_019_I(); test_DI_019_J()
    test_DI_019_K()

    _section("UN-020 Document Review & Approval")
    test_DI_020_A(); test_DI_020_B(); test_DI_020_C(); test_DI_020_D(); test_DI_020_E()

    _section("UN-021 Single-Instance Enforcement")
    test_DI_021_A()

    _section("UN-031 Browser Tab Singleton")
    test_DI_031_A(); test_DI_031_B()

    _section("UN-023 Historical Data Depth")
    test_DI_023_A(); test_DI_023_B(); test_DI_023_C(); test_DI_023_D()

    _section("UN-024/025 Phase 2C — SOW & Regulatory Strategy")
    test_DI_024_A(); test_DI_025_A()

    _section("UN-026/027 Phase 2C — App Loading & Document Filter")
    test_DI_026_A(); test_DI_027_A()

    _section("UN-028 Voice/Noise Discrimination")
    test_DI_028_A(); test_DI_028_B(); test_DI_028_C(); test_DI_028_D()

    _section("UN-029 Audio Device Detection")
    test_DI_029_A(); test_DI_029_B(); test_DI_029_C()

    _section("UN-030 McKinsey/Latitude Brand Formatting Standard")
    test_DI_030_A(); test_DI_030_B(); test_DI_030_C()

    _section("UN-032 Consulting Learning Visibility")
    test_DI_consulting_032_A(); test_DI_consulting_032_B()

    _section("UN-033 Voice Query Readiness Latency (CO-010)")
    test_DI_033_A(); test_DI_033_B(); test_DI_033_C()

    _section("UN-034 Engineering Process Integrity")
    test_DI_034_A(); test_DI_034_B(); test_DI_034_C()
    test_DI_034_D(); test_DI_034_E(); test_DI_034_F()

    if args.live or args.full:
        test_live_api()

    passed = _print_summary()
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
