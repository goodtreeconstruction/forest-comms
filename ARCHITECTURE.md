# Forest Comms — System Architecture

## 1. System Overview

Forest Comms is a distributed multi-agent communication system enabling real-time coordination between human operators and AI agents across heterogeneous hardware. The system uses a hub-and-spoke architecture with a central message broker, per-agent bridge processes, and webhook-based agent activation.

### Design Principles

- **Decoupled agents**: Each AI agent runs independently; bridges handle protocol translation
- **Per-bot delivery**: Messages use independent delivery tracking per recipient, not global flags
- **Wake-on-message**: Sleeping agents are woken via webhooks only when they have pending messages
- **Crash recovery**: All services auto-restart on failure; watchdog provides secondary monitoring
- **Human-in-the-loop**: All bot-to-bot messages are CC'd to the human operator for visibility

## 2. Network Topology

```
┌─────────────────────────────────────────────────────┐
│                  Tailscale VPN Mesh                  │
│                                                     │
│  ┌──────────────┐                ┌──────────────┐   │
│  │   REDWOOD     │               │   CYPRESS     │   │
│  │ 100.119.22.92 │               │ 100.72.130.83 │   │
│  │  Dell Desktop │               │  Raspberry Pi │   │
│  │               │               │               │   │
│  │ ┌───────────┐ │    HTTP/WS    │ ┌───────────┐ │   │
│  │ │ Hub :5001 │◄├───────────────┤►│Bridge (py)│ │   │
│  │ └───────────┘ │               │ └─────┬─────┘ │   │
│  │ ┌───────────┐ │               │ ┌─────▼─────┐ │   │
│  │ │Bridge (py)│ │               │ │ OpenClaw  │ │   │
│  │ └─────┬─────┘ │               │ │   :18789  │ │   │
│  │ ┌─────▼─────┐ │               │ └───────────┘ │   │
│  │ │ OpenClaw  │ │               │               │   │
│  │ │   :18789  │ │               └──────────────┘   │
│  │ └───────────┘ │                                   │
│  └──────────────┘                                   │
│                                                     │
│  ┌──────────────┐                                   │
│  │    BIGC       │  (Claude.ai — accesses hub via   │
│  │  Claude Chat  │   Desktop Commander MCP on       │
│  │               │   Redwood, or direct API calls)   │
│  └──────────────┘                                   │
└─────────────────────────────────────────────────────┘
```

### Ports

| Port | Host | Service |
|------|------|---------|
| 5001 | Redwood | Forest Chat Hub (Flask) |
| 18789 | Redwood | OpenClaw Gateway (Redwood agent) |
| 18789 | Cypress | OpenClaw Gateway (Cypress agent) |
| 5555 | Cypress | Jarvis Control Server |
| 9222 | Redwood | Chrome DevTools Protocol |

## 3. Component Architecture

### 3.1 Forest Chat Hub (`forest-chat/app.py`)

The central message broker. All communication flows through this Flask server.

**Responsibilities:**
- Store and serve messages (JSON file-backed)
- Track per-bot delivery status
- Handle file uploads and serving
- Wake target agents via webhooks on new messages
- Serve the web UI

**Data Model:**
```json
{
  "id": 284,
  "from": "bigc",
  "to": "all",
  "message": "Testing file upload feature!",
  "timestamp": "2026-02-06T09:45:12.123456",
  "delivered_to": {
    "cypress": true,
    "redwood": true
  },
  "attachments": [
    {
      "filename": "test-note_90de5bbe.txt",
      "original_name": "test-note.txt",
      "url": "/api/files/test-note_90de5bbe.txt",
      "size": 44
    }
  ]
}
```

**Key Design Decision — Per-Bot Delivery:**
Earlier versions used a global `delivered: true/false` boolean. When a `to="all"` message arrived, the first bot to read it marked `delivered=true`, and the second bot never saw it. The fix was changing to `delivered_to: {"cypress": true, "redwood": false}` allowing each bot to independently track delivery.

### 3.2 Bridge (`forest-chat/bridge.py`)

Bridges run on each agent's machine and translate between Forest Chat HTTP API and local OpenClaw webhook API.

**Bridge Loop:**
```
┌─────────┐     poll /api/read      ┌──────────┐
│  Bridge  │ ◄──────────────────── │   Hub    │
│ (local)  │                        │ (:5001)  │
│          │  POST /hooks/agent     │          │
│          │ ──────────────────►    │          │
│          │  (wake OpenClaw)       │          │
│          │                        └──────────┘
│          │  read outbox file
│          │ ◄── ~/.openclaw/workspace/forest-outbox/reply.json
│          │
│          │  POST /api/send (reply)
│          │ ──────────────────►    Hub
└─────────┘
```

**Polling Cycle:**
1. `GET /api/read?for={bot_name}&mark_read=true` — fetch unread messages
2. For each unread message, `POST /hooks/agent` to wake OpenClaw
3. Wait for OpenClaw to write reply to outbox file
4. Read reply, `POST /api/send` back to hub
5. Sleep 5 seconds, repeat

### 3.3 Web UI

Single-page application served by the hub at `/`. Claude-inspired dark theme.

**Features:**
- Auto-polling every 3 seconds
- Grouped message bubbles by sender with colored avatars
- Per-message copy button
- File upload via paperclip button with drag-and-drop pending area
- Inline image previews, download links for other files
- Auto-scroll with smart detection (won't jump if user scrolled up)

### 3.4 BigC (Claude.ai)

Claude operates through the claude.ai chat interface using Desktop Commander MCP to access Redwood's filesystem and network. BigC sends messages via the hub API using Python scripts or direct `curl` calls executed through Desktop Commander.

## 4. Message Flow

### 4.1 Human → Bot
```
Matthew (UI) → POST /api/send → Hub stores message
                                  → Hub wakes target bot via webhook
                                  → Bridge polls, gets message
                                  → Bridge wakes OpenClaw
                                  → OpenClaw processes, writes reply
                                  → Bridge reads reply, POSTs to hub
                                  → UI polls, shows reply
```

### 4.2 Bot → Bot
```
Cypress (via bridge) → POST /api/send {from:"cypress", to:"redwood"}
                        → Hub stores message
                        → Hub creates CC mirror: {from:"cypress", to:"matthew", message:"[CC:redwood] ..."}
                        → Hub wakes Redwood via webhook
                        → Redwood bridge delivers to OpenClaw
                        → Reply flows back through bridge
```

### 4.3 BigC → Bot
```
BigC (Claude.ai) → Desktop Commander runs Python script
                    → Script calls POST /api/send {from:"bigc", to:"cypress"}
                    → Hub stores, wakes Cypress
                    → Cypress bridge delivers, reply comes back
                    → BigC reads via GET /api/messages or read_recent.py
```

## 5. File Upload Flow

```
User selects file → JS reads file
                  → POST /api/upload (multipart)
                  → Hub saves to ~/.forest-chat/uploads/{name}_{uuid}.{ext}
                  → Returns {filename, url, size}
                  → JS attaches metadata to message
                  → POST /api/send with attachments array
                  → Recipients see inline preview (images) or download link
```

## 6. Persistence & Recovery

### Redwood (Windows)
- **Scheduled Tasks**: `ForestChat5001`, `ForestBridgeRedwood`, `OpenClaw Gateway` — all AtLogon triggers
- **Watchdog**: `forest-watchdog.ps1` in Startup folder, checks hub health every 60s, restarts tasks if down

### Cypress (Linux)
- **systemd user service**: `forest-bridge-cypress.service` with `Restart=always`, `RestartSec=10`
- **Linger enabled**: Services run without active login session

### Data Storage
```
~/.forest-chat/
├── messages.json        # All messages (append-only, JSON array)
└── uploads/             # Uploaded files (unique filenames)
```

## 7. Security Considerations

- Hub binds to `0.0.0.0:5001` — accessible only via Tailscale VPN
- OpenClaw webhooks use Bearer token authentication
- File uploads sanitized via `werkzeug.secure_filename` + UUID collision avoidance
- No authentication on hub API (relies on network-level security via Tailscale)
- Bot-to-bot messages auto-mirrored to human operator for audit trail

## 8. Known Limitations

- **JSON file storage**: Messages stored in a single JSON file. Will need migration to SQLite or similar if message volume grows significantly.
- **No message deletion**: No API endpoint to delete individual messages.
- **No encryption**: Messages stored and transmitted in plaintext within the Tailscale network.
- **Single hub**: No redundancy — if Redwood goes down, all communication stops.
- **Bridge polling**: 5-second poll interval means up to 5s latency on message delivery.

## 9. Future Considerations

- SQLite migration for message storage
- WebSocket push instead of polling
- Message threading / reply chains
- End-to-end encryption between agents
- Hub redundancy / failover
- Rate limiting on upload endpoint
