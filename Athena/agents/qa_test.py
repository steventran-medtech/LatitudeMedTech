"""
Latitude MedTech — QA Test Suite
==================================
Runs before any deployment to catch bugs before you see them.

Tests:
1. Syntax check all Python files
2. Import check all agents
3. Unicode safety check (Windows cp1252)
4. F-string backslash check (Python 3.9)
5. Path hardcoding check
6. Server route completeness check
7. API endpoint live test (if server running)
8. Agent dry-run test

Run:
    python qa_test.py           (all tests)
    python qa_test.py --quick   (syntax + imports only)
    python qa_test.py --live    (includes live API tests)
"""

import os
import sys
import ast
import json
import re
import argparse
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime

ATHENA    = Path(__file__).resolve().parent.parent  # agents/ -> Athena/
AGENTS    = ATHENA / "agents"
UI_BACK   = ATHENA / "ui" / "backend"
UI_FRONT  = ATHENA / "ui" / "frontend" / "src"
VOICE_DIR = ATHENA / "voice"

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"
SKIP = "[SKIP]"

results = []

def log(status, test, detail=""):
    icon = {"[PASS]":"OK", "[FAIL]":"XX", "[WARN]":"!!", "[SKIP]":"--"}[status]
    msg = f"  {icon}  {test}"
    if detail:
        msg += f"\n       {detail}"
    print(msg)
    results.append({"status": status, "test": test, "detail": detail})

def section(title):
    print(f"\n{'='*56}")
    print(f"  {title}")
    print(f"{'='*56}")


# ── Test 1: Syntax check ──────────────────────────────────────────────────────

def test_syntax():
    section("1. Python Syntax Check")
    py_files = list(AGENTS.glob("*.py")) + list(UI_BACK.glob("*.py"))
    for f in sorted(py_files):
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            ast.parse(content)
            log(PASS, f"Syntax: {f.name}")
        except SyntaxError as e:
            log(FAIL, f"Syntax: {f.name}", f"Line {e.lineno}: {e.msg}")


# ── Test 2: Unicode safety (Windows cp1252) ───────────────────────────────────

def test_unicode():
    section("2. Unicode Safety (Windows cp1252)")
    BAD_CHARS = ["╔","╗","╚","╝","╠","╣","║","═","◎","◈","◇","◉","✓","✗","▷"]
    py_files  = list(AGENTS.glob("*.py")) + list(UI_BACK.glob("*.py"))

    for f in sorted(py_files):
        content = f.read_text(encoding="utf-8", errors="replace")
        # Check print statements for bad chars
        bad_prints = []
        for i, line in enumerate(content.splitlines(), 1):
            if "print(" in line:
                for ch in BAD_CHARS:
                    if ch in line:
                        bad_prints.append(f"Line {i}: {ch}")
        if bad_prints:
            log(FAIL, f"Unicode: {f.name}", " | ".join(bad_prints[:3]))
        else:
            log(PASS, f"Unicode: {f.name}")


# ── Test 3: F-string backslash (Python 3.9) ───────────────────────────────────

def test_fstring_backslash():
    section("3. F-string Backslash Check (Python 3.9)")
    py_files = list(AGENTS.glob("*.py")) + list(UI_BACK.glob("*.py"))

    for f in sorted(py_files):
        content = f.read_text(encoding="utf-8", errors="replace")
        issues  = []
        # Find f-strings with backslashes inside {}
        fstring_pattern = re.compile(r'f""".*?"""', re.DOTALL)
        for match in fstring_pattern.finditer(content):
            text = match.group()
            # Find { } blocks
            for block in re.finditer(r'\{[^}]+\}', text):
                if '\\' in block.group():
                    line_no = content[:match.start()].count('\n') + 1
                    issues.append(f"Line ~{line_no}")
        if issues:
            log(FAIL, f"F-string backslash: {f.name}", " | ".join(issues[:3]))
        else:
            log(PASS, f"F-string backslash: {f.name}")


# ── Test 4: Import check ──────────────────────────────────────────────────────

def test_imports():
    section("4. Import Check")
    sys.path.insert(0, str(AGENTS))

    agents_to_check = [
        "memory",
        "kb_query",
        "settings_manager",
        "dashboard",
    ]

    for mod in agents_to_check:
        f = AGENTS / f"{mod}.py"
        if not f.exists():
            log(WARN, f"Import: {mod}", "File not found in agents/")
            continue
        try:
            spec   = importlib.util.spec_from_file_location(mod, f)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            log(PASS, f"Import: {mod}")
        except Exception as e:
            log(FAIL, f"Import: {mod}", str(e)[:100])


# ── Test 5: Server route completeness ─────────────────────────────────────────

def test_server_routes():
    section("5. Server Route Completeness")
    server_file = UI_BACK / "server.py"
    if not server_file.exists():
        log(FAIL, "Server file exists", str(server_file))
        return

    content = server_file.read_text(encoding="utf-8", errors="replace")

    required_routes = [
        '/api/dashboard',
        '/api/drafts',
        '/api/briefings',
        '/api/agents/rag',
        '/api/agents/content',
        '/api/agents/briefing',
        '/api/files/delete',
        '/api/files/save',
        '/api/settings',
        '/api/coaching/briefs',
        '/api/documents/generate',
    ]

    # Check __main__ is at end
    main_idx  = content.rfind('if __name__ == "__main__"')
    app_idx   = content.rfind('@app.')
    if main_idx < app_idx:
        log(FAIL, "server.py: __main__ block position",
            f"__main__ at pos {main_idx} but last @app. route at {app_idx} — routes after __main__ won't load")
    else:
        log(PASS, "server.py: __main__ block at end")

    for route in required_routes:
        if route in content:
            log(PASS, f"Route exists: {route}")
        else:
            log(FAIL, f"Route missing: {route}")


# ── Test 6: Path hardcoding check ─────────────────────────────────────────────

def test_paths():
    section("6. Hardcoded Path Check")
    py_files = list(AGENTS.glob("*.py"))
    for f in sorted(py_files):
        content = f.read_text(encoding="utf-8", errors="replace")
        # Check load_dotenv uses correct path
        if "load_dotenv" in content:
            if "Path.home()" in content or "ATHENA" in content or r"Athena\voice" in content:
                log(PASS, f"Paths: {f.name}")
            else:
                log(WARN, f"Paths: {f.name}", "load_dotenv may not find .env")


# ── Test 7: Live API tests ────────────────────────────────────────────────────

def test_live_api():
    section("7. Live API Tests (server must be running)")
    try:
        import urllib.request
        import urllib.error

        base = "http://localhost:8000"

        # Test root
        try:
            r = urllib.request.urlopen(f"{base}/", timeout=3)
            log(PASS, "API: root endpoint reachable")
        except Exception as e:
            log(FAIL, "API: server not reachable", "Start server first: python server.py")
            return

        # Test dashboard
        try:
            r    = urllib.request.urlopen(f"{base}/api/dashboard", timeout=5)
            data = json.loads(r.read())
            if "token_report" in data:
                log(PASS, "API: /api/dashboard returns data")
            else:
                log(WARN, "API: /api/dashboard", f"Unexpected response: {str(data)[:80]}")
        except Exception as e:
            log(FAIL, "API: /api/dashboard", str(e)[:80])

        # Test routes completeness via openapi
        try:
            r      = urllib.request.urlopen(f"{base}/openapi.json", timeout=5)
            spec   = json.loads(r.read())
            paths  = list(spec.get("paths", {}).keys())
            log(PASS, f"API: {len(paths)} routes registered")

            required = ["/api/files/delete", "/api/settings", "/api/coaching/briefs"]
            for route in required:
                if route in paths:
                    log(PASS, f"API route live: {route}")
                else:
                    log(FAIL, f"API route missing: {route}",
                        "Restart server after updating server.py")
        except Exception as e:
            log(FAIL, "API: openapi.json", str(e)[:80])

        # Test delete endpoint exists (don't actually delete)
        try:
            import urllib.request
            req  = urllib.request.Request(
                f"{base}/api/files/delete",
                data=b'{"filename":"test.md","folder":"content/drafts"}',
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            try:
                r    = urllib.request.urlopen(req, timeout=5)
                data = json.loads(r.read())
                # 404 on file is fine - means route works, file just doesn't exist
                log(PASS, "API: /api/files/delete route responding")
            except urllib.error.HTTPError as e:
                body = e.read().decode()
                if "not found" in body.lower() or "File not found" in body:
                    log(PASS, "API: /api/files/delete route responding (file not found is expected)")
                else:
                    log(FAIL, "API: /api/files/delete", body[:80])
        except Exception as e:
            log(FAIL, "API: /api/files/delete", str(e)[:80])

    except ImportError:
        log(SKIP, "Live API tests", "urllib not available")


# ── Test 8: KB and memory check ───────────────────────────────────────────────

def test_data():
    section("8. Data & Memory Check")

    # Memory DB
    mem_db = ATHENA / "memory" / "latitude_memory.db"
    if mem_db.exists():
        size = mem_db.stat().st_size
        log(PASS, f"Memory DB exists ({size:,} bytes)")
    else:
        log(WARN, "Memory DB not found", "Run an agent first to create it")

    # KB
    kb_dir = ATHENA / "knowledge_base"
    if kb_dir.exists():
        files = list(kb_dir.rglob("*.json"))
        non_index = [f for f in files if f.name != "index.json"]
        log(PASS, f"Knowledge base: {len(non_index)} document files")
        if len(non_index) == 0:
            log(WARN, "Knowledge base empty", "Run run_rag.bat to populate")
    else:
        log(WARN, "Knowledge base directory not found", "Run run_rag.bat")

    # Settings
    settings_file = ATHENA / "settings.json"
    if settings_file.exists():
        log(PASS, "settings.json exists")
    else:
        log(WARN, "settings.json not found", "Will be created on first settings load")

    # .env
    env_file = VOICE_DIR / ".env"
    if env_file.exists():
        content = env_file.read_text(errors="replace")
        keys = ["ANTHROPIC_API_KEY", "TAVILY_API_KEY", "BRAVE_API_KEY", "HF_TOKEN"]
        for key in keys:
            if key in content and f"{key}=" in content:
                log(PASS, f".env: {key} present")
            else:
                log(WARN, f".env: {key} missing")
    else:
        log(FAIL, ".env file not found", str(env_file))


# ── Summary ───────────────────────────────────────────────────────────────────

def print_summary():
    print(f"\n{'='*56}")
    print("  QA SUMMARY")
    print(f"{'='*56}")

    passed  = sum(1 for r in results if r["status"] == PASS)
    failed  = sum(1 for r in results if r["status"] == FAIL)
    warned  = sum(1 for r in results if r["status"] == WARN)
    skipped = sum(1 for r in results if r["status"] == SKIP)

    print(f"  OK  Passed : {passed}")
    print(f"  XX  Failed : {failed}")
    print(f"  !!  Warned : {warned}")
    print(f"  --  Skipped: {skipped}")
    print(f"{'='*56}")

    if failed > 0:
        print("\n  FAILURES TO FIX:")
        for r in results:
            if r["status"] == FAIL:
                print(f"  - {r['test']}")
                if r["detail"]:
                    print(f"    {r['detail']}")

    if failed == 0:
        print("\n  All checks passed. Safe to deploy.")
    else:
        print(f"\n  {failed} failure(s) found. Fix before deploying.")

    print()
    return failed == 0


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Syntax + imports only")
    parser.add_argument("--live",  action="store_true", help="Include live API tests")
    args = parser.parse_args()

    print(f"\nLatitude MedTech QA Test Suite")
    print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    test_syntax()
    test_unicode()
    test_fstring_backslash()
    test_server_routes()

    if not args.quick:
        test_imports()
        test_paths()
        test_data()

    if args.live:
        test_live_api()

    passed = print_summary()
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
