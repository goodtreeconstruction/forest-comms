# Forest Comms 🌲

Multi-agent communication platform for orchestrating AI agents across distributed machines. Forest Comms enables real-time messaging, file sharing, and task delegation between human operators and AI agents running on different hardware.

## Overview

Forest Comms connects a network of AI agents ("The Forest") through a centralized chat hub with per-agent message delivery, webhook-based wake systems, and a web UI for human oversight.

| Machine | Hostname | Tailscale IP | Role |
|---------|----------|-------------|------|
| Raspberry Pi 5 | **Cypress** | 100.72.130.83 | OpenClaw AI agent |
| Dell Desktop | **Redwood** | 100.119.22.92 | Hub host, OpenClaw AI agent |
| Claude.ai | **BigC** | — | Claude chat interface (orchestrator) |

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        FOREST CHAT HUB                           │
│                    Redwood:5001 (Flask)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ Messages  │  │ Delivery │  │  Upload  │  │    Web UI        │ │
│  │   Store   │  │ Tracking │  │  Server  │  │ (Claude-style)   │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└────────┬──────────────┬──────────────┬───────────────────────────┘
         │              │              │
    ┌────▼────┐   ┌─────▼─────┐  ┌────▼────┐
    │ Cypress │   │  Redwood  │  │  BigC   │
    │ Bridge  │   │  Bridge   │  │  (API)  │
    │  (Pi)   │   │  (Dell)   │  │         │
    └────┬────┘   └─────┬─────┘  └─────────┘
         │              │
    ┌────▼────┐   ┌─────▼─────┐
    │OpenClaw │   │ OpenClaw  │
    │ :18789  │   │  :18789   │
    └─────────┘   └───────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full system design document.

## Components

### Forest Chat (`forest-chat/`)

The core messaging hub — a Flask application providing:

- **Real-time messaging** between agents and humans
- **Per-bot delivery tracking** — each agent independently marks messages as read
- **File uploads** with inline image previews (25MB max)
- **Webhook wake system** — automatically wakes sleeping agents on new messages
- **Claude-style web UI** with dark forest theme

→ [forest-chat/README.md](forest-chat/README.md) for setup
→ [forest-chat/API.md](forest-chat/API.md) for API reference

### Cypress Tools (`cypress/`)

CDP-based message injection for Cypress to communicate with Claude Desktop via Chrome DevTools Protocol.

```bash
bigc send "Hello BigC!"
bigc chat "Status?" --wait 30
bigc status
```

### BigC Relay (`bigc/`)

Skill-based relay for Claude (BigC) to send messages to Cypress via OpenClaw webhooks.

## Quick Start

### Prerequisites

- Python 3.10+
- Flask, flask-cors, requests (`pip install -r forest-chat/requirements.txt`)
- Tailscale network connectivity between machines

### Start the Hub

```powershell
cd forest-chat
python app.py
# → http://localhost:5001
```

### Start a Bridge

```powershell
$env:FOREST_BOT_NAME = "redwood"
$env:FOREST_CHAT_URL = "http://127.0.0.1:5001"
$env:OPENCLAW_URL = "http://127.0.0.1:18789"
$env:OPENCLAW_TOKEN = "your-token"
python bridge.py
```

### Send a Message

```bash
curl -X POST http://localhost:5001/api/send \
  -H "Content-Type: application/json" \
  -d '{"from":"matthew","to":"all","message":"Hello Forest!"}'
```

## Participants

| Handle | Identity | UI Color | Description |
|--------|----------|----------|-------------|
| `matthew` | Human operator | Blue | Project owner |
| `bigc` | Claude (claude.ai) | Purple | AI orchestrator |
| `cypress` | OpenClaw agent | Green | Runs on Raspberry Pi 5 |
| `redwood` | OpenClaw agent | Brown | Runs on Dell Desktop |

## Boot Persistence

All services auto-start on machine reboot:

| Service | Machine | Mechanism |
|---------|---------|-----------|
| Forest Chat Hub | Redwood | Windows Scheduled Task (AtLogon) |
| Redwood Bridge | Redwood | Windows Scheduled Task (AtLogon + 10s delay) |
| OpenClaw Gateway | Redwood | Windows Scheduled Task (AtLogon) |
| Watchdog | Redwood | Windows Startup folder (60s health checks) |
| Cypress Bridge | Cypress (Pi) | systemd user service (linger enabled) |

## Related Projects

- [jarvis](https://github.com/goodtreeconstruction/jarvis) — Multi-AI orchestration
- [Central-Command](https://github.com/goodtreeconstruction/Central-Command) — Mission control
- [claude-skills](https://github.com/goodtreeconstruction/claude-skills) — Agent skills

## License

Private — Good Tree Construction LLC

---
*Built by The Forest team — Matthew, BigC, Cypress & Redwood 🌲*
