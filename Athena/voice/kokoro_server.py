"""
Kokoro TTS Server
=================
Persistent process that keeps the Kokoro model loaded in memory.
Accepts POST /speak → returns WAV audio bytes directly.
Runs on localhost:8002.

Start: called automatically by voice_bridge on first TTS request.
Stop:  POST /shutdown or kill the process.
"""

import io
import os
import sys
import numpy as np
import soundfile as sf
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# ── Load Kokoro once at startup ───────────────────────────────────────────────

print("[kokoro_server] Loading Kokoro model...", flush=True)
try:
    from kokoro import KPipeline
    _pipeline_en_gb = KPipeline(lang_code="b")   # British English
    _pipeline_en_us = KPipeline(lang_code="a")   # American English fallback
    _pipeline = _pipeline_en_gb
    print("[kokoro_server] Model loaded. Ready on port 8002.", flush=True)
except Exception as e:
    print(f"[kokoro_server] FATAL: {e}", flush=True)
    sys.exit(1)


def _synthesise(text: str, voice: str, speed: float = 0.92) -> bytes:
    """Return WAV bytes for the given text."""
    chunks = []
    for _, _, audio in _pipeline(text, voice=voice, speed=speed):
        chunks.append(audio)
    if not chunks:
        raise RuntimeError("No audio generated")
    combined = np.concatenate(chunks)
    buf = io.BytesIO()
    sf.write(buf, combined, 24000, format="WAV")
    return buf.getvalue()


# ── HTTP handler ──────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass   # suppress per-request access logs

    def do_POST(self):
        if self.path == "/shutdown":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            sys.exit(0)

        if self.path != "/speak":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body   = json.loads(self.rfile.read(length))
        text   = body.get("text", "").strip()
        voice  = body.get("voice", "bf_emma")

        if not text:
            self.send_response(400)
            self.end_headers()
            return

        try:
            speed = float(body.get("speed", 0.92))
            wav_bytes = _synthesise(text, voice, speed)
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(wav_bytes)))
            self.end_headers()
            self.wfile.write(wav_bytes)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8002
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"[kokoro_server] Listening on port {port}", flush=True)
    server.serve_forever()
