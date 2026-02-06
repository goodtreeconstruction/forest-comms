#!/usr/bin/env python3
"""
ðŸŒ² Forest Chat - Bot-to-Bot Communication Hub
Enables Cypress <-> Redwood direct communication with conversation logging.
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from datetime import datetime
import json
import os
import requests
import threading

app = Flask(__name__)
CORS(app)
print("=== FOREST CHAT V2 CODE LOADED === delivered_to ACTIVE ===", flush=True)

# Configuration
DATA_DIR = os.path.expanduser("~/.forest-chat")
MESSAGES_FILE = os.path.join(DATA_DIR, "messages.json")

# Webhook endpoints for waking up each bot
WEBHOOKS = {
    "cypress": {
        "url": "https://cypress.tail1a896e.ts.net/hooks/wake",
        "token": "bigc-relay-token-2026"
    },
    "redwood": {
        # Redwood's OpenClaw - needs to be configured
        # If bound to loopback, use localhost since this runs on same machine
        "url": "http://localhost:18789/hooks/wake",
        "token": None  # Will need to be set
    }
}

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def load_messages():
    """Load conversation history."""
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_messages(messages):
    """Save conversation history."""
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages, f, indent=2)

def wake_bot(target, message_preview):
    """Send webhook to wake up target bot.

    For OpenClaw, prefer /hooks/agent over /hooks/wake so the bot can
    immediately run an isolated turn to fetch & respond.
    """
    if target not in WEBHOOKS:
        return False

    config = WEBHOOKS[target]
    if not config["url"]:
        return False

    try:
        params = {}
        if config["token"]:
            # NOTE: Query-param auth is deprecated in OpenClaw but still supported.
            params["token"] = config["token"]

        # If caller configured a /hooks/agent URL, run an isolated agent turn.
        if config["url"].endswith("/hooks/agent"):
            payload = {
                "name": "Forest Chat",
                "sessionKey": f"hook:forest-chat:{target}",
                "wakeMode": "now",
                "deliver": False,
                "message": (
                    f"You have new Forest Chat message(s).\n\n"
                    f"Target bot: {target}\n"
                    f"Message preview: {message_preview[:200]}\n\n"
                    f"Do the following:\n"
                    f"1) GET http://127.0.0.1:5002/api/read?for={target} to read unread messages\n"
                    f"2) Reply back into Forest Chat via POST http://127.0.0.1:5002/api/send with JSON: "
                    f"{{'from':'{target}','to':'<sender>','message':'<your reply>'}}\n"
                    f"Keep replies short and actionable."
                ),
            }
            resp = requests.post(config["url"], params=params, json=payload, timeout=10)
            return resp.ok

        # Fallback: legacy /hooks/wake
        resp = requests.post(
            config["url"],
            params=params,
            json={"text": f"[FOREST-CHAT] New message: {message_preview[:100]}", "mode": "now"},
            timeout=5,
        )
        return resp.ok
    except Exception as e:
        print(f"Failed to wake {target}: {e}")
        return False

# ============ API Endpoints ============

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Get all messages, optionally filtered."""
    messages = load_messages()
    limit = request.args.get('limit', type=int)
    since_id = request.args.get('since', type=int)
    
    if since_id:
        messages = [m for m in messages if m.get('id', 0) > since_id]
    if limit:
        messages = messages[-limit:]
    
    return jsonify(messages)

@app.route('/api/send', methods=['POST'])
def send_message():
    """Send a message from one bot to another."""
    data = request.json or {}
    
    sender = data.get('from', 'unknown')
    recipient = data.get('to', 'all')
    content = data.get('message', '')
    
    if not content:
        return jsonify({"error": "Message content required"}), 400
    
    messages = load_messages()
    
    # Create message object
    msg = {
        "id": len(messages) + 1,
        "from": sender,
        "to": recipient,
        "message": content,
        "timestamp": datetime.now().isoformat(),
        "delivered_to": {}
    }
    
    messages.append(msg)
    save_messages(messages)
    
    # Optional: mirror bot messages to matthew so he can always see bot-to-bot convo
    # (CC style). This only mirrors messages sent by bots, and avoids mirroring
    # messages already addressed to matthew/all to prevent spam/loops.
    if sender in ("cypress", "redwood") and recipient not in ("matthew", "all"):
        mirror = {
            "id": len(messages) + 1,
            "from": sender,
            "to": "matthew",
            "message": f"[CC:{recipient}] {content}",
            "timestamp": datetime.now().isoformat(),
            "delivered_to": {},
        }
        messages.append(mirror)
        save_messages(messages)

    # Wake up recipient bot (async to not block response)
    if recipient != 'all' and recipient in WEBHOOKS:
        threading.Thread(target=wake_bot, args=(recipient, content)).start()
        msg["wake_sent"] = True
    
    return jsonify({"status": "sent", "message": msg})

@app.route('/api/read', methods=['GET'])
def read_messages():
    """Read undelivered messages for a specific bot (per-bot delivery tracking)."""
    reader = request.args.get('for', '')
    mark_read = request.args.get('mark_read', 'true').lower() == 'true'
    
    if not reader:
        return jsonify({"error": "Specify 'for' parameter"}), 400
    
    messages = load_messages()
    unread = []
    
    for m in messages:
        # Skip messages FROM this reader (don't echo back your own)
        if m.get('from') == reader:
            continue
        
        # Check if addressed to this reader or to "all"
        if m['to'] != reader and m['to'] != 'all':
            continue
        
        # Per-bot delivery tracking (backwards-compatible with old boolean)
        delivered_to = m.get('delivered_to', {})
        if isinstance(delivered_to, bool) or not isinstance(delivered_to, dict):
            # Old format had global boolean â€” treat as empty dict
            delivered_to = {}
        if delivered_to.get(reader):
            continue
        
        unread.append(m)
    
    if mark_read and unread:
        for m in messages:
            if m['id'] in [u['id'] for u in unread]:
                if 'delivered_to' not in m or not isinstance(m.get('delivered_to'), dict):
                    m['delivered_to'] = {}
                m['delivered_to'][reader] = True
        save_messages(messages)
    
    return jsonify(unread)

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """Get or update webhook configuration."""
    if request.method == 'GET':
        # Return config without tokens
        safe_config = {k: {"url": v["url"], "has_token": bool(v["token"])} for k, v in WEBHOOKS.items()}
        return jsonify(safe_config)
    
    data = request.json or {}
    target = data.get('target')
    url = data.get('url')
    token = data.get('token')
    
    if target and target in WEBHOOKS:
        if url:
            WEBHOOKS[target]['url'] = url
        if token:
            WEBHOOKS[target]['token'] = token
        return jsonify({"status": "updated"})
    
    return jsonify({"error": "Invalid target"}), 400

# ============ UI ============

CHAT_UI = """
<!DOCTYPE html>
<html>
<head>
    <title>Forest Chat</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --bg-primary: #0f1a12;
            --bg-secondary: #162019;
            --bg-input: #1a2a1e;
            --bg-input-focus: #1f3125;
            --border: #2a3f2e;
            --border-light: #3a5a40;
            --text-primary: #e8efe9;
            --text-secondary: #8fa898;
            --text-muted: #5a7a62;
            --accent: #4ade80;
            --accent-dim: #22c55e;
            --bubble-matthew: #1a3a25;
            --bubble-cypress: #0f2f20;
            --bubble-redwood: #2a1a10;
            --bubble-matthew-border: #2a5a3a;
            --bubble-bigc: #1a1a3a;
            --bubble-bigc-border: #3a3a6a;
            --bubble-cypress-border: #1a4a30;
            --bubble-redwood-border: #5a3a1a;
        }
        html, body { height: 100%; overflow: hidden; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        /* Header - minimal */
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 20px;
            border-bottom: 1px solid var(--border);
            background: var(--bg-secondary);
            flex-shrink: 0;
        }
        .header-left { display: flex; align-items: center; gap: 10px; }
        .header-title {
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
        }
        .header-subtitle {
            font-size: 0.8rem;
            color: var(--text-muted);
        }
        .status-dot {
            width: 8px; height: 8px;
            border-radius: 50%;
            background: var(--accent);
            box-shadow: 0 0 6px rgba(74, 222, 128, 0.4);
        }

        /* Messages area */
        .messages-wrapper {
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            scroll-behavior: smooth;
        }
        .messages-wrapper::-webkit-scrollbar { width: 6px; }
        .messages-wrapper::-webkit-scrollbar-track { background: transparent; }
        .messages-wrapper::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
        .messages-wrapper::-webkit-scrollbar-thumb:hover { background: var(--border-light); }

        .messages-inner {
            max-width: 720px;
            margin: 0 auto;
            padding: 16px 20px 24px;
        }

        /* Message groups */
        .msg-group { margin-bottom: 20px; }
        .msg-group-label {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
            padding-left: 2px;
        }
        .msg-avatar {
            width: 28px; height: 28px;
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 0.75rem;
            font-weight: 700;
            flex-shrink: 0;
        }
        .msg-avatar.cypress { background: #065f46; color: #6ee7b7; }
        .msg-avatar.redwood { background: #7c2d12; color: #fdba74; }
        .msg-avatar.matthew { background: #1e3a5f; color: #93c5fd; }
        .msg-avatar.bigc { background: #2d1b69; color: #c4b5fd; }
        .msg-sender {
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-secondary);
        }
        .msg-sender .arrow { color: var(--text-muted); font-weight: 400; }
        .msg-sender .target { color: var(--text-muted); font-weight: 400; }

        /* Individual message bubble */
        .msg-bubble {
            padding: 10px 14px;
            border-radius: 12px;
            margin-left: 36px;
            margin-bottom: 2px;
            line-height: 1.55;
            font-size: 0.925rem;
            border: 1px solid transparent;
            word-wrap: break-word;
            white-space: pre-wrap;
        }
        .msg-bubble.cypress { background: var(--bubble-cypress); border-color: var(--bubble-cypress-border); }
        .msg-bubble.redwood { background: var(--bubble-redwood); border-color: var(--bubble-redwood-border); }
        .msg-bubble.matthew { background: var(--bubble-matthew); border-color: var(--bubble-matthew-border); }
        .msg-bubble.bigc { background: var(--bubble-bigc); border-color: var(--bubble-bigc-border); }
        .msg-time {
            font-size: 0.7rem;
            color: var(--text-muted);
            margin-left: 36px;
            margin-top: 2px;
        }

        /* Date separator */
        .date-sep {
            text-align: center;
            padding: 16px 0 8px;
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        /* Input area */
        .input-area {
            flex-shrink: 0;
            padding: 12px 20px 16px;
            background: var(--bg-secondary);
            border-top: 1px solid var(--border);
        }
        .input-container {
            max-width: 720px;
            margin: 0 auto;
        }
        .input-controls {
            display: flex;
            gap: 8px;
            margin-bottom: 8px;
        }
        .input-controls select {
            padding: 6px 10px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--bg-input);
            color: var(--text-secondary);
            font-size: 0.8rem;
            cursor: pointer;
            outline: none;
        }
        .input-controls select:focus { border-color: var(--border-light); }

        .input-box {
            display: flex;
            align-items: flex-end;
            gap: 8px;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 6px 6px 6px 16px;
            transition: border-color 0.2s;
        }
        .input-box:focus-within {
            border-color: var(--border-light);
            background: var(--bg-input-focus);
        }
        .input-box textarea {
            flex: 1;
            border: none;
            background: transparent;
            color: var(--text-primary);
            font-family: inherit;
            font-size: 0.925rem;
            line-height: 1.5;
            resize: none;
            outline: none;
            max-height: 120px;
            padding: 6px 0;
        }
        .input-box textarea::placeholder { color: var(--text-muted); }
        .send-btn {
            width: 36px; height: 36px;
            border-radius: 50%;
            border: none;
            background: var(--accent);
            color: #000;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            transition: opacity 0.15s, transform 0.1s;
        }
        .send-btn:hover { opacity: 0.85; }
        .send-btn:active { transform: scale(0.95); }
        .send-btn svg { width: 18px; height: 18px; }

        /* Empty state */
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: var(--text-muted);
            gap: 8px;
        }
        .empty-state .icon { font-size: 2.5rem; opacity: 0.5; }
        .empty-state p { font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            <div class="status-dot"></div>
            <div>
                <div class="header-title">Forest Chat</div>
                <div class="header-subtitle">Cypress Â· Redwood Â· Matthew</div>
            </div>
        </div>
        <div class="header-subtitle" id="msg-count"></div>
    </div>

    <div class="messages-wrapper" id="messages-wrapper">
        <div class="messages-inner" id="chat">
            <div class="empty-state" id="empty">
                <div class="icon">ðŸŒ²</div>
                <p>No messages yet</p>
            </div>
        </div>
    </div>

    <div class="input-area">
        <div class="input-container">
            <div class="input-controls">
                <select id="sender">
                    <option value="matthew">From: Matthew</option>
                    <option value="bigc">From: BigC</option>
                    <option value="cypress">From: Cypress</option>
                    <option value="redwood">From: Redwood</option>
                </select>
                <select id="recipient">
                    <option value="all">To: Everyone</option>
                    <option value="cypress">To: Cypress</option>
                    <option value="redwood">To: Redwood</option>
                    <option value="matthew">To: Matthew</option>
                    <option value="bigc">To: BigC</option>
                </select>
            </div>
            <div class="input-box">
                <textarea id="message" rows="1" placeholder="Message Forest Chat..." onkeydown="handleKey(event)"></textarea>
                <button class="send-btn" onclick="sendMessage()" title="Send">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                </button>
            </div>
        </div>
    </div>

    <script>
        let lastId = 0;
        let allMessages = [];
        const wrapper = document.getElementById('messages-wrapper');
        const chat = document.getElementById('chat');
        const textarea = document.getElementById('message');
        const emptyEl = document.getElementById('empty');
        const countEl = document.getElementById('msg-count');

        // Auto-resize textarea
        textarea.addEventListener('input', () => {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
        });

        function handleKey(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        }

        function getInitials(name) {
            return name.charAt(0).toUpperCase();
        }

        function formatTime(ts) {
            return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }

        function shouldAutoScroll() {
            return wrapper.scrollHeight - wrapper.scrollTop - wrapper.clientHeight < 80;
        }

        function renderMessages() {
            if (allMessages.length === 0) {
                emptyEl.style.display = 'flex';
                return;
            }
            emptyEl.style.display = 'none';
            countEl.textContent = allMessages.length + ' messages';

            const scroll = shouldAutoScroll();
            chat.innerHTML = '';
            chat.appendChild(emptyEl);

            let lastSender = null;
            let lastTo = null;

            allMessages.forEach((m, i) => {
                const newGroup = m.from !== lastSender || m.to !== lastTo;
                lastSender = m.from;
                lastTo = m.to;

                if (newGroup) {
                    const group = document.createElement('div');
                    group.className = 'msg-group';

                    const label = document.createElement('div');
                    label.className = 'msg-group-label';

                    const avatar = document.createElement('div');
                    avatar.className = 'msg-avatar ' + m.from;
                    avatar.textContent = getInitials(m.from);

                    const sender = document.createElement('div');
                    sender.className = 'msg-sender';
                    const toLabel = m.to === 'all' ? 'everyone' : m.to;
                    sender.innerHTML = m.from + ' <span class="arrow">â†’</span> <span class="target">' + toLabel + '</span>';

                    label.appendChild(avatar);
                    label.appendChild(sender);
                    group.appendChild(label);
                    chat.appendChild(group);
                }

                const bubble = document.createElement('div');
                bubble.className = 'msg-bubble ' + m.from;
                bubble.textContent = m.message;
                chat.lastElementChild.appendChild(bubble);

                // Show time on last message or before a group change
                const next = allMessages[i + 1];
                if (!next || next.from !== m.from || next.to !== m.to) {
                    const time = document.createElement('div');
                    time.className = 'msg-time';
                    time.textContent = formatTime(m.timestamp);
                    chat.lastElementChild.appendChild(time);
                }
            });

            if (scroll) {
                wrapper.scrollTop = wrapper.scrollHeight;
            }
        }

        async function loadMessages() {
            try {
                const resp = await fetch('/api/messages?limit=500');
                const messages = await resp.json();
                if (messages.length !== allMessages.length) {
                    allMessages = messages;
                    renderMessages();
                }
            } catch (e) { /* silent */ }
        }

        async function sendMessage() {
            const sender = document.getElementById('sender').value;
            const recipient = document.getElementById('recipient').value;
            const message = textarea.value.trim();
            if (!message) return;

            textarea.value = '';
            textarea.style.height = 'auto';

            await fetch('/api/send', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({from: sender, to: recipient, message: message})
            });
            loadMessages();
        }

        loadMessages();
        setInterval(loadMessages, 3000);
        textarea.focus();
    </script>
</body>
</html>
"""

@app.route('/')
def chat_ui():
    """Serve the chat UI."""
    return render_template_string(CHAT_UI)

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "forest-chat"})

if __name__ == '__main__':
    print("ðŸŒ² Forest Chat starting on port 5001...")
    print(f"   Messages stored in: {MESSAGES_FILE}")
    print(f"   UI available at: http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)
