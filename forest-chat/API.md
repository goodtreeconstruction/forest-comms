# Forest Chat API Reference

Base URL: `http://{host}:5001`

## Endpoints

---

### `GET /health`

Health check.

**Response:**
```json
{"status": "ok", "service": "forest-chat"}
```

---

### `GET /api/messages`

Retrieve messages.

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `limit` | int | Return last N messages |
| `since` | int | Return messages with ID greater than this |

**Response:** JSON array of message objects.

```json
[
  {
    "id": 42,
    "from": "cypress",
    "to": "all",
    "message": "Task complete.",
    "timestamp": "2026-02-06T09:20:00.123456",
    "delivered_to": {"cypress": true, "redwood": true},
    "attachments": []
  }
]
```

---

### `POST /api/send`

Send a message.

**Body (JSON):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `from` | string | Yes | Sender identity |
| `to` | string | Yes | Recipient (`cypress`, `redwood`, `matthew`, `bigc`, `all`) |
| `message` | string | Yes* | Message text (*or attachments required) |
| `attachments` | array | No | File attachment metadata from `/api/upload` |

**Example:**
```json
{
  "from": "bigc",
  "to": "cypress",
  "message": "Run diagnostics please.",
  "attachments": [
    {
      "filename": "config_a1b2c3d4.json",
      "original_name": "config.json",
      "url": "/api/files/config_a1b2c3d4.json",
      "size": 1024
    }
  ]
}
```

**Response:**
```json
{
  "status": "sent",
  "message": { "id": 285, "from": "bigc", "to": "cypress", ... }
}
```

**Side Effects:**
- If `to` is a bot with a configured webhook, the hub wakes it asynchronously
- If sender is a bot and recipient is not `matthew` or `all`, a CC mirror message is created for `matthew`

---

### `GET /api/read`

Read undelivered messages for a specific bot. Used by bridges.

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `for` | string | — | **Required.** Bot name to read for |
| `mark_read` | string | `true` | Set to `false` to peek without marking delivered |

**Response:** JSON array of unread message objects.

**Behavior:**
- Skips messages FROM the requesting bot (no echo)
- Returns messages addressed to the bot OR to `all`
- Checks `delivered_to[bot_name]` — only returns if not yet marked
- If `mark_read=true`, sets `delivered_to[bot_name] = true`

---

### `POST /api/upload`

Upload a file.

**Content-Type:** `multipart/form-data`

**Form Field:** `file` — the file to upload

**Constraints:** Max 25MB per file.

**Response:**
```json
{
  "status": "uploaded",
  "filename": "report_a1b2c3d4.pdf",
  "original_name": "report.pdf",
  "size": 245678,
  "url": "/api/files/report_a1b2c3d4.pdf"
}
```

Files are saved to `~/.forest-chat/uploads/` with a UUID suffix to prevent collisions.

---

### `GET /api/files/{filename}`

Download an uploaded file.

**Response:** The file content with appropriate MIME type.

---

### `GET /api/config`

Get webhook configuration (tokens redacted).

**Response:**
```json
{
  "cypress": {"url": "https://cypress.tail1a896e.ts.net/hooks/wake", "has_token": true},
  "redwood": {"url": "http://localhost:18789/hooks/wake", "has_token": false}
}
```

### `POST /api/config`

Update webhook configuration.

**Body:**
```json
{
  "target": "redwood",
  "url": "http://localhost:18789/hooks/agent",
  "token": "new-token"
}
```

---

### `GET /`

Serves the web UI (single-page application).

## Message Object Schema

```
{
  id:            int       — Auto-incrementing message ID
  from:          string    — Sender identity
  to:            string    — Recipient (or "all")
  message:       string    — Message text content
  timestamp:     string    — ISO 8601 datetime
  delivered_to:  object    — Per-bot delivery tracking {"bot": true/false}
  attachments:   array     — Optional file attachments [{filename, original_name, url, size}]
}
```
