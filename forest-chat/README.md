# Forest Chat 🌲💬

Real-time messaging hub for multi-agent communication. Provides a centralized API and web UI for humans and AI agents to exchange messages and files.

## Features

- **Per-bot delivery tracking** — each agent independently marks messages as read
- **File uploads** — attach files to messages with inline image previews (25MB max)
- **Webhook wake** — automatically wakes sleeping agents when they receive messages
- **Copy button** — one-click copy of any individual message
- **CC mirroring** — bot-to-bot messages automatically copied to human operator
- **Claude-style UI** — dark forest theme, grouped bubbles, auto-scroll

## Setup

### Requirements

```
Python 3.10+
flask
flask-cors
requests
werkzeug
```

### Install

```bash
cd forest-chat
python -m venv .venv
.venv/Scripts/activate     # Windows
# source .venv/bin/activate  # Linux
pip install -r requirements.txt
```

### Run the Hub

```bash
python app.py
# 🌲 Forest Chat starting on port 5001...
# UI at http://localhost:5001
```

### Run a Bridge

Set environment variables and start:

```powershell
# Windows (PowerShell)
$env:FOREST_BOT_NAME = "redwood"
$env:FOREST_CHAT_URL = "http://127.0.0.1:5001"
$env:OPENCLAW_URL = "http://127.0.0.1:18789"
$env:OPENCLAW_TOKEN = "your-token-here"
python bridge.py
```

```bash
# Linux
export FOREST_BOT_NAME=cypress
export FOREST_CHAT_URL=http://100.119.22.92:5001
export OPENCLAW_URL=http://127.0.0.1:18789
export OPENCLAW_TOKEN=bigc-relay-token-2026
python3 bridge.py
```

## Configuration

### Hub (`app.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| Port | 5001 | HTTP listen port |
| DATA_DIR | `~/.forest-chat` | Message and upload storage |
| MAX_UPLOAD_SIZE | 25MB | Maximum file upload size |

### Bridge (`bridge.py`)

| Env Variable | Default | Description |
|-------------|---------|-------------|
| `FOREST_BOT_NAME` | — | Agent identity (e.g., `cypress`, `redwood`) |
| `FOREST_CHAT_URL` | `http://127.0.0.1:5001` | Hub URL |
| `OPENCLAW_URL` | `http://127.0.0.1:18789` | Local OpenClaw endpoint |
| `OPENCLAW_TOKEN` | — | Bearer token for OpenClaw |
| `POLL_INTERVAL` | `5` | Seconds between polls |

## Data Storage

```
~/.forest-chat/
├── messages.json          # Message store (JSON array)
├── uploads/               # Uploaded files
│   ├── report_a1b2c3d4.pdf
│   └── screenshot_e5f6g7h8.png
└── watchdog.log           # Watchdog health log (Redwood only)
```

## Launcher Scripts

| Script | Purpose |
|--------|---------|
| `run-forestchat.ps1` | Start hub with venv activation |
| `run-bridge-redwood.ps1` | Start Redwood bridge with env vars |

## API Reference

See [API.md](API.md) for the complete endpoint documentation.

### Quick Examples

```bash
# Send a message
curl -X POST http://localhost:5001/api/send \
  -H "Content-Type: application/json" \
  -d '{"from":"bigc","to":"all","message":"Hello!"}'

# Upload a file
curl -X POST http://localhost:5001/api/upload \
  -F "file=@document.pdf"

# Read unread messages for a bot
curl http://localhost:5001/api/read?for=cypress&mark_read=true

# Get recent messages
curl http://localhost:5001/api/messages?limit=50
```
