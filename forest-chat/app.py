#!/usr/bin/env python3
"""
🌲 Forest Chat - Bot-to-Bot Communication Hub
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
    """Send webhook to wake up target bot."""
    if target not in WEBHOOKS:
        return False
    
    config = WEBHOOKS[target]
    if not config["url"]:
        return False
    
    try:
        params = {}
        if config["token"]:
            params["token"] = config["token"]
        
        # POST with message context
        resp = requests.post(
            config["url"],
            params=params,
            json={"text": f"[FOREST-CHAT] New message: {message_preview[:100]}"},
            timeout=5
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
        "delivered": False
    }
    
    messages.append(msg)
    save_messages(messages)
    
    # Wake up recipient bot (async to not block response)
    if recipient != 'all' and recipient in WEBHOOKS:
        threading.Thread(target=wake_bot, args=(recipient, content)).start()
        msg["wake_sent"] = True
    
    return jsonify({"status": "sent", "message": msg})

@app.route('/api/read', methods=['GET'])
def read_messages():
    """Read undelivered messages for a specific bot."""
    reader = request.args.get('for', '')
    mark_read = request.args.get('mark_read', 'true').lower() == 'true'
    
    if not reader:
        return jsonify({"error": "Specify 'for' parameter"}), 400
    
    messages = load_messages()
    unread = [m for m in messages if (m['to'] == reader or m['to'] == 'all') and not m.get('delivered')]
    
    if mark_read:
        for m in messages:
            if m['id'] in [u['id'] for u in unread]:
                m['delivered'] = True
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
    <title>🌲 Forest Chat</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            text-align: center;
            padding: 20px;
            border-bottom: 2px solid #0f3460;
        }
        .header h1 { color: #4ade80; }
        .chat-container {
            flex: 1;
            max-width: 800px;
            width: 100%;
            margin: 0 auto;
            padding: 20px;
            overflow-y: auto;
        }
        .message {
            margin: 10px 0;
            padding: 12px 16px;
            border-radius: 12px;
            max-width: 80%;
            animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .message.cypress {
            background: linear-gradient(135deg, #065f46 0%, #047857 100%);
            margin-right: auto;
            border-bottom-left-radius: 4px;
        }
        .message.redwood {
            background: linear-gradient(135deg, #7c2d12 0%, #9a3412 100%);
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }
        .message.matthew {
            background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%);
            margin: 10px auto;
            border-radius: 12px;
        }
        .message .meta {
            font-size: 0.75em;
            color: rgba(255,255,255,0.6);
            margin-bottom: 4px;
        }
        .message .content { line-height: 1.4; }
        .input-area {
            padding: 20px;
            border-top: 2px solid #0f3460;
            background: rgba(0,0,0,0.3);
        }
        .input-row {
            max-width: 800px;
            margin: 0 auto;
            display: flex;
            gap: 10px;
        }
        select, input, button {
            padding: 12px;
            border: 1px solid #0f3460;
            border-radius: 8px;
            background: #0d1117;
            color: #eee;
            font-size: 1em;
        }
        input { flex: 1; }
        button {
            background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
            color: #000;
            font-weight: bold;
            cursor: pointer;
            border: none;
        }
        button:hover { opacity: 0.9; }
        .status {
            text-align: center;
            padding: 10px;
            font-size: 0.85em;
            color: #888;
        }
        .status .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 5px; }
        .status .dot.online { background: #4ade80; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌲 Forest Chat</h1>
        <p style="color: #888; margin-top: 5px;">Cypress ↔ Redwood Communication</p>
    </div>
    
    <div class="status">
        <span class="dot online"></span> Live — Auto-refreshing every 3s
    </div>
    
    <div class="chat-container" id="chat"></div>
    
    <div class="input-area">
        <div class="input-row">
            <select id="sender">
                <option value="matthew">👤 Matthew</option>
                <option value="cypress">🌲 Cypress</option>
                <option value="redwood">🌲 Redwood</option>
            </select>
            <select id="recipient">
                <option value="all">📢 All</option>
                <option value="cypress">🌲 Cypress</option>
                <option value="redwood">🌲 Redwood</option>
            </select>
            <input type="text" id="message" placeholder="Type a message..." onkeypress="if(event.key==='Enter')sendMessage()">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>
    
    <script>
        let lastId = 0;
        
        async function loadMessages() {
            const resp = await fetch('/api/messages?since=' + lastId);
            const messages = await resp.json();
            
            if (messages.length > 0) {
                const chat = document.getElementById('chat');
                messages.forEach(m => {
                    if (m.id > lastId) lastId = m.id;
                    const div = document.createElement('div');
                    div.className = 'message ' + m.from;
                    const time = new Date(m.timestamp).toLocaleTimeString();
                    div.innerHTML = `
                        <div class="meta">${m.from} → ${m.to} • ${time}</div>
                        <div class="content">${m.message}</div>
                    `;
                    chat.appendChild(div);
                });
                chat.scrollTop = chat.scrollHeight;
            }
        }
        
        async function sendMessage() {
            const sender = document.getElementById('sender').value;
            const recipient = document.getElementById('recipient').value;
            const message = document.getElementById('message').value.trim();
            
            if (!message) return;
            
            await fetch('/api/send', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({from: sender, to: recipient, message: message})
            });
            
            document.getElementById('message').value = '';
            loadMessages();
        }
        
        // Initial load
        loadMessages();
        // Poll for new messages
        setInterval(loadMessages, 3000);
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
    print("🌲 Forest Chat starting on port 5001...")
    print(f"   Messages stored in: {MESSAGES_FILE}")
    print(f"   UI available at: http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)
