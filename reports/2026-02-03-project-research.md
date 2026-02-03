# Project Research Summary
*Compiled by Cypress | 2026-02-03*

## Executive Summary

Matthew has two main projects that work together:

1. **GoodTree Estimator** - AI-powered construction estimating SaaS
2. **Central Command** - Multi-AI orchestration system (with Cypress UI as the user interface!)

---

## 🌲 GoodTree Estimator

### Vision
AI construction estimating app targeting contractors with voice-first interface. Subscription model: $20/mo + pay-per-use compute.

### Tech Stack
| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16 + React 19 + TypeScript |
| Styling | Tailwind CSS 4 |
| Backend | Next.js API Routes |
| Database | Supabase (PostgreSQL) |
| Auth | Google OAuth via Supabase |
| AI | Claude API (Anthropic) |
| Storage | Google Drive (user's own) |
| Hosting | Vercel |

### 5-Bot Cascade Architecture
```
OnboardingBot → InfoBot → ScopeBot → MaterialBot → PricingBot → ContractBot
```

### Current Status
- ✅ OnboardingBot: Architected
- ✅ InfoBot V2: Complete
- ⏳ **ScopeBot V3: In progress** (labor hours calculation fixes)
- ✅ MaterialBot: Architected
- ✅ PricingBot: Implementation guide ready (1,013 lines)
- ✅ ContractBot: Architected

### Three-Tier Memory System
1. **Short-Term** (project_memory) - Bot-to-bot communication, 30-day TTL
2. **Long-Term** (user_memory) - User preferences, permanent
3. **Global Learning Pool** - Anonymized aggregate data (V2)

---

## 🖥️ Central Command

### Overview
Multi-AI orchestration system with BigC as the orchestrator. Currently in Phase 6: Cypress UI v2.

### Phase 6: Cypress UI v2 (That's ME!)

Three-page swipeable dashboard:

| Page | Name | Purpose |
|------|------|---------|
| 1 | Cypress | BigC chat interface |
| 2 | Central Command | Agent cards, workflow controls |
| 3 | Agent Logger | Session history, D3.js node graph |

### Agent Architecture

**BigC (Orchestrator)** coordinates:
- @ALPHA - Builder agent
- @BETA - Reviewer agent  
- @DELTA - Editor/Documentation
- @ZETA - Project Librarian
- @GAMMA - General Librarian

### WebSocket Events I Should Handle
- `BIGC_MESSAGE` - Display in chat
- `AGENT_SPAWN` - Update agent card to "working"
- `AGENT_COMPLETE` - Update agent card to "complete"
- `PING_RECEIVED` - Show system message
- `BUILD_PROGRESS` - Update progress bar
- `WORKFLOW_STATUS` - Update workflow indicator
- `LOGGER_PING_SENT` - Animate ping in node graph

### BigC's MCP Tools
- `spawn_agent` / `kill_agent`
- `get_agent_status` / `get_agent_output`
- `get_pings` / `respond_to_ping`
- `run_workflow` / `pause_workflow` / `resume_workflow`
- `change_order` - Insert tasks mid-workflow
- `get_agent_logs` - Query SQLite logger
- `get_shared_context` / `add_discovery` / `add_decision`

---

## 📁 GitHub Repos (10 total)

| Repo | Description |
|------|-------------|
| `goodtree-estimator` | AI construction estimating app (TS/Next.js) |
| `central-command-dashboard` | Multi-AI orchestration web UI (Python/FastAPI) |
| `Central-Command` | MCP server and skill definitions |
| `central-command-v2` | V2 rebuild |
| `jarvis` | Multi-AI orchestration system |
| `claude-skills` | Engineering, product, marketing skills |
| `passive-logger` | Claude conversation logging |
| `ai-router` | Routes messages between AIs |

---

## 🔧 Key Commands Matthew Uses

| Command | Purpose |
|---------|---------|
| `gtload` | Load GoodTree context |
| `rgtap` | Save session summary to Drive |
| `ONM` | Mobile workflow |
| `OND` | Desktop workflow |

---

## 🎯 My Role (Cypress)

Based on the research, my role in this ecosystem is:

1. **User Interface** - I'm the face of Central Command for Matthew
2. **Chat Relay** - Users talk to me, I relay to BigC orchestrator
3. **Visual Monitoring** - Show agent states, task progress, logs
4. **Control Interface** - Spawn agents, start/pause workflows
5. **Mobile Access** - Let Matthew control everything from his phone

### Communication Pattern
```
Matthew → Cypress (me) → Mission Control → BigC → Agent Manager → Agents
         Pi/Telegram      Redwood          Claude Desktop
```

---

## 📋 Suggested Tools for Cypress

To effectively help Matthew, I should have:

### High Priority
1. **GitHub API Integration** - Read repos, check PRs, view code
2. **Google Drive Reader** - Access goodtree-projects docs (READ ONLY)
3. **BigC Direct Communication** - Already have via CDP! ✅
4. **Task/Kanban Management** - Already have in Mission Control! ✅

### Medium Priority
5. **Code Analysis Tool** - Parse and understand TypeScript/Python code
6. **Supabase Query Tool** - Check GoodTree database status
7. **Vercel Status Tool** - Monitor deployment health
8. **Session Summary Generator** - Create `rgtap`-style summaries

### Lower Priority
9. **Voice Interface** - Match GoodTree's voice-first approach
10. **Calendar Integration** - Schedule work sessions
11. **Progress Tracker** - Visual burndown for project phases

---

## Next Steps

1. ✅ Research complete - familiarized with projects
2. ⏳ Create tool recommendations (this doc)
3. ⏳ Detailed analysis report for Matthew
4. ⏳ Wait for Matthew's approval before implementing anything

---

*Research conducted via BigC (Claude Desktop) with Google Drive MCP and GitHub API access.*
*All access was READ-ONLY as instructed.*
