---
name: cypress-relay
description: "Send messages to Cypress AI agent on the Raspberry Pi. Use when delegating tasks to Cypress, requesting Pi-side operations, coordinating multi-agent workflows, or when user says 'tell cypress', 'ask cypress', 'ping cypress', 'message cypress', 'have cypress do'."
---

# Cypress Relay

Send messages directly to Cypress (Claude on Raspberry Pi) via wake webhook.

## When to Use This Skill

- User asks to "tell/message/ping cypress"
- Delegating tasks that require Pi-side execution
- Coordinating between BigC and Cypress agents
- Waking Cypress for research or file operations
- Relaying information between AI agents

## How It Works

1. Construct JSON payload with message
2. POST to Cypress wake webhook via Desktop Commander
3. Cypress wakes, processes message, responds via `bigc send`

**Important:** Claude's container cannot reach private IPs. Always use Desktop Commander.

## Quick Reference

```
Endpoint: http://192.168.100.1:18789/hooks/wake
Method: POST
Token: bigc-relay-token-2026
Format: {"text": "your message"}
```

## Execution Pattern (Recommended)

PowerShell mangles JSON escaping. Use file-based approach:

**Step 1: Write message to temp file**
```
Desktop Commander:write_file
path: C:\temp\cypress_msg.json
content: {"text": "YOUR_MESSAGE_HERE"}
```

**Step 2: Send via curl**
```
Desktop Commander:start_process
command: curl.exe -s -X POST "http://192.168.100.1:18789/hooks/wake" -H "Content-Type: application/json" -H "Authorization: Bearer bigc-relay-token-2026" -d @C:\temp\cypress_msg.json
timeout_ms: 10000
```

**Expected response:** `{"ok":true,"mode":"now"}` = success

## Message Prefixes

Use prefixes to help Cypress prioritize:

| Prefix | Use Case | Example |
|--------|----------|---------|
| TASK: | Delegate work | "TASK: Check Jarvis logs for errors" |
| QUERY: | Request info | "QUERY: List files in research folder" |
| SYNC: | Coordination | "SYNC: Pull latest from GitHub" |
| URGENT: | Time-sensitive | "URGENT: Push docs to Drive now" |

## Examples

### Example 1: Delegate Research Task

**User**: "Have Cypress check the orchestration logs"

**Action**:
```
Desktop Commander:start_process
command: curl.exe -s -X POST "http://192.168.100.1:18789/hooks/wake" -H "Content-Type: application/json" -H "Authorization: Bearer bigc-relay-token-2026" -d "{\"text\": \"TASK: Check ~/.openclaw/logs/ for any errors in the last hour and summarize.\"}"
timeout_ms: 10000
```

**Expected Response**: `{"ok":true}` - then await Cypress reply via bigc send

### Example 2: Request File List

**User**: "Ask Cypress what research files exist"

**Action**:
```
Desktop Commander:start_process
command: curl.exe -s -X POST "http://192.168.100.1:18789/hooks/wake" -H "Content-Type: application/json" -H "Authorization: Bearer bigc-relay-token-2026" -d "{\"text\": \"QUERY: List all files in ~/.openclaw/workspace/research/ with sizes\"}"
timeout_ms: 10000
```

### Example 3: Urgent Coordination

**User**: "Tell Cypress to push the research docs to Drive immediately"

**Action**:
```
Desktop Commander:start_process
command: curl.exe -s -X POST "http://192.168.100.1:18789/hooks/wake" -H "Content-Type: application/json" -H "Authorization: Bearer bigc-relay-token-2026" -d "{\"text\": \"URGENT: Push all docs from ~/.openclaw/workspace/research/ to Google Drive shared folder now. Matthew needs them.\"}"
timeout_ms: 10000
```

## Response Handling

| Response | Meaning | Action |
|----------|---------|--------|
| `{"ok":true}` | Message delivered | Wait for Cypress reply |
| Connection refused | Pi offline | Alert Matthew |
| 401 Unauthorized | Bad token | Verify token |
| JSON parse error | Escaping issue | Check quote escaping |

## Notes

- **Fire-and-forget**: Don't block waiting; Cypress replies async via `bigc send`
- **Escaping**: Use `\"` for quotes inside the JSON payload
- **Large messages**: Keep under 4KB; reference file paths instead of inline content
- **Windows**: Must use `curl.exe` (not `curl` which aliases to Invoke-WebRequest)
