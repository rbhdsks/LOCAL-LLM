Local Research Assistant

A private, laptop-hosted AI assistant prototype that you can open from an iPad browser. The laptop runs the model; the iPad is the chat screen. The first use case is helping with thesis work while keeping prompts and documents on devices you control.

Project status

App: a small responsive web chat, served by Python.

Model runtime: Ollama on the Mac.

Starting model: qwen3:1.7b (downloaded separately; it is not stored in this Git repository).

Hardware: tested setup target is a MacBook Air with Apple M1 and 8 GB unified memory. The 1.7B model is a modest starting point; speed and available context depend on memory pressure and other apps.

Demo mode: available for checking the app without calling a model.

Thesis files/RAG: not connected yet. The current assistant only sees the messages you send in the current browser page.

Fine-tuning, distributed training, worker nodes, admin panel, and remote access: future work.

Architecture

flowchart LR
    IPad["iPad browser"] -->|"question over Wi-Fi"| Server["Python web server on Mac"]
    Server -->|"local API request"| Ollama["Ollama on Mac"]
    Ollama --> Model["Qwen model weights on Mac"]
    Model --> Ollama --> Server -->|"answer over Wi-Fi"| IPad

What each part does

Qwen model: generates the answer. Its model files are downloaded to the Mac by Ollama.

Ollama: loads and runs those model files and exposes a local API.

server.py: serves the chat page, checks the access password, and forwards chat messages to Ollama.

iPad browser: displays the chat UI and sends requests to the Mac. It does not run the model in this version.

Wi-Fi: carries requests between the iPad and Mac when both are on the same trusted network.

A request travels like this:

You enter a question in Safari on the iPad.

The browser sends it to the Mac's Python server.

The server forwards it to Ollama on the same Mac.

Ollama asks the selected model to generate an answer.

The answer travels back through the server to the iPad.

The Mac must remain on for the assistant to answer. If the iPad is switched off, the Mac's model can keep running. If the Mac is switched off, this prototype is unavailable until the Mac or a future host comes back online.

Model and code are separate

The Git repository contains the app code, not the model weights. This keeps large model files out of Git. The OLLAMA_MODEL setting tells the app which model already installed in Ollama to use.

For this Mac, start with qwen3:1.7b. Ollama lists this model at approximately 1.4 GB. That is the model download size, not the total RAM needed while generating answers. Close memory-heavy apps if generation is slow or the Mac becomes unresponsive. A larger model may give stronger answers but needs more memory.

Run on a Mac

1. Install and check Ollama

Install Ollama for macOS if it is not already installed. In Terminal:

ollama --version

2. Download and try the model

ollama run qwen3:1.7b

Try a short question. Type /bye to leave the model prompt when finished. The model remains installed locally.

3. Start the app for Mac-only testing

From the project folder:

read -s APP_PASSWORD
echo
export APP_PASSWORD
export OLLAMA_MODEL='qwen3:1.7b'
python3 server.py

When read -s waits, type a password of at least 10 characters and press Enter. The characters will not appear on screen. Open http://127.0.0.1:8000 on the Mac and enter that password.

4. Open it on the iPad over local Wi-Fi

Stop the server with Control+C. Restart it so it listens on the Mac's network interfaces:

python3 server.py --host 0.0.0.0

Find the Mac's Wi-Fi address in another Terminal window:

ipconfig getifaddr en0

If that returns no address, find the IP under System Settings → Wi-Fi → Details → TCP/IP. Keep the server running. Connect the iPad to the same trusted Wi-Fi network and open this address in Safari, replacing the example IP with the address shown on your Mac:

http://192.168.1.5:8000

Enter the app password and send a test message. 0.0.0.0 is the server's listen address; it is not the address to type into Safari. If the page cannot connect, check that both devices are on the same Wi-Fi, that the server is still running, and that macOS Firewall allows Python to accept incoming connections.

Demo mode

Demo mode checks the web interface and server without needing Ollama. It returns an echo, not an AI answer.

APP_PASSWORD=demopassword DEMO_MODE=1 python3 server.py

Open http://127.0.0.1:8000 and enter demopassword. Stop the demo server before starting a real-model server on the same port.

Configuration

Setting

Default

Purpose

APP_PASSWORD

none

Required in real mode; use at least 10 characters.

OLLAMA_URL

http://127.0.0.1:11434

Ollama's local API address.

OLLAMA_MODEL

qwen2.5:3b

Installed model tag to use. Set to qwen3:1.7b for the current Mac setup.

HOST

127.0.0.1

Server bind address. Use --host 0.0.0.0 for iPad access over LAN.

PORT

8000

Web app port.

DEMO_MODE

0

Set to 1 for echo-only demo mode.

Privacy and security

In real mode, the app sends prompts to Ollama at the configured local address. It does not call a hosted AI API.

Chat history is held in the browser page and is cleared when you refresh. This prototype does not save prompts or answers to a database or file.

The server prints request paths and response statuses to its terminal, not the prompt text.

The iPad-to-Mac connection uses plain HTTP in this prototype. Use it only on a trusted private network. Do not expose port 8000 through router port forwarding or use it as a public internet service.

The password is a basic shared-password gate, not a production authentication system. Remote access needs a private VPN/tunnel, HTTPS, stronger session handling, and a security review.

Downloading model weights requires internet access. Once installed, local inference can run without sending prompts to an external model service.

What it can help with today

With the relevant material pasted into chat, the small model can help explain a code snippet, summarize an experiment result, suggest a draft experiment plan, or improve the wording of a thesis paragraph. It can make mistakes. Verify mathematical derivations, empirical conclusions, and citations against your code and source papers.

The app does not yet read the thesis repository, notebooks, or PDFs automatically. It also does not retain context after a browser refresh. A future local document-search feature can retrieve relevant thesis files and show their source paths. That is retrieval-augmented generation (RAG): it gives the model useful context at answer time without changing its weights.

Fine-tuning changes model weights using examples. We should first build document retrieval and an evaluation set for thesis questions, then consider a lightweight fine-tune only if we can identify a repeatable behavior that retrieval and good instructions do not solve.

Project phases

Local chat prototype — current phase. Connect the iPad browser, Mac server, Ollama, and one local model.

Thesis knowledge — next. Index selected thesis notes, papers, source code, and experiment outputs locally; retrieve relevant passages and cite file names/sections.

Evaluation. Build representative questions about BTL, CDM, low-rank CDM, optimizer behavior, and experiment interpretation. Check correctness and citations before relying on answers.

Fine-tuning, if useful. Test a small LoRA-style adaptation on carefully prepared examples. Keep the original model and compare on held-out questions.

Admin and security. Add named users, permissions, node registration/revocation, job history, model/data version records, and secure remote access.

Optional decentralized nodes. Let friends opt in as worker devices, with clear control over whether their device participates and what it can access. A coordinator can schedule jobs; nodes can return results or model updates. Keeping raw data on a node does not automatically make its updates private, so privacy protections and consent must be designed and tested.

Distributed computing experiments. Data parallelism means several model copies train on separate data batches and synchronize updates. Model parallelism means splitting one model across devices. These add network and synchronization complexity, so first measure a real need on the single Mac. An iPad is not a reliable always-on worker when its app is backgrounded or the device is off.

Blockchain is not required for the first coordinator. Start with authenticated nodes, signed job records, permissions, and an audit log. Consider a ledger only if multiple independent owners need a shared trust or incentive mechanism that simpler records cannot provide.

Current limitations

One Mac is the only model host; shutting it down stops inference.

The current password gate is basic and all local-network traffic is unencrypted.

No user accounts, roles, admin dashboard, job queue, or node coordinator.

No RAG, citation retrieval, automatic repository access, saved chat history, or fine-tuning.

No model parallelism or data-parallel training.

The 1.7B model is a useful local starting point, not a substitute for checking thesis mathematics and research claims.