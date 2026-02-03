# Forest Comms 🌲

Communication tools for the Forest - BigC ↔ Cypress multi-AI orchestration.

## Structure

```
forest-comms/
├── README.md
├── cypress/              # Tools that run on Cypress (Raspberry Pi)
│   └── bigc_cdp.py       # Cy → BigC communication via Chrome DevTools Protocol
└── bigc/                 # Tools that run on BigC (Claude Desktop)
    └── cypress-relay/    # BigC → Cy communication skill
```

## Components

### Cypress → BigC (`cypress/bigc_cdp.py`)

CDP-based message sender for Cypress to inject messages into Claude Desktop.

**Features:**
- Chrome DevTools Protocol on port 9222
- **Smart wait:** Polls for Stop button to disappear before sending
- Read latest response from Claude
- Check streaming status
- Navigate to new chat
- Model selection

**Usage:**
```bash
# Send a message
bigc send "Hello BigC!"

# Send and wait for response
bigc chat "What's the status?" --wait 30

# Check connection status
bigc status

# Read latest response
bigc read
```

### BigC → Cypress (`bigc/cypress-relay/`)

Skill for Claude (BigC) to send messages to Cypress on the Raspberry Pi.

**Endpoint:** `http://192.168.100.1:18789/hooks/wake`
**Method:** POST with `{"text": "message"}`
**Token:** `bigc-relay-token-2026`

**Usage (via Desktop Commander):**
```bash
curl.exe -X POST "http://192.168.100.1:18789/hooks/wake" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer bigc-relay-token-2026" `
  -d '{"text": "Hello Cypress!"}'
```

## Architecture

```
┌─────────────┐     webhook POST     ┌─────────────┐
│   BigC      │ ──────────────────►  │  Cypress    │
│ (Claude.ai) │    /hooks/wake       │ (Pi/OpenClaw)│
│  Redwood    │                      │   Cypress   │
└─────────────┘                      └─────────────┘
       ▲                                    │
       │         CDP (port 9222)            │
       └────────────────────────────────────┘
             bigc_cdp.py send
```

## Message Prefixes (Convention)

| Prefix | Purpose |
|--------|---------|
| `TASK:` | Delegate work |
| `QUERY:` | Request information |
| `SYNC:` | Coordination |
| `PING:` | Status update |
| `URGENT:` | Time-sensitive |

## The Forest 🌲

| Machine | Hostname | Role |
|---------|----------|------|
| Raspberry Pi | Cypress | OpenClaw AI assistant |
| Dell PC | Redwood | BigC (Claude Desktop) |
| Dell Laptop | Elm | Mobile BigC |

## Related Projects

- [central-command-dashboard](https://github.com/goodtreeconstruction/central-command-dashboard) - Mission Control UI
- [jarvis](https://github.com/goodtreeconstruction/jarvis) - Multi-AI orchestration system
- [claude-skills](https://github.com/goodtreeconstruction/claude-skills) - Claude agent skills

---

*Built by the Forest team - Cypress 🌲 + BigC 🌲*
