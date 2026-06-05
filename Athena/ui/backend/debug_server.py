import sys
import traceback

from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[2] / 'agents'))

try:
    # Try importing everything server.py imports
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, Request
    print("OK: fastapi")
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, JSONResponse
    from pydantic import BaseModel
    from dotenv import load_dotenv
    print("OK: all imports")

    # Try loading the full server
    with open('server.py') as f:
        code = f.read()

    # Count routes
    routes = [line for line in code.split('\n') if line.startswith('@app.')]
    print(f"Routes in file: {len(routes)}")
    for r in routes:
        print(f"  {r}")

except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
