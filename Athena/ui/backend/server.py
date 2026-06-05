"""
Latitude MedTech — Local Backend API
======================================
FastAPI server that powers the desktop UI.
Runs on localhost:8000.

Start: python server.py
"""

import os
import sys
import re
import json
import secrets
import subprocess
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from dotenv import load_dotenv

ATHENA      = Path(__file__).resolve().parents[2]        # ui/backend/ -> ui/ -> Athena/
AGENTS_DIR  = ATHENA / "agents"
VENV_PYTHON = ATHENA / "voice" / "venv" / "Scripts" / "python.exe"

# ── App version (single source of truth: Athena/VERSION.json) ──────────────────
def _load_version_info() -> dict:
    """Read the canonical version metadata. Never raises — falls back to a
    dev placeholder so a missing/corrupt VERSION.json can't block startup."""
    try:
        return json.loads((ATHENA / "VERSION.json").read_text(encoding="utf-8"))
    except Exception:
        return {"version": "0.0.0", "released": "unknown", "channel": "dev"}

VERSION_INFO = _load_version_info()
APP_VERSION  = VERSION_INFO.get("version", "0.0.0")

load_dotenv(ATHENA / "voice" / ".env")

sys.path.insert(0, str(AGENTS_DIR))

try:
    from memory import Memory
    mem = Memory()
except ImportError:
    mem = None

# LangGraph coaching orchestrator (Phase 1A). Loaded lazily so a missing
# langgraph install never blocks server startup.
_orch = None
def _orchestrator():
    global _orch
    if _orch is None:
        import orchestrator as _orch  # noqa: F811
    return _orch

# ── Session token (generated once per server start) ───────────────────────────
_KEY_FILE = ATHENA / "voice" / ".athena.key"

def _get_or_create_token() -> str:
    if _KEY_FILE.exists():
        token = _KEY_FILE.read_text().strip()
        if len(token) >= 32:
            return token
    token = secrets.token_hex(32)
    _KEY_FILE.write_text(token)
    try:
        import stat
        _KEY_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass
    return token

SESSION_TOKEN = _get_or_create_token()

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

# ── Security helpers ──────────────────────────────────────────────────────────

_SAFE_FILENAME = re.compile(r'^[\w\-. ]+$')
_SAFE_ARG      = re.compile(r'^[\w\-. /:\[\]@#]+$')

def _safe_filename(name: str) -> str:
    """Reject filenames with path traversal characters."""
    if not name or not _SAFE_FILENAME.match(name) or '..' in name or '/' in name or '\\' in name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return name

def _safe_arg(arg: str, max_len: int = 500) -> str:
    """Sanitise a free-text override arg — strip shell metacharacters."""
    if not arg:
        return ""
    sanitised = re.sub(r'[;&|`$<>{}]', '', arg)[:max_len]
    return sanitised.strip()

# ── Security headers middleware ───────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"]  = "nosniff"
        response.headers["X-Frame-Options"]         = "DENY"
        response.headers["Referrer-Policy"]         = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"]        = "1; mode=block"
        # Tight CSP for local-only app
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' ws://localhost:* http://localhost:*; "
            "img-src 'self' data: blob:;"
        )
        return response

app = FastAPI(title="Latitude MedTech", version=APP_VERSION,
              docs_url=None, redoc_url=None)  # disable public docs
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SecurityHeadersMiddleware)

# ── Voice bridge ──────────────────────────────────────────────────────────────
sys.path.insert(0, str(ATHENA / "voice"))
try:
    from voice_bridge import router as voice_router, voice_websocket_endpoint
    app.include_router(voice_router)
    VOICE_AVAILABLE = True
    print("[voice] Voice bridge loaded — OWW + Whisper + Kokoro preloading in background")
except Exception as _ve:
    VOICE_AVAILABLE = False
    print(f"[voice] Bridge not loaded: {_ve}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000",
                   "app://.", "file://"],           # Electron origins
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-Athena-Key"],
    allow_credentials=False,
)

# ── WebSocket manager ─────────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)

manager = ConnectionManager()
running_agents = set()  # Prevent duplicate runs

_shutting_down = False           # set True once /api/shutdown is called
_goodbye_task  = None            # asyncio.Task — delayed goodbye after WS disconnect


async def _ws_goodbye():
    """Play TTS farewell 3 s after all WebSocket clients disconnect.

    The 3-second window absorbs page-refresh reconnects without triggering TTS.
    Guarded by _shutting_down so the in-app exit button never double-speaks.
    """
    import asyncio as _asyncio
    await _asyncio.sleep(3)
    if manager.active or _shutting_down:
        return
    stop_script = ATHENA / "ui" / "stop_athena.ps1"
    phrase = _random.choice(_GOODBYES)
    await _asyncio.get_event_loop().run_in_executor(None, _speak_phrase, phrase)
    try:
        flags = (getattr(subprocess, "CREATE_NO_WINDOW", 0) |
                 getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        subprocess.Popen(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-NoProfile",
             "-File", str(stop_script)],
            creationflags=flags, close_fds=True,
        )
    except Exception:
        pass
    import os as _os; _os._exit(0)


# ── Agent runner ──────────────────────────────────────────────────────────────

async def run_agent(agent_name: str, script: str, args: list = None):
    """Run an agent script and stream output via WebSocket."""
    if agent_name in running_agents:
        await manager.broadcast({"type": "agent_log", "agent": agent_name, "line": f"[SKIPPED] {agent_name} already running"})
        return
    running_agents.add(agent_name)
    await manager.broadcast({"type": "agent_start", "agent": agent_name, "ts": datetime.now().isoformat()})

    cmd = [str(VENV_PYTHON), str(AGENTS_DIR / script)] + (args or [])
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(AGENTS_DIR),
    )

    lines = []
    async for line in proc.stdout:
        text = line.decode('utf-8', errors='replace').rstrip()
        lines.append(text)
        await manager.broadcast({"type": "agent_log", "agent": agent_name, "line": text})

    await proc.wait()
    running_agents.discard(agent_name)
    status = "success" if proc.returncode == 0 else "error"
    await manager.broadcast({"type": "agent_done", "agent": agent_name, "status": status, "ts": datetime.now().isoformat()})
    return {"status": status, "lines": lines}


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "Latitude MedTech API", "version": APP_VERSION}


@app.get("/api/version")
def get_version():
    """Current Athena version plus the full changelog (raw Markdown).

    Source of truth is Athena/VERSION.json (cached at startup as VERSION_INFO);
    the changelog is read fresh so edits show up without a server restart.
    """
    changelog = ""
    try:
        changelog = (ATHENA / "CHANGELOG.md").read_text(encoding="utf-8")
    except Exception:
        pass
    return {**VERSION_INFO, "changelog": changelog}


@app.get("/api/auth/token")
def get_token():
    """Returns the session token for the local UI. No auth required (localhost only)."""
    return {"token": SESSION_TOKEN}


_dashboard_cache = {"data": None, "ts": 0}

@app.get("/api/dashboard")
def get_dashboard():
    global _dashboard_cache
    # Cache for 60 seconds
    if _dashboard_cache["data"] and (datetime.now().timestamp() - _dashboard_cache["ts"]) < 60:
        return _dashboard_cache["data"]
    if not mem:
        return {"error": "Memory not available"}
    try:
        report = mem.get_token_report(days=30)
        kb     = mem.get_kb_stats()
        topics = mem.get_recent_topics(days=90)
        result = {
            "token_report": report,
            "kb_stats":     kb,
            "recent_topics":topics[:20],
            "generated_at": datetime.now().isoformat(),
        }
        _dashboard_cache = {"data": result, "ts": datetime.now().timestamp()}
        return result
    except Exception as e:
        return {"error": str(e), "token_report": {}, "kb_stats": {}, "recent_topics": []}


# ── Voice session log ─────────────────────────────────────────────────────────

SESSIONS_FILE = ATHENA / "voice" / "sessions.jsonl"

class SessionLogBody(BaseModel):
    started_at: str
    ended_at: str
    duration_secs: int
    queries: int
    device: Optional[str] = ""

@app.post("/api/sessions/log")
async def log_session(body: SessionLogBody):
    record = body.dict()
    with open(SESSIONS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return {"status": "logged"}

@app.get("/api/sessions")
def get_sessions(limit: int = 20):
    if not SESSIONS_FILE.exists():
        return {"sessions": []}
    sessions = []
    with open(SESSIONS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    sessions.append(json.loads(line))
                except Exception:
                    pass
    return {"sessions": list(reversed(sessions[-limit:]))}


@app.get("/api/drafts")
def list_drafts():
    drafts_dir = ATHENA / 'content' / 'drafts'
    if not drafts_dir.exists():
        return {"drafts": []}
    files = sorted(drafts_dir.glob('*.md'), key=lambda f: f.stat().st_mtime, reverse=True)
    drafts = []
    for f in files[:20]:
        content = f.read_text(encoding='utf-8', errors='replace')
        title   = f.stem
        # Extract title from frontmatter
        for line in content.splitlines():
            if line.startswith('title:'):
                title = line.replace('title:', '').strip()
                break
        drafts.append({
            "filename": f.name,
            "title":    title,
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            "size":     f.stat().st_size,
            "path":     str(f),
        })
    return {"drafts": drafts}


@app.get("/api/drafts/{filename}")
def get_draft(filename: str):
    drafts_dir = ATHENA / 'content' / 'drafts'
    f = drafts_dir / filename
    if not f.exists():
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return {"filename": filename, "content": f.read_text(encoding='utf-8', errors='replace')}


@app.get("/api/briefings")
def list_briefings():
    briefings_dir = ATHENA / 'briefings'
    if not briefings_dir.exists():
        return {"briefings": []}
    files = sorted(
        [f for f in briefings_dir.glob('*.md') if not f.name.startswith('.')],
        key=lambda f: f.stat().st_mtime, reverse=True
    )
    briefings = []
    for f in files[:10]:
        briefings.append({
            "filename": f.name,
            "date":     f.name[:10],
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            "path":     str(f),
        })
    return {"briefings": briefings}


@app.get("/api/briefings/{filename}")
def get_briefing(filename: str):
    briefings_dir = ATHENA / 'briefings'
    f = briefings_dir / filename
    if not f.exists():
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return {"filename": filename, "content": f.read_text(encoding='utf-8', errors='replace')}


@app.get("/api/kb/stats")
def kb_stats():
    if not mem:
        return {"error": "Memory not available"}
    return mem.get_kb_stats()


# ── HR + Learning routes ──────────────────────────────────────────────────────

# Canonical agent roster (label + tier) so the Workforce view always renders a
# full row set even before the first HR Review has run.
WORKFORCE_ROSTER = [
    ("content",         "Content Agent",         "Manager"),
    ("briefing",        "Briefing Agent",        "Senior Associate"),
    ("iso",             "ISO Coach Agent",       "Manager"),
    ("coaching",        "Coaching Brief Agent",  "Manager"),
    ("fda",             "FDA Agent",             "Manager"),
    ("eu_mdr",          "EU MDR Agent",          "Manager"),
    ("rag",             "RAG Ingestion Agent",   "Senior Associate"),
    ("consulting",      "Consulting Agent",      "Senior Manager"),
    ("ma_intelligence", "M&A Intelligence Agent","Senior Manager"),
    ("hr",              "HR / L&D Manager Agent","Business Function"),
    ("voice_bridge",    "Voice Assistant",       "Associate"),
]


@app.get("/api/hr/health")
def hr_health():
    if not mem:
        return {"error": "Memory not available"}
    # Stored flag/error data keyed by agent (populated by the last HR Review).
    stored = {a["agent"]: a for a in mem.get_all_agent_health()}
    agents = []
    for key, label, tier in WORKFORCE_ROSTER:
        row = dict(stored.get(key, {"agent": key, "flag_status": "green",
                                    "error_count_7d": 0, "learning_7d": 0,
                                    "flag_reason": None}))
        row.setdefault("agent", key)
        row["label"] = label
        row["tier"]  = tier
        # Always overlay live timestamps so they never read "Never" while
        # activity exists in the DB under any name variant.
        live_run   = mem.get_agent_last_run(key)
        live_learn = mem.get_last_learning(key)
        if live_run:
            row["last_run"] = live_run
        if live_learn:
            row["last_learning"] = live_learn["timestamp"]
        agents.append(row)
    # Include any stored agents not in the roster (forward-compat).
    for key, a in stored.items():
        if key not in {k for k, _, _ in WORKFORCE_ROSTER}:
            agents.append(a)
    return {"agents": agents}


@app.get("/api/hr/skills")
def hr_skills():
    """Live skill/KB accumulation per agent, queried directly from the memory DB."""
    if not mem:
        return {"error": "Memory not available"}
    result = {}
    for key, label, tier in WORKFORCE_ROSTER:
        acc = mem.get_skill_accumulation(key)
        result[key] = {
            "label": label, "tier": tier,
            "total_items":  acc["total_items"],
            "total_chunks": acc["total_chunks"],
            "domains":      acc["domains"],
            "last":         acc["last"],
        }
    return {"skills": result}


@app.post("/api/agents/skills-profile")
async def trigger_skills_profile(background_tasks: BackgroundTasks):
    """Regenerate all agent skill/KB profile .md files."""
    background_tasks.add_task(run_agent, "skills_profile", "skills_profile.py")
    return {"status": "started", "agent": "skills_profile"}


@app.get("/api/hr/learning")
def hr_learning(days: int = 7):
    if not mem:
        return {"error": "Memory not available"}
    return {"stats": mem.get_learning_stats(days=days)}


@app.post("/api/agents/hr")
async def trigger_hr(background_tasks: BackgroundTasks):
    # Block HR review if any learning agent is currently running
    if "agent_learning" in running_agents:
        return JSONResponse(status_code=409,
            content={"error": "Learning in progress — wait for it to complete before running HR Review",
                     "blocked_by": "agent_learning"})
    # Also block if HR is already running (prevents double-click double-run)
    if "hr_agent" in running_agents:
        return JSONResponse(status_code=409,
            content={"error": "HR Review is already running", "blocked_by": "hr_agent"})
    background_tasks.add_task(run_agent, "hr_agent", "hr_agent.py")
    return {"status": "started", "agent": "hr_agent"}


@app.post("/api/agents/learn")
async def trigger_learning(request: Request, background_tasks: BackgroundTasks):
    body   = await request.json()
    agent  = body.get("agent", "")
    args   = ["--agent", agent] if agent else []
    background_tasks.add_task(run_agent, "agent_learning", "agent_learning.py", args)
    return {"status": "started", "agent": "agent_learning", "target": agent or "all"}


@app.post("/api/agents/run-all")
async def trigger_run_all(background_tasks: BackgroundTasks):
    """Run all standard agents in parallel (briefing, content, RAG, consulting, M&A, ISO)."""
    batch = [
        ("briefing_agent",        "briefing_agent.py",        []),
        ("content_agent",         "content_agent.py",         []),
        ("rag_agent",             "rag_agent.py",             []),
        ("consulting_agent",      "consulting_agent.py",      []),
        ("ma_intelligence_agent", "ma_intelligence_agent.py", []),
        ("iso_coach",             "iso_coach_agent.py",       ["--next"]),
    ]
    for name, script, args in batch:
        background_tasks.add_task(run_agent, name, script, args)
    return {"status": "started", "agents": [b[0] for b in batch]}


@app.post("/api/agents/consulting")
async def trigger_consulting(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    mode = body.get("mode", "learn")   # "learn" | "report"
    args = ["--generate", "report"] if mode == "report" else []
    background_tasks.add_task(run_agent, "consulting_agent", "consulting_agent.py", args)
    return {"status": "started", "agent": "consulting_agent", "mode": mode}


@app.post("/api/agents/marketing")
async def trigger_marketing(request: Request, background_tasks: BackgroundTasks):
    body   = await request.json()
    mode   = body.get("mode", "brief")   # "brief" | "plan" | "events" | "scorecard" | "learn"
    target = body.get("target", "")
    if mode == "plan":
        args = ["--plan"]
    elif mode == "events":
        args = ["--events"]
    elif mode == "scorecard":
        args = ["--scorecard"]
    elif mode == "learn":
        args = ["learn"]
    elif mode == "outreach" and target:
        args = ["--outreach", _safe_arg(target)]
    else:
        args = []  # default: brief
    background_tasks.add_task(run_agent, "marketing_agent", "marketing_agent.py", args)
    return {"status": "started", "agent": "marketing_agent", "mode": mode}


@app.get("/api/marketing/pipeline")
def get_marketing_pipeline():
    """Return pipeline summary counts and high-priority next actions."""
    import sqlite3 as _sq
    db = ATHENA / "ops" / "marketing" / "pipeline.db"
    if not db.exists():
        return {"summary": [], "actions": [], "kpis": {}}
    with _sq.connect(db) as conn:
        conn.row_factory = _sq.Row
        summary = [dict(r) for r in conn.execute(
            "SELECT type, status, COUNT(*) as count FROM targets GROUP BY type, status ORDER BY type, status"
        ).fetchall()]
        actions = [dict(r) for r in conn.execute(
            "SELECT name, type, org, status, next_action, next_date FROM targets "
            "WHERE priority = 1 AND status NOT IN ('converted','closed') "
            "ORDER BY CASE WHEN next_date IS NULL THEN '9999' ELSE next_date END LIMIT 10"
        ).fetchall()]
        row = conn.execute(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN status!='identified' THEN 1 ELSE 0 END) as contacted, "
            "SUM(CASE WHEN status='in_discussion' THEN 1 ELSE 0 END) as meetings, "
            "SUM(CASE WHEN status='converted' THEN 1 ELSE 0 END) as converted "
            "FROM targets"
        ).fetchone()
        kpis = dict(row) if row else {}
    return {"summary": summary, "actions": actions, "kpis": kpis}


@app.post("/api/marketing/pipeline/update")
async def update_pipeline_target(request: Request):
    """Update a target's status from the UI."""
    import sqlite3 as _sq
    body   = await request.json()
    name   = _safe_arg(body.get("name", ""))
    status = _safe_arg(body.get("status", ""))
    note   = _safe_arg(body.get("note", ""))
    VALID  = {"identified", "contacted", "in_discussion", "converted", "closed"}
    if not name or status not in VALID:
        raise HTTPException(status_code=400, detail="Invalid name or status")
    db = ATHENA / "ops" / "marketing" / "pipeline.db"
    if not db.exists():
        raise HTTPException(status_code=404)
    with _sq.connect(db) as conn:
        conn.execute(
            "UPDATE targets SET status=?, notes=COALESCE(notes,'')||'\n'||?, updated_at=date('now') WHERE name LIKE ?",
            (status, f"[{datetime.now().strftime('%Y-%m-%d')}] {note}", f"%{name}%")
        )
        conn.commit()
    return {"status": "updated", "target": name}


@app.get("/api/marketing/outputs")
def list_marketing_outputs():
    """List all generated marketing output files."""
    mdir = ATHENA / "ops" / "marketing"
    if not mdir.exists():
        return {"files": []}
    files = []
    for f in sorted(mdir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
        files.append({"filename": f.name, "label": f.stem.replace("_", " ").title(),
                      "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")})
    out_dir = mdir / "outreach"
    if out_dir.exists():
        for f in sorted(out_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
            files.append({"filename": f"outreach/{f.name}",
                          "label": f.stem.replace("_outreach_", " → ").replace("_", " ").title(),
                          "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")})
    return {"files": files}


@app.get("/api/marketing/outputs/{filename:path}")
def get_marketing_output(filename: str):
    """Read a specific marketing output file."""
    parts = Path(filename).parts
    if ".." in parts or len(parts) > 2:
        raise HTTPException(status_code=400, detail="Invalid path")
    path = ATHENA / "ops" / "marketing" / filename
    if not path.exists() or path.suffix != ".md":
        raise HTTPException(status_code=404)
    return {"content": path.read_text(encoding="utf-8"), "filename": filename}


@app.post("/api/agents/ma")
async def trigger_ma(request: Request, background_tasks: BackgroundTasks):
    body  = await request.json()
    mode  = body.get("mode", "learn")   # "learn" | "analyse" | "historical"
    topic = body.get("topic", "")
    if mode == "analyse":
        args = ["--analyse"] + (["--topic", topic] if topic else [])
    elif mode == "historical":
        args = ["--historical"]
    else:
        args = []
    background_tasks.add_task(run_agent, "ma_intelligence_agent", "ma_intelligence_agent.py", args)
    return {"status": "started", "agent": "ma_intelligence_agent", "mode": mode}


# ── Agent triggers ────────────────────────────────────────────────────────────

@app.post("/api/agents/rag")
async def trigger_rag(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    args = ["--override", _safe_arg(body["override"])] if body.get("override") else []
    background_tasks.add_task(run_agent, "rag_agent", "rag_agent.py", args)
    return {"status": "started", "agent": "rag_agent"}


@app.post("/api/agents/briefing")
async def trigger_briefing(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    args = ["--override", _safe_arg(body["override"])] if body.get("override") else []
    background_tasks.add_task(run_agent, "briefing_agent", "briefing_agent.py", args)
    return {"status": "started", "agent": "briefing_agent"}


@app.post("/api/agents/content")
async def trigger_content(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    args = ["--override", _safe_arg(body["override"])] if body.get("override") else []
    background_tasks.add_task(run_agent, "content_agent", "content_agent.py", args)
    return {"status": "started", "agent": "content_agent"}


class BriefRequest(BaseModel):
    client: str

@app.post("/api/agents/brief")
async def trigger_brief(req: BriefRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_agent, "coaching_brief", "coaching_brief.py", [req.client])
    return {"status": "started", "agent": "coaching_brief", "client": req.client}


# ── LangGraph coaching orchestration (Phase 1A) ──────────────────────────────
async def _run_coaching_workflow(client: str):
    """Run the coaching graph to the human gate, streaming progress to the UI."""
    await manager.broadcast({"type": "agent_start", "agent": "orchestrator",
                             "ts": datetime.now().isoformat()})
    try:
        result = await asyncio.to_thread(_orchestrator().start_coaching, client)
        for step in result.get("steps", []):
            await manager.broadcast({"type": "agent_log", "agent": "orchestrator", "line": step})
        await manager.broadcast({"type": "agent_log", "agent": "orchestrator",
                                 "line": f"[HUMAN GATE] Review #{result.get('review_id')} "
                                         f"awaiting Steven's approval (thread {result['thread_id']})"})
        await manager.broadcast({"type": "agent_done", "agent": "orchestrator",
                                 "status": "awaiting_review", "ts": datetime.now().isoformat()})
    except Exception as e:
        await manager.broadcast({"type": "agent_log", "agent": "orchestrator", "line": f"[ERROR] {e}"})
        await manager.broadcast({"type": "agent_done", "agent": "orchestrator",
                                 "status": "error", "ts": datetime.now().isoformat()})

@app.post("/api/orchestrate/coaching")
async def orchestrate_coaching(req: BriefRequest, background_tasks: BackgroundTasks):
    """Run the full coaching workflow (brief -> human gate -> finalize) via LangGraph."""
    background_tasks.add_task(_run_coaching_workflow, req.client)
    return {"status": "started", "workflow": "coaching", "client": req.client}


class ISORequest(BaseModel):
    clause: Optional[str] = None

@app.post("/api/agents/iso")
async def trigger_iso(req: ISORequest, background_tasks: BackgroundTasks):
    # Blank clause = generate the next ungenerated clause (never ALL)
    args = ["--clause", req.clause] if req.clause else ["--next"]
    background_tasks.add_task(run_agent, "iso_coach", "iso_coach_agent.py", args)
    return {"status": "started", "agent": "iso_coach"}


# ── Document generation ───────────────────────────────────────────────────────

class DocRequest(BaseModel):
    title:    str
    content:  str
    doc_type: str = "article"  # article | brief | report | sop


@app.post("/api/documents/generate")
async def generate_document(req: DocRequest):
    """Generate a branded .docx from content."""
    try:
        out_path = await asyncio.get_event_loop().run_in_executor(
            None, generate_docx, req.title, req.content, req.doc_type
        )
        return {"status": "ok", "path": str(out_path), "filename": out_path.name}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── Figure embedding (Markdown ![alt](path) inside document content) ──────────
FIGURES_DIR      = ATHENA / "documents" / "figures"
MAX_FIG_WIDTH_IN = 6.1   # Letter (8.5in) minus 1.2in margins on each side


def _resolve_figure(src: str) -> Optional[Path]:
    """Resolve a figure referenced by ![alt](src). Tries absolute, the figures
    dir, Athena-relative, then cwd. Returns None if nothing exists."""
    cand = Path(src)
    candidates = [cand] if cand.is_absolute() else [
        FIGURES_DIR / src, ATHENA / "documents" / src, ATHENA / src, Path.cwd() / src,
    ]
    for c in candidates:
        try:
            if c.is_file():
                return c
        except OSError:
            continue
    return None


def generate_docx(title: str, content: str, doc_type: str) -> Path:
    """Generate branded .docx using python-docx.

    Content is Markdown. Supported block constructs:
      ``# / ## / ###``     headings
      ``- `` / ``* ``      bullets
      ``**text**``         bold (line or inline)
      ``---``              horizontal rule
      ``![caption](path)`` figure (chart/diagram), centered, width-constrained,
                           caption beneath. Render charts with
                           ``figures.bar_chart(...)`` and reference the path.
      ``> text``           callout / pull-stat box (shaded, left accent bar);
                           consecutive ``>`` lines merge into one box.
      ``| a | b |``        pipe table; a ``|---|`` separator row marks a header.
    """
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor, Inches, Cm
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.style import WD_STYLE_TYPE
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
        import re
    except ImportError:
        raise ImportError("python-docx not installed. Run: pip install python-docx")

    # Latitude MedTech colors
    LM_BLACK = RGBColor(0x1A, 0x1A, 0x1A)
    LM_SLATE = RGBColor(0x2C, 0x3E, 0x50)
    LM_BLUE  = RGBColor(0x5B, 0x7F, 0xA6)
    LM_MUTED = RGBColor(0x8A, 0x86, 0x80)
    LM_WHITE = RGBColor(0xFF, 0xFF, 0xFF)

    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin    = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin   = Inches(1.2)
        section.right_margin  = Inches(1.2)

    # Default font
    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(10.5)
    doc.styles['Normal'].font.color.rgb = LM_SLATE

    # ── Header ────────────────────────────────────────────────────────────────
    header = doc.sections[0].header
    header.paragraphs[0].clear()
    run = header.paragraphs[0].add_run("LATITUDE MEDTECH LLC")
    run.font.name  = 'Calibri'
    run.font.size  = Pt(7.5)
    run.font.color.rgb = LM_BLUE
    run.font.bold  = True
    header.paragraphs[0].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # ── Footer ────────────────────────────────────────────────────────────────
    footer = doc.sections[0].footer
    footer.paragraphs[0].clear()
    run = footer.paragraphs[0].add_run(
        f"Latitude MedTech LLC  ·  San Diego, CA  ·  latitudemedtech.com  ·  "
        f"Generated {datetime.now().strftime('%B %d, %Y')}  ·  "
        "Educational purposes only — not regulatory advice"
    )
    run.font.name  = 'Calibri'
    run.font.size  = Pt(7)
    run.font.color.rgb = LM_MUTED
    footer.paragraphs[0].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # ── Title block ───────────────────────────────────────────────────────────
    title_para = doc.add_paragraph()
    title_para.paragraph_format.space_before = Pt(0)
    title_para.paragraph_format.space_after  = Pt(6)
    title_run = title_para.add_run(title.upper())
    title_run.font.name  = 'Calibri'
    title_run.font.size  = Pt(18)
    title_run.font.bold  = True
    title_run.font.color.rgb = LM_BLACK
    title_para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # Accent line under title
    meta_para = doc.add_paragraph()
    meta_run  = meta_para.add_run(
        f"Latitude MedTech LLC  ·  {doc_type.title()}  ·  "
        f"{datetime.now().strftime('%B %d, %Y')}"
    )
    meta_run.font.name  = 'Calibri'
    meta_run.font.size  = Pt(8.5)
    meta_run.font.color.rgb = LM_BLUE
    meta_para.paragraph_format.space_after = Pt(18)

    # ── Content ───────────────────────────────────────────────────────────────
    def emit_runs(p, text):
        """Add runs to paragraph p, honoring inline **bold**."""
        for j, part in enumerate(re.split(r'\*\*(.+?)\*\*', text)):
            if not part:
                continue
            r = p.add_run(part)
            r.font.name = 'Calibri'; r.font.size = Pt(10.5)
            if j % 2 == 1:
                r.font.bold = True

    def emit_callout(text_lines):
        """Shaded pull-stat / callout box with a left accent bar (from > lines)."""
        p = doc.add_paragraph()
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')
        for edge, sz, col in (('left', '20', '5B7FA6'), ('top', '4', 'D9E1EA'),
                              ('bottom', '4', 'D9E1EA'), ('right', '4', 'D9E1EA')):
            e = OxmlElement('w:' + edge)
            e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), sz)
            e.set(qn('w:space'), '8');    e.set(qn('w:color'), col)
            pBdr.append(e)
        pPr.append(pBdr)
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear'); shd.set(qn('w:fill'), 'EFF3F7')
        pPr.append(shd)
        pf = p.paragraph_format
        pf.left_indent = Inches(0.14); pf.right_indent = Inches(0.10)
        pf.space_before = Pt(8);       pf.space_after = Pt(10)
        for k, t in enumerate(text_lines):
            if k:
                p.add_run().add_break()
            emit_runs(p, t)

    def shade_cell(cell, fill):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear'); shd.set(qn('w:fill'), fill)
        tcPr.append(shd)

    def set_table_borders(table):
        tblPr = table._tbl.tblPr
        borders = OxmlElement('w:tblBorders')
        for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            e = OxmlElement('w:' + edge)
            e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '4')
            e.set(qn('w:space'), '0');    e.set(qn('w:color'), 'CCCCCC')
            borders.append(e)
        ref = tblPr.find(qn('w:tblLook'))
        if ref is None:
            ref = tblPr.find(qn('w:tblCellMar'))
        if ref is not None:
            ref.addprevious(borders)
        else:
            tblPr.append(borders)

    def emit_table(block):
        """Render a Markdown pipe table; a |---| separator row marks a header."""
        grid = [[c.strip() for c in row.strip().strip('|').split('|')] for row in block]
        is_sep = lambda cells: all(set(c) <= set('-: ') and '-' in c
                                   for c in cells if c != '')
        has_header = len(grid) >= 2 and is_sep(grid[1])
        body = ([grid[0]] + grid[2:]) if has_header else grid
        ncols = max(len(r) for r in body)
        table = doc.add_table(rows=0, cols=ncols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.allow_autofit = False
        set_table_borders(table)
        col_w = Inches(MAX_FIG_WIDTH_IN / ncols)
        for ri, row in enumerate(body):
            cells = table.add_row().cells
            for ci in range(ncols):
                cell = cells[ci]; cell.width = col_w
                para = cell.paragraphs[0]
                para.paragraph_format.space_after = Pt(2)
                text = row[ci] if ci < len(row) else ''
                if has_header and ri == 0:
                    shade_cell(cell, '5B7FA6')
                    r = para.add_run(re.sub(r'\*\*(.+?)\*\*', r'\1', text))
                    r.font.name = 'Calibri'; r.font.size = Pt(10)
                    r.font.bold = True;      r.font.color.rgb = LM_WHITE
                else:
                    if has_header and ri % 2 == 0:
                        shade_cell(cell, 'F2F5F8')
                    emit_runs(para, text)
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    lines = content.splitlines()
    n    = len(lines)
    idx  = 0
    while idx < n:
        line = lines[idx].strip()

        if not line:
            doc.add_paragraph()
            idx += 1
            continue

        # Pipe table — consume the contiguous block of | … | lines
        if line.startswith('|'):
            block = []
            while idx < n and lines[idx].strip().startswith('|'):
                block.append(lines[idx].strip())
                idx += 1
            emit_table(block)
            continue

        # Callout / pull-stat — consume contiguous > lines
        if line.startswith('>'):
            quote = []
            while idx < n and lines[idx].strip().startswith('>'):
                quote.append(lines[idx].strip()[1:].strip())
                idx += 1
            emit_callout(quote)
            continue

        # H1
        if line.startswith('# '):
            p    = doc.add_heading(line[2:], level=1)
            p.runs[0].font.color.rgb = LM_BLACK
            p.runs[0].font.name = 'Calibri'
            idx += 1; continue

        # H2
        if line.startswith('## '):
            p    = doc.add_heading(line[3:], level=2)
            p.runs[0].font.color.rgb = LM_BLUE
            p.runs[0].font.name = 'Calibri'
            idx += 1; continue

        # H3
        if line.startswith('### '):
            p    = doc.add_heading(line[4:], level=3)
            p.runs[0].font.color.rgb = LM_SLATE
            p.runs[0].font.name = 'Calibri'
            idx += 1; continue

        # Bullet (inline bold supported)
        if line.startswith('- ') or line.startswith('* '):
            p = doc.add_paragraph(style='List Bullet')
            emit_runs(p, line[2:])
            idx += 1; continue

        # Whole-line bold paragraph (single bold span only)
        if line.startswith('**') and line.endswith('**') and line.count('**') == 2:
            p   = doc.add_paragraph()
            run = p.add_run(line[2:-2])
            run.font.bold = True
            run.font.name = 'Calibri'
            run.font.size = Pt(10.5)
            idx += 1; continue

        # Horizontal rule
        if line.startswith('---'):
            p = doc.add_paragraph()
            pPr = p._p.get_or_add_pPr()
            pBdr = OxmlElement('w:pBdr')
            bottom = OxmlElement('w:bottom')
            bottom.set(qn('w:val'), 'single')
            bottom.set(qn('w:sz'), '4')
            bottom.set(qn('w:space'), '1')
            bottom.set(qn('w:color'), '5B7FA6')
            pBdr.append(bottom)
            pPr.append(pBdr)
            idx += 1; continue

        # Figure — ![caption](path) on its own line
        img = re.match(r'^!\[(.*?)\]\((.+?)\)\s*$', line)
        if img:
            alt, src = img.group(1).strip(), img.group(2).strip()
            fig_path = _resolve_figure(src)
            if fig_path is None:
                miss = doc.add_paragraph()
                mrun = miss.add_run(f"[missing figure: {src}]")
                mrun.font.name = 'Calibri'; mrun.font.size = Pt(9)
                mrun.font.italic = True;    mrun.font.color.rgb = LM_MUTED
                idx += 1; continue
            # Constrain to content width; never upscale a smaller image
            width_in = MAX_FIG_WIDTH_IN
            try:
                from PIL import Image as _PILImage
                with _PILImage.open(fig_path) as im:
                    width_in = min(MAX_FIG_WIDTH_IN, im.width / 96.0)
            except Exception:
                pass
            doc.add_picture(str(fig_path), width=Inches(width_in))
            pic = doc.paragraphs[-1]
            pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pic.paragraph_format.space_before = Pt(6)
            pic.paragraph_format.space_after  = Pt(2)
            if alt:
                cap = doc.add_paragraph()
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                cap.paragraph_format.space_after = Pt(10)
                crun = cap.add_run(alt)
                crun.font.name = 'Calibri'; crun.font.size = Pt(8.5)
                crun.font.italic = True;    crun.font.color.rgb = LM_MUTED
            idx += 1; continue

        # Normal paragraph — inline bold
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        emit_runs(p, line)
        idx += 1

    # ── Disclaimer ────────────────────────────────────────────────────────────
    doc.add_paragraph()
    disc = doc.add_paragraph()
    disc.paragraph_format.space_before = Pt(12)
    disc_run = disc.add_run(
        "DISCLAIMER: This document is produced by Latitude MedTech LLC for educational and planning purposes only. "
        "Nothing herein constitutes formal regulatory, legal, or compliance advice. "
        "Always defer to official regulations and guidance from the FDA, ISO, EU Commission, "
        "and applicable regulatory bodies."
    )
    disc_run.font.name   = 'Calibri'
    disc_run.font.size   = Pt(8)
    disc_run.font.italic = True
    disc_run.font.color.rgb = LM_MUTED

    # ── Save ──────────────────────────────────────────────────────────────────
    out_dir  = ATHENA / 'documents'
    out_dir.mkdir(exist_ok=True)
    slug     = re.sub(r'[^a-z0-9]+', '_', title.lower())[:50]
    out_path = out_dir / f"{datetime.now().strftime('%Y-%m-%d')}_{slug}.docx"
    doc.save(str(out_path))
    return out_path


@app.get("/api/documents")
def list_documents():
    docs_dir = ATHENA / 'documents'
    if not docs_dir.exists():
        return {"documents": []}
    files = sorted(docs_dir.glob('*.docx'), key=lambda f: f.stat().st_mtime, reverse=True)
    return {"documents": [
        {"filename": f.name, "path": str(f), "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()}
        for f in files[:20]
    ]}


@app.get("/api/documents/open/{filename}")
def open_document(filename: str):
    docs_dir = ATHENA / 'documents'
    f = docs_dir / filename
    if not f.exists():
        return JSONResponse(status_code=404, content={"error": "Not found"})
    subprocess.Popen(['start', '', str(f)], shell=True)
    return {"status": "opened", "filename": filename}


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    global _goodbye_task
    # Cancel any pending goodbye — client is reconnecting (e.g. page refresh).
    if _goodbye_task and not _goodbye_task.done():
        _goodbye_task.cancel()
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
        if not manager.active and not _shutting_down:
            _goodbye_task = asyncio.get_event_loop().create_task(_ws_goodbye())


@app.websocket("/ws/voice")
async def voice_ws_endpoint(ws: WebSocket):
    if VOICE_AVAILABLE:
        await voice_websocket_endpoint(ws)
    else:
        await ws.accept()
        await ws.send_json({"type": "voice_error", "message": "Voice bridge not available"})
        await ws.close()




# ── Settings routes ───────────────────────────────────────────────────────────

sys.path.insert(0, str(AGENTS_DIR))
try:
    from settings_manager import settings as agent_settings
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False


@app.get("/api/settings")
def get_settings():
    if not SETTINGS_AVAILABLE:
        return JSONResponse(status_code=503, content={"error": "settings_manager.py not found in agents folder"})
    return agent_settings.get_all()


@app.post("/api/settings")
async def update_settings(request: Request):
    if not SETTINGS_AVAILABLE:
        return JSONResponse(status_code=503, content={"error": "settings_manager not available"})
    try:
        body = await request.json()
        for key_path, value in body.items():
            agent_settings.set(key_path, value)
        return {"status": "saved", "updated_at": datetime.now().isoformat()}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/settings/prompt/{agent_name}")
async def update_prompt(agent_name: str, request: Request):
    if not SETTINGS_AVAILABLE:
        return JSONResponse(status_code=503, content={"error": "settings_manager not available"})
    try:
        body  = await request.json()
        prompt = body.get("prompt", "")
        agent_settings.set_prompt(agent_name, prompt)
        return {"status": "saved", "agent": agent_name}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/settings/reset")
def reset_settings():
    if not SETTINGS_AVAILABLE:
        return JSONResponse(status_code=503, content={"error": "settings_manager not available"})
    agent_settings.reset_to_defaults()
    return {"status": "reset"}


# ── File management routes ────────────────────────────────────────────────────

_HOME_ATHENA = ATHENA   # canonical code-tree root; agents write here
FOLDER_MAP = {
    "briefings":       _HOME_ATHENA / "briefings",
    "content/drafts":  _HOME_ATHENA / "content" / "drafts",
    "coaching/briefs": _HOME_ATHENA / "coaching" / "briefs",
    "documents":       _HOME_ATHENA / "documents",
    "iso13485":        _HOME_ATHENA / "coaching" / "iso13485",
    "learning":        _HOME_ATHENA / "knowledge_base" / "learning",
    "hr":              _HOME_ATHENA / "ops" / "hr",
    "consulting":      _HOME_ATHENA / "ops" / "consulting",
    "ma_intelligence": _HOME_ATHENA / "ops" / "ma_intelligence",
}


@app.post("/api/files/delete")
async def delete_file(request: Request):
    try:
        body     = await request.json()
        folder   = body.get("folder", "")
        filename = body.get("filename", "")
        base     = FOLDER_MAP.get(folder)
        if not base:
            print(f"DELETE ERROR: Unknown folder '{folder}'. Known: {list(FOLDER_MAP.keys())}")
            return JSONResponse(status_code=400, content={"error": f"Unknown folder: {folder}"})
        f = base / filename
        print(f"DELETE: {f} exists={f.exists()}")
        if f.exists():
            f.unlink()
            return {"status": "deleted", "filename": filename}
        # Try searching all folders
        for fname, fbase in FOLDER_MAP.items():
            candidate = fbase / filename
            if candidate.exists():
                candidate.unlink()
                return {"status": "deleted", "filename": filename, "found_in": fname}
        return JSONResponse(status_code=404, content={"error": f"File not found: {filename} in {base}"})
    except Exception as e:
        print(f"DELETE EXCEPTION: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/files/delete-bulk")
async def delete_files_bulk(request: Request):
    try:
        body  = await request.json()
        items = body.get("items", [])   # [{folder, filename}, ...]
        deleted, failed = [], []
        for item in items:
            folder   = item.get("folder", "")
            filename = item.get("filename", "")
            base     = FOLDER_MAP.get(folder)
            deleted_this = False
            if base:
                f = base / filename
                if f.exists():
                    f.unlink()
                    deleted.append(filename)
                    deleted_this = True
            if not deleted_this:
                # Search all folders
                for fbase in FOLDER_MAP.values():
                    candidate = fbase / filename
                    if candidate.exists():
                        candidate.unlink()
                        deleted.append(filename)
                        deleted_this = True
                        break
            if not deleted_this:
                failed.append(filename)
        return {"deleted": deleted, "failed": failed, "count": len(deleted)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/files/save")
async def save_file(request: Request):
    try:
        body     = await request.json()
        filename = body.get("filename", "")
        content  = body.get("content", "")
        for folder, base in FOLDER_MAP.items():
            f = base / filename
            if f.exists():
                f.write_text(content, encoding="utf-8")
                return {"status": "saved", "filename": filename}
        return JSONResponse(status_code=404, content={"error": f"File not found in any folder: {filename}"})
    except Exception as e:
        print(f"SAVE EXCEPTION: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/coaching/briefs")
def list_briefs():
    briefs_dir = _HOME_ATHENA / "coaching" / "briefs"
    if not briefs_dir.exists():
        return {"briefs": []}
    files = sorted(briefs_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    return {"briefs": [
        {"filename": f.name, "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()}
        for f in files[:20]
    ]}


@app.get("/api/coaching/briefs/{filename}")
def get_brief(filename: str):
    briefs_dir = _HOME_ATHENA / "coaching" / "briefs"
    f = briefs_dir / filename
    if not f.exists():
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return {"filename": filename, "content": f.read_text(encoding="utf-8", errors="replace")}


# ── ISO 13485 coach content ───────────────────────────────────────────────────

@app.get("/api/iso/lessons")
def list_iso_lessons():
    iso_dir = _HOME_ATHENA / "coaching" / "iso13485"
    if not iso_dir.exists():
        return {"lessons": []}
    files = sorted(iso_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    def _parse_iso_stem(stem: str):
        # stem like: clause_4_1_general_qms_requirements
        # → clause "4.1", title "General QMS Requirements"
        parts = stem.split("_")
        # skip leading "clause" word
        start = 1 if parts and parts[0].lower() == "clause" else 0
        parts = parts[start:]
        num_parts, word_parts = [], []
        for p in parts:
            if p.replace(".", "").isdigit():
                num_parts.append(p)
            else:
                word_parts.append(p)
        clause = ".".join(num_parts) if num_parts else stem
        title  = " ".join(w.capitalize() for w in word_parts) if word_parts else clause
        return clause, title

    return {"lessons": [
        {
            "filename": f.name,
            "clause":   _parse_iso_stem(f.stem)[0],
            "title":    _parse_iso_stem(f.stem)[1],
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
        }
        for f in files[:50]
    ]}


@app.get("/api/iso/lessons/{filename}")
def get_iso_lesson(filename: str):
    iso_dir = _HOME_ATHENA / "coaching" / "iso13485"
    f = iso_dir / filename
    if not f.exists():
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return {"filename": filename, "content": f.read_text(encoding="utf-8", errors="replace")}


# ── File serve (for in-browser viewer) ───────────────────────────────────────

from fastapi.responses import Response as FResponse

@app.get("/api/files/serve/{folder}/{filename}")
def serve_file(folder: str, filename: str):
    """Serve raw file bytes for in-browser viewing (PDF / DOCX / MD)."""
    _safe_filename(filename)                        # raises 400 on traversal
    base = FOLDER_MAP.get(folder)
    if not base:
        return JSONResponse(status_code=400, content={"error": "Unknown folder"})
    f = (base / filename).resolve()
    # Confirm resolved path is still inside the expected base directory
    if not str(f).startswith(str(base.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    if not f.exists():
        return JSONResponse(status_code=404, content={"error": "Not found"})
    suffix = f.suffix.lower()
    mime = {
        ".pdf":  "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".md":   "text/plain; charset=utf-8",
        ".txt":  "text/plain; charset=utf-8",
    }.get(suffix, "application/octet-stream")
    return FResponse(content=f.read_bytes(), media_type=mime,
                     headers={"Content-Disposition": f'inline; filename="{filename}"'})


# ── Human Review Queue (Phase 1A) ────────────────────────────────────────────

@app.get("/api/review/pending")
def review_pending():
    if not mem: return {"items": []}
    return {"items": mem.get_pending_reviews(), "stats": mem.get_review_stats()}

async def _resume_workflow(item_id: int, decision: str, notes: str):
    """If the reviewed item belongs to a paused workflow, resume it."""
    if not mem:
        return
    row = mem.get_review(item_id)
    thread_id = row.get("thread_id") if row else None
    if not thread_id:
        return  # standalone item (e.g. legacy subprocess brief) — nothing to resume
    try:
        result = await asyncio.to_thread(_orchestrator().resume_coaching, thread_id, decision, notes)
        for step in result.get("steps", []):
            await manager.broadcast({"type": "agent_log", "agent": "orchestrator", "line": step})
        await manager.broadcast({"type": "agent_done", "agent": "orchestrator",
                                 "status": result.get("status"), "ts": datetime.now().isoformat()})
    except Exception as e:
        await manager.broadcast({"type": "agent_log", "agent": "orchestrator",
                                 "line": f"[ERROR] resume failed: {e}"})

@app.post("/api/review/{item_id}/approve")
async def review_approve(item_id: int, request: Request):
    body  = await request.json()
    notes = body.get("notes", "")
    if mem: mem.approve_review(item_id, notes)
    await _resume_workflow(item_id, "approved", notes)
    return {"status": "approved", "id": item_id}

@app.post("/api/review/{item_id}/reject")
async def review_reject(item_id: int, request: Request):
    body  = await request.json()
    notes = body.get("notes", "")
    if mem: mem.reject_review(item_id, notes)
    await _resume_workflow(item_id, "rejected", notes)
    return {"status": "rejected", "id": item_id}


def _resolve_review_file(item_id: int):
    """Locate the file backing a review item by its stored path, falling back
    to a filename search across the known folders if the absolute path moved."""
    if not mem:
        return None
    row = mem.get_review(item_id)
    if not row or not row.get("file_path"):
        return None
    f = Path(row["file_path"])
    if f.exists():
        return f
    for base in FOLDER_MAP.values():
        cand = base / f.name
        if cand.exists():
            return cand
    return None


@app.get("/api/review/{item_id}/content")
def review_content(item_id: int):
    """Return the text of a review item so it can be opened/read in-queue.
    Markdown/text is returned inline; binary docs point the client at /serve."""
    f = _resolve_review_file(item_id)
    if not f:
        return JSONResponse(status_code=404, content={"error": "File not found for this review item"})
    ext = f.suffix.lower().lstrip(".")
    if ext in ("md", "txt"):
        return {"filename": f.name, "ext": ext,
                "content": f.read_text(encoding="utf-8", errors="replace")}
    return {"filename": f.name, "ext": ext, "content": None}   # docx/pdf → use /serve


@app.get("/api/review/{item_id}/serve")
def review_serve(item_id: int):
    """Serve raw bytes of a review item's file (for docx/pdf in-browser viewing)."""
    f = _resolve_review_file(item_id)
    if not f:
        return JSONResponse(status_code=404, content={"error": "File not found"})
    suffix = f.suffix.lower()
    mime = {
        ".pdf":  "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".md":   "text/plain; charset=utf-8",
        ".txt":  "text/plain; charset=utf-8",
    }.get(suffix, "application/octet-stream")
    return FResponse(content=f.read_bytes(), media_type=mime,
                     headers={"Content-Disposition": f'inline; filename="{f.name}"'})


def _split_frontmatter(text: str):
    """Return (frontmatter_block_including_fences, body). Empty fm if none."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            nl = text.find("\n", end + 1)
            if nl != -1:
                return text[:nl + 1], text[nl + 1:]
    return "", text


def _ai_edit_document(body: str, instruction: str) -> str:
    """Revise a Markdown document per a reviewer instruction, at consulting
    quality, returning the full revised Markdown body (no preamble)."""
    import anthropic
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")
    client = anthropic.Anthropic(api_key=key)
    system = (
        "You are a senior editor at a Big 4-calibre MedTech/Pharma consulting firm "
        "(Latitude MedTech). Revise the document per the reviewer's instruction while "
        "preserving its Markdown structure and factual claims. Keep the house style: "
        "specific citations (21 CFR §, ISO clause, company, dollar figure), no filler "
        "phrases ('it is important to note', 'leverage', 'robust', 'in conclusion'), "
        "concrete opening sentence. Return ONLY the full revised Markdown document — "
        "no commentary, no code fences, no preamble."
    )
    resp = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=4000, system=system,
        messages=[{"role": "user",
                   "content": f"Reviewer instruction:\n{instruction}\n\n"
                              f"---\nDocument to revise:\n\n{body}"}],
    )
    return resp.content[0].text.strip()


class ReviewEditRequest(BaseModel):
    instruction: str


@app.post("/api/review/{item_id}/edit")
async def review_edit(item_id: int, req: ReviewEditRequest):
    """Apply an AI edit to a review item's document from a reviewer prompt.
    Writes the revised content back to the same file and returns it."""
    if not req.instruction.strip():
        return JSONResponse(status_code=400, content={"error": "Instruction is empty"})
    f = _resolve_review_file(item_id)
    if not f:
        return JSONResponse(status_code=404, content={"error": "File not found for this item"})
    if f.suffix.lower() not in (".md", ".txt"):
        return JSONResponse(status_code=400,
            content={"error": f"Only markdown/text documents are editable (got {f.suffix})"})
    try:
        original    = f.read_text(encoding="utf-8", errors="replace")
        fm, body    = _split_frontmatter(original)
        revised     = await asyncio.to_thread(_ai_edit_document, body, req.instruction)
        new_content = (fm + "\n" + revised) if fm else revised
        f.write_text(new_content, encoding="utf-8")
        if mem:
            mem.log_event("human_review", "ai_edit",
                          subject=f.name, metadata={"item_id": item_id})
        return {"status": "edited", "filename": f.name,
                "ext": f.suffix.lower().lstrip("."), "content": new_content}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/dashboard/knowledge-growth")
def knowledge_growth(days: int = 90):
    """Cumulative knowledge accumulation over time — every ingested KB document
    and every learning item, counted per day and accumulated. Powers the
    Workforce 'Knowledge Growth' chart."""
    if not mem:
        return {"daily": [], "total": 0}
    rows = mem.conn.execute(
        """SELECT substr(ts,1,10) AS date, COUNT(*) AS n FROM (
               SELECT timestamp AS ts FROM knowledge_items
               UNION ALL
               SELECT timestamp AS ts FROM agent_learning
           ) WHERE ts IS NOT NULL
           GROUP BY date ORDER BY date ASC"""
    ).fetchall()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    cum, out = 0, []
    for r in rows:
        cum += r["n"]
        if r["date"] >= cutoff:
            out.append({"date": r["date"], "items": r["n"], "cumulative": cum})
    # If the window opens mid-history, seed the first point with the running
    # total so the curve starts at the true accumulated height, not zero.
    return {"daily": out, "total": cum}


# ── Token history for dashboard charts ───────────────────────────────────────

@app.get("/api/dashboard/history")
def dashboard_history(days: int = 30):
    if not mem:
        return {"daily": []}
    cutoff = (datetime.now() - __import__("datetime").timedelta(days=days)).strftime("%Y-%m-%d")
    rows = mem.conn.execute(
        "SELECT date, total_calls, total_tokens, total_cost FROM daily_summaries "
        "WHERE date >= ? ORDER BY date ASC", (cutoff,)
    ).fetchall()
    return {"daily": [dict(r) for r in rows]}


@app.get("/api/dashboard/timeseries")
def dashboard_timeseries(day: str = "today"):
    """Time-resolved token usage: today vs yesterday totals + per-hour breakdown.

    `day` selects which day the hourly breakdown covers: "today" or "yesterday".
    Timestamps in api_calls are stored as local-time ISO strings (datetime.now().isoformat()),
    so all date math uses SQLite's 'localtime' modifier to stay in the user's timezone.
    """
    if not mem:
        return {"today": {}, "yesterday": {}, "hourly": [], "hourly_day": day}

    def _day_totals(day_expr):
        row = mem.conn.execute(
            "SELECT COUNT(*) AS calls, "
            "       COALESCE(SUM(total_tokens),0) AS tokens, "
            "       COALESCE(SUM(cost_usd),0)     AS cost, "
            "       COALESCE(SUM(cache_hit),0)    AS cache_hits "
            "FROM api_calls WHERE date(timestamp)=" + day_expr
        ).fetchone()
        return dict(row) if row else {}

    today     = _day_totals("date('now','localtime')")
    yesterday = _day_totals("date('now','localtime','-1 day')")
    today["date"]     = datetime.now().strftime("%Y-%m-%d")
    yesterday["date"] = (datetime.now() - __import__("datetime").timedelta(days=1)).strftime("%Y-%m-%d")

    # Per-hour breakdown for the selected day, zero-filled across all 24 hours.
    hour_day_expr = "date('now','localtime','-1 day')" if day == "yesterday" else "date('now','localtime')"
    rows = mem.conn.execute(
        "SELECT strftime('%H', timestamp) AS hour, "
        "       COUNT(*) AS calls, "
        "       COALESCE(SUM(total_tokens),0) AS tokens, "
        "       COALESCE(SUM(cost_usd),0)     AS cost "
        "FROM api_calls WHERE date(timestamp)=" + hour_day_expr + " "
        "GROUP BY hour"
    ).fetchall()
    by_hour = {r["hour"]: dict(r) for r in rows}
    hourly = [
        by_hour.get(f"{h:02d}", {"hour": f"{h:02d}", "calls": 0, "tokens": 0, "cost": 0})
        for h in range(24)
    ]
    for slot in hourly:
        slot["hour"] = f"{int(slot['hour']):02d}"

    return {"today": today, "yesterday": yesterday, "hourly": hourly, "hourly_day": day}


# ── Voice greeting + shutdown ─────────────────────────────────────────────────

import random as _random

def _time_greeting() -> str:
    h = datetime.now().hour
    if h < 12:   return "Good morning"
    if h < 17:   return "Good afternoon"
    if h < 21:   return "Good evening"
    return "Good evening"

# Note: "Athena" mispronounced as "Atheney" by Kokoro bf_emma.
# Greetings now use "your AI assistant" or "online" — avoids the name in TTS.
# The name still appears visually in the UI.
_GREETINGS_MORNING = [
    "Good morning, Steven. Your AI operating system is online and ready.",
    "Morning. Latitude MedTech is online. What are we working on today?",
    "Good morning, Steven. Your AI assistant has loaded. Ready to go.",
    "Morning. All systems online. What can I help you with?",
]
_GREETINGS_AFTERNOON = [
    "Good afternoon, Steven. Your AI assistant is online and ready.",
    "Afternoon. Latitude MedTech online. What would you like to work on?",
    "Good afternoon, Steven. All systems ready. How can I help?",
    "Afternoon. Online and standing by, Steven.",
]
_GREETINGS_EVENING = [
    "Good evening, Steven. Your AI assistant is online — still at it.",
    "Evening. Latitude MedTech online. What's on the agenda?",
    "Good evening, Steven. Online and ready. What do you need?",
    "Evening. All systems running. Let's get to work.",
]

_GOODBYES = [
    "Goodbye, Steven. Have a wonderful day — you're building something great.",
    "Signing off. Take care, and well done today.",
    "Farewell, Steven. Great working with you. Until next time.",
    "Goodbye. Rest well — Latitude MedTech will be here when you return.",
    "That's a wrap. Have a great day, Steven.",
    "Signing off. It was a pleasure. See you next time.",
]

def _pick_greeting() -> str:
    h = datetime.now().hour
    if h < 12:   pool = _GREETINGS_MORNING
    elif h < 17: pool = _GREETINGS_AFTERNOON
    else:        pool = _GREETINGS_EVENING
    return _random.choice(pool)

_phrase_cache: dict = {}   # phrase text → raw WAV bytes pre-synthesized at startup


def _kokoro_synth(text: str) -> Optional[bytes]:
    """Fetch WAV bytes from the Kokoro TTS server. Returns None on any failure."""
    try:
        import urllib.request, json
        payload = json.dumps({"text": text, "voice": os.getenv("VOICE_KOKORO_VOICE", "bf_emma")}).encode()
        req = urllib.request.Request("http://127.0.0.1:8002/speak", data=payload,
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read()
    except Exception:
        return None


def _preload_phrases():
    """Synthesize all greeting + goodbye phrases once, immediately after models load.

    Blocks until voice_bridge._models_ready fires (guaranteed before Chrome opens),
    then hits Kokoro for each phrase and stores the WAV bytes in _phrase_cache.
    _speak_phrase plays cached audio instantly with zero synthesis latency.
    """
    if not VOICE_AVAILABLE:
        return
    try:
        from voice_bridge import _models_ready
        _models_ready.wait(timeout=300)
    except Exception:
        import time; time.sleep(30)
    all_phrases = (_GREETINGS_MORNING + _GREETINGS_AFTERNOON +
                   _GREETINGS_EVENING + _GOODBYES)
    for phrase in all_phrases:
        if phrase not in _phrase_cache:
            wav = _kokoro_synth(phrase)
            if wav:
                _phrase_cache[phrase] = wav


def _speak_phrase(text: str):
    """Play a greeting or goodbye phrase.

    Uses pre-synthesized WAV from _phrase_cache when available (zero latency);
    falls back to on-demand Kokoro synthesis, then pyttsx3.
    """
    try:
        import io, sounddevice as sd, soundfile as sf
        wav = _phrase_cache.get(text) or _kokoro_synth(text)
        if wav is None:
            raise RuntimeError("no Kokoro audio")
        if text not in _phrase_cache:
            _phrase_cache[text] = wav   # cache opportunistically
        data, sr = sf.read(io.BytesIO(wav))
        sd.play(data.astype("float32"), sr); sd.wait()
    except Exception:
        try:
            import pyttsx3
            e = pyttsx3.init(); e.setProperty("rate", 175); e.say(text); e.runAndWait()
        except Exception:
            pass
    # Allow speaker audio to fully drain before the mic reopens for wake word detection
    import time; time.sleep(1.0)


@app.on_event("startup")
async def _startup_preload():
    import threading
    threading.Thread(target=_preload_phrases, daemon=True, name="tts-preloader").start()

_session_greeted = False   # plays once per server restart, regardless of tab refreshes

@app.post("/api/voice/greet")
async def greet():
    """
    Play the startup greeting exactly once per server session.
    React StrictMode and tab refreshes call this multiple times — the flag prevents repeats.
    """
    global _session_greeted
    if _session_greeted:
        return {"phrase": "", "skipped": True}
    _session_greeted = True
    phrase = _pick_greeting()
    # Await TTS completion so the caller knows it's safe to open the mic
    await asyncio.get_event_loop().run_in_executor(None, _speak_phrase, phrase)
    return {"phrase": phrase}

@app.post("/api/shutdown")
async def shutdown_app(background_tasks: BackgroundTasks):
    """Play a goodbye, hand off to the verified stop script, then exit.

    TTS is awaited synchronously so the response only returns after Athena
    finishes speaking. The stop script and os._exit run as a background task
    so they fire after the response has been fully sent to the client.
    """
    global _shutting_down
    _shutting_down = True      # prevent WS-disconnect from double-speaking
    phrase = _random.choice(_GOODBYES)
    stop_script = ATHENA / "ui" / "stop_athena.ps1"

    # Block until TTS finishes — response is sent only after this completes.
    await asyncio.get_event_loop().run_in_executor(None, _speak_phrase, phrase)

    def _cleanup():
        import time; time.sleep(0.15)  # brief buffer for response to flush
        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            subprocess.Popen(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-NoProfile",
                 "-File", str(stop_script)],
                creationflags=flags, close_fds=True,
            )
        except Exception:
            pass
        import os; os._exit(0)

    background_tasks.add_task(_cleanup)
    return {"phrase": phrase, "status": "shutting_down"}


if __name__ == "__main__":
    import uvicorn
    print("\nLatitude MedTech API starting on http://localhost:8000")
    print("Open http://localhost:3000 for the dashboard\n")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
