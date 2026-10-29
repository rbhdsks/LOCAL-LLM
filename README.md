# Local Research Assistant — prototype 0.1

A small password-protected web chat hosted by your laptop. An iPad (or another browser) connects to the laptop. The app forwards messages to a local Ollama server; it does not send prompts to a hosted AI API and does not write chat history to disk.

## What works in this prototype

- Responsive chat page for iPad and laptop browsers.
- Local Ollama `/api/chat` integration (default model name: `qwen2.5:3b`).
- Password check for every API request.
- Demo mode to verify the browser-to-server path without an LLM.
- No database, user accounts, fine-tuning, document retrieval, distributed nodes, or model/data parallelism yet.

## Run a safe local demo

Requires Python 3; no Python packages are needed.

```bash
cd ipad-local-llm
APP_PASSWORD=demopassword DEMO_MODE=1 python3 server.py
```

Open `http://127.0.0.1:8000`, enter `demopassword`, and send a message. Demo mode only echoes the request; it is not an LLM.

## Connect a real local model on a Mac

1. Install and launch Ollama on the Mac.
2. In Terminal, download a model that fits your device, for example `ollama pull qwen2.5:3b`. Model size and speed depend on Mac memory; this is only a starting point.
3. Start this app from its folder:

```bash
read -s APP_PASSWORD
echo
export APP_PASSWORD
export OLLAMA_MODEL='qwen2.5:3b'
python3 server.py --host 0.0.0.0
```

4. Find the Mac's private Wi-Fi IP address (System Settings → Wi-Fi → Details → TCP/IP).
5. On the iPad on the same trusted Wi-Fi, open `http://MAC_PRIVATE_IP:8000` and enter the password.

The server listens on all network interfaces only because `--host 0.0.0.0` was specified. Use it only on a trusted private network; do not forward port 8000 from your router or expose it to the public internet. For remote access later, add a private VPN/tunnel and review the authentication design first. This prototype uses HTTP, so use only on a trusted LAN.

## Configuration

- `APP_PASSWORD`: required for real mode; at least 10 characters.
- `OLLAMA_URL`: default `http://127.0.0.1:11434`.
- `OLLAMA_MODEL`: default `qwen2.5:3b`; must match an installed Ollama model tag.
- `HOST` / `PORT`: default `127.0.0.1` / `8000`.
- `DEMO_MODE=1`: no Ollama call; fake echo for connectivity checks.

## Next phases

1. Check laptop/iPad hardware and choose a model that fits.
2. Validate local chat over Wi-Fi.
3. Add private document retrieval (RAG) with source citations.
4. Add evaluation and only then consider LoRA fine-tuning.
5. Add opt-in worker nodes, admin roles, audit trail, and secure remote access.
6. Explore distributed training only if a measured bottleneck justifies it.
