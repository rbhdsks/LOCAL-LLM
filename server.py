#!/usr/bin/env python3
"""Tiny password-protected web UI/API proxy for a local Ollama model."""
from __future__ import annotations
import argparse
import json
import os
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
PASSWORD = os.environ.get("APP_PASSWORD", "")
DEMO = os.environ.get("DEMO_MODE", "0") == "1"

class Handler(BaseHTTPRequestHandler):
    server_version = "LocalResearchAssistant/0.1"

    def log_message(self, fmt, *args):
        # Avoid logging prompts, request bodies, or passwords.
        print(f"{self.address_string()} - {fmt % args}")

    def _send(self, status: int, body: bytes, content_type: str = "application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, data):
        self._send(status, json.dumps(data).encode("utf-8"))

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            try:
                page = (STATIC / "index.html").read_bytes()
            except OSError:
                self._json(500, {"error": "UI file is missing"}); return
            self._send(200, page, "text/html; charset=utf-8"); return
        self._json(404, {"error": "Not found"})

    def _read_payload(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 100_000:
                self._json(413, {"error": "Request too large"}); return None
            data = json.loads(self.rfile.read(length) or b"{}") if length else {}
            if not isinstance(data, dict):
                self._json(400, {"error": "JSON body must be an object"}); return None
            return data
        except (ValueError, json.JSONDecodeError):
            self._json(400, {"error": "Invalid JSON"}); return None

    def do_POST(self):
        if self.path not in ("/api/status", "/api/chat"):
            self._json(404, {"error": "Not found"}); return
        data = self._read_payload()
        if data is None: return
        supplied = str(data.get("password", ""))
        if not secrets.compare_digest(supplied, PASSWORD):
            self._json(401, {"error": "Password is incorrect"}); return
        if self.path == "/api/status":
            if DEMO:
                self._json(200, {"mode": "demo", "model": "Demo model (no LLM connected)"}); return
            try:
                with urlopen(Request(f"{OLLAMA_URL}/api/tags"), timeout=3) as response:
                    tags = json.loads(response.read())
                names = [m.get("name", "") for m in tags.get("models", [])]
                self._json(200, {"mode": "ollama", "model": MODEL, "available": MODEL in names, "installed_models": names})
            except Exception:
                self._json(200, {"mode": "ollama", "model": MODEL, "available": False, "installed_models": []})
            return

        messages = data.get("messages", [])
        if not isinstance(messages, list) or not messages or len(messages) > 40:
            self._json(400, {"error": "Send between 1 and 40 chat messages"}); return
        clean = []
        for msg in messages:
            if not isinstance(msg, dict) or msg.get("role") not in ("user", "assistant") or not isinstance(msg.get("content"), str):
                self._json(400, {"error": "Invalid message format"}); return
            if len(msg["content"]) > 20_000:
                self._json(400, {"error": "A message is too long (20,000 characters max)"}); return
            clean.append({"role": msg["role"], "content": msg["content"]})
        if DEMO:
            prompt = next((m["content"] for m in reversed(clean) if m["role"] == "user"), "")
            self._json(200, {"reply": f"Demo mode received your message: {prompt}\n\nThis confirms the browser-to-server path works. Connect Ollama to get real model answers."}); return

        body = json.dumps({"model": MODEL, "messages": clean, "stream": False}).encode()
        request = Request(f"{OLLAMA_URL}/api/chat", data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=300) as response:
                result = json.loads(response.read())
            self._json(200, {"reply": result.get("message", {}).get("content", "")})
        except HTTPError as e:
            detail = e.read(1000).decode("utf-8", "replace")
            self._json(502, {"error": f"Ollama returned HTTP {e.code}: {detail}"})
        except (URLError, TimeoutError, OSError) as e:
            self._json(502, {"error": f"Cannot reach Ollama at {OLLAMA_URL}. Is Ollama running? ({e})"})
        except Exception as e:
            self._json(502, {"error": f"Model service error: {e}"})


def main():
    parser = argparse.ArgumentParser(description="Private local LLM web prototype")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    args = parser.parse_args()
    if not DEMO and len(PASSWORD) < 10:
        raise SystemExit("Set APP_PASSWORD to a password of at least 10 characters, or run with DEMO_MODE=1 for a fake local demo.")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Local Research Assistant listening on http://{args.host}:{args.port}")
    print("Demo mode: no real model" if DEMO else f"Ollama model: {MODEL}; prompts are sent only to {OLLAMA_URL}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server")
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
