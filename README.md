# Forest Comms 🌲

Communication tools for BigC ↔ Cypress multi-AI orchestration.

## Components

### BigC → Cypress (`cypress-relay/`)
Skill for Claude (BigC) to send messages to Cypress on the Raspberry Pi.

- **Endpoint:** `http://192.168.100.1:18789/hooks/wake`
- **Method:** POST with `{"text": "message"}`
- **Token:** `bigc-relay-token-2026`

### Cypress → BigC (`bigc_cdp.py`)
CDP-based message sender for Cypress to inject messages into Claude Desktop.

- Uses Chrome DevTools Protocol on port 9222
- Smart wait: polls for Stop button to disappear before sending
- Appends to existing input (never replaces)

## Architecture

```
┌─────────────┐     webhook      ┌─────────────┐
│   BigC      │ ───────────────► │  Cypress    │
│ (Claude.ai) │                  │ (Pi/OpenClaw)│
└─────────────┘                  └─────────────┘
       ▲                                │
       │         CDP (port 9222)        │
       └────────────────────────────────┘
```

## Usage

### BigC sending to Cypress:
```bash
curl -X POST "http://192.168.100.1:18789/hooks/wake" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer bigc-relay-token-2026" \
  -d '{"text": "TASK: Check the logs"}'
```

### Cypress sending to BigC:
```python
from bigc_cdp import send_to_bigc
send_to_bigc("PING: Task complete!")
```

## Message Prefixes

| Prefix | Purpose |
|--------|---------|
| `TASK:` | Delegate work |
| `QUERY:` | Request information |
| `SYNC:` | Coordination |
| `PING:` | Status update |
| `URGENT:` | Time-sensitive |

## Related Projects

- [central-command-dashboard](https://github.com/goodtreeconstruction/central-command-dashboard) - Mission Control UI
- [jarvis](https://github.com/goodtreeconstruction/jarvis) - Multi-AI orchestration system
- [claude-skills](https://github.com/goodtreeconstruction/claude-skills) - Claude agent skills

