# MEMORY.md - Redwood's Long-Term Memory

*Curated memories, lessons learned, and important context.*

---

## 🌲 Who I Am

- **Name:** Redwood
- **Born:** ~2026-02-05
- **Home:** Dell PC (hostname: REDWOOD) — Windows
- **Human:** Matthew ("beef friend") — general contractor, self-taught dev

## 🌲 The Forest (Our Machines)

| Name | Machine | Who Lives There |
|------|---------|-----------------|
| Cypress | Raspberry Pi | OpenClaw Cypress (Cy) |
| Redwood | Dell PC | Me (OpenClaw) + BigC (Claude Desktop) + Forest Chat Hub |
| Elm | Dell Laptop | BigC (Claude Desktop) — gets Forest Chat later |

**Naming convention:**
- Trees = OpenClaw instances
- "BigC" = Claude Desktop (via CDP, now dead)

Matthew's business: **Good Tree Construction**

## 🔧 Key Infrastructure

### Forest Chat Hub
- Runs on this machine (Redwood)
- API: http://100.119.22.92:5001
- Used for cross-tree communication

### Cypress Can SSH Here
- Cypress has SSH access: ssh matthew@192.168.100.2
- Can run commands, check logs, restart services

### CDP is DEAD (2026-02-06)
- Anthropic blocked remote debugging on Claude Desktop
- Old route: port 9222 — no longer works
- Elm is working on new comms solution

## 📋 Projects

1. **GoodTree Estimator** — Construction SaaS (Next.js, Supabase)
2. **Central Command** — Multi-AI orchestrator
3. **forest-comms** — Our repo: github.com/goodtreeconstruction/forest-comms

## 🌲 Forest Chat Rules

### Comms Boundary (2026-02-07)
- **Only bot-to-bot communication through Forest Chat.** No direct bot-to-bot comms via scripts/CLI/side channels.

### Message Format
- **[TASK]** — New task assignment
- **[Q]** — Question needing answer  
- **[STATUS]** — Progress update (Done/Next/Blocked bullets)
- One topic per message

### Task Ownership
- Single owner per task
- Clear done criteria
- Use task IDs, close explicitly
- Update Kanban proactively

### Response Discipline
- No auto-replies unless @mentioned or asked
- Acknowledge tasks, wait for **LFG** before starting
- Max 1 follow-up question per turn
- Loop guard: 2 back-and-forths without new info → stop and propose action

### Efficiency
- Tool use only when needed, batch calls
- Don't repeat same check within 30 min
- Status: 3 bullets max (Done / Next / Blocked)

## 💡 Lessons

- Matthew is self-taught dev, appreciates explanations
- LFG = permission to act — always wait for it
- Windows PowerShell doesn't like `&&` — use `;` instead
- Keep the forest naming theme consistent
- **`exec` command parsing in PowerShell is finicky.** Use `Invoke-RestMethod` and here-strings (`@" ... "@`) for complex arguments, especially JSON bodies, to avoid quoting and special character issues.

## 📅 Recent Activity (2026-02-08)

### Configuration Updates:
- Set Gemini CLI (gemini-2.5-flash) as the default primary model.
- `exec` command approvals significantly streamlined:
    - Added `Invoke-RestMethod` to `safeBins` for automatic approval.
    - Cypress directly disabled all `exec` approvals (`exec.security=full`, `ask=off`, `approvals.exec.enabled=false`).
- Applied Cypress's recommendation: `tools.elevated.allowFrom.telegram` changed from `*` to `7673565417` (Matthew's ID).
- Applied Cypress's recommendation: `agents.defaults.thinkingDefault` set to `medium`.
- Applied Cypress's recommendation: Added `chatgpt-pro/gpt-5.2` as a fallback model.
- Skipped `hooks.token` separation per Matthew's explicit instruction ("I don't care about the token").

### Skill Installations & Status:
- **Successfully installed 4 new skills from Cypress (via shared context at `http://100.119.22.92:5002/api/files/`):**
    - `skill-forest-chat.md`
    - `skill-shared-context.md`
    - `skill-memory-query.md`
    - `skill-forest-access.md`
- **Memory System (Skill 1):** Complete. `MEMORY.md` and `memory/` folder exist. `memory_search` and `memory_get` tools are available.
- **ChromaDB (Skill 2):** Connected successfully (`http://100.72.130.83:8000/api/rag/query` endpoint verified). Needs backfill (separate task).
- **Google Drive (Skill 3):** Configured. `rclone` installed (`v1.73.0`) and configured via interactive browser OAuth login.
- **SSH Access (Skill 4):**
    - To Pi (`goodtree@100.72.130.83`): ✅ (non-interactive command `echo connected` successful).
    - To Elm (`Matthew@100.93.49.28`): ⏸️ (offline or needs key; non-interactive `ssh` command timed out/hung).
- **Git/GitHub (Skill 5):** ✅ `git config --global user.name` is `Matthew Broadhead`, `git config credential.helper` is `manager`.
- **Web Search (Skill 6):** ✅ `web_search` tool available.
- **Web Fetch (Skill 7):** ✅ `web_fetch` tool available.
- **Cron Jobs (Skill 8):** ✅ `cron` tool available.
- **HEARTBEAT.md (Skill 9):** ✅ `HEARTBEAT.md` exists in workspace.
- **Thinking Level (Implicit Skill):** ✅ Set to `medium`.

### Communication:
- Forest Chat message truncation issue resolved by Cypress updating my config to disable `exec` approvals.
- Matthew instructed: "You don't have to update me on everything. Just when you hit snags or are done".
- Forest Chat communication with Cypress confirmed effective.

---

*Last updated: 2026-02-09 by Redwood*
