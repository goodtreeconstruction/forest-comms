#!/usr/bin/env python3
"""
🌲 Forest Chat Bridge - Polls for messages and wakes OpenClaw
Run this alongside forest-chat to automatically inject messages.
"""

import requests
import subprocess
import time
import os
import sys
import json

# Configuration
BOT_NAME = os.environ.get("FOREST_BOT_NAME", "redwood")  # default to redwood on this machine
FOREST_CHAT_URL = os.environ.get("FOREST_CHAT_URL", "http://localhost:5001")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "5"))  # seconds
TELEGRAM_GROUP = os.environ.get("TELEGRAM_GROUP", "")  # optional: mirror to telegram

def check_messages():
    """Check for new messages addressed to this bot."""
    try:
        resp = requests.get(
            f"{FOREST_CHAT_URL}/api/read",
            params={"for": BOT_NAME, "mark_read": "true"},
            timeout=5
        )
        if resp.ok:
            return resp.json()
    except Exception as e:
        print(f"Error checking messages: {e}")
    return []

def send_response(to, message):
    """Send a response via Forest Chat."""
    try:
        resp = requests.post(
            f"{FOREST_CHAT_URL}/api/send",
            json={"from": BOT_NAME, "to": to, "message": message},
            timeout=5
        )
        return resp.ok
    except Exception as e:
        print(f"Error sending response: {e}")
        return False

OUTBOX_DIR = os.path.expanduser("~/.openclaw/workspace/forest-outbox")
OUTBOX_FILE = os.path.join(OUTBOX_DIR, "reply.json")


def _read_outbox():
    try:
        if not os.path.exists(OUTBOX_FILE):
            return None
        with open(OUTBOX_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def wake_openclaw(message_text, sender):
    """Wake OpenClaw with the message.

    Option 2B (deterministic):
    - Ask OpenClaw (via /hooks/agent) to write a reply payload to OUTBOX_FILE.
    - Bridge then reads OUTBOX_FILE and POSTS the reply into Forest Chat.

    Env vars:
      - OPENCLAW_URL (default http://127.0.0.1:18789)
      - OPENCLAW_TOKEN (required)
    """
    print(f"[WAKE] Message from {sender}: {message_text}")

    openclaw_url = os.environ.get("OPENCLAW_URL", "http://127.0.0.1:18789").rstrip("/")
    token = os.environ.get("OPENCLAW_TOKEN")
    if not token:
        print("[WAKE] Missing OPENCLAW_TOKEN; cannot wake OpenClaw")
        return False

    os.makedirs(OUTBOX_DIR, exist_ok=True)

    # Snapshot current outbox content so we can detect updates.
    before = _read_outbox()

    prompt = (
        f"You are {BOT_NAME}. A message arrived in Forest Chat.\n\n"
        f"From: {sender}\n"
        f"Message: {message_text}\n\n"
        f"Write EXACTLY ONE JSON object to this file (overwrite):\n"
        f"{OUTBOX_FILE}\n\n"
        f"JSON schema:\n"
        f"{{\"from\":\"{BOT_NAME}\",\"to\":\"{sender}\",\"message\":\"<reply>\"}}\n\n"
        f"Rules:\n"
        f"- message must be plain text (no markdown fences)\n"
        f"- keep it short\n"
        f"- do not include extra keys\n"
    )

    payload = {
        "name": "Forest Chat",
        "sessionKey": f"hook:forest-chat:{BOT_NAME}",
        "wakeMode": "now",
        "deliver": False,
        "message": prompt,
    }

    try:
        resp = requests.post(
            f"{openclaw_url}/hooks/agent",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=10,
        )
        print(f"[WAKE] OpenClaw /hooks/agent -> {resp.status_code}")
        if not resp.ok:
            return False

        # Wait for OUTBOX_FILE to change (allow longer; hooks/agent is async).
        # Retry once if we time out.
        for attempt in (1, 2):
            deadline = time.time() + 60
            while time.time() < deadline:
                after = _read_outbox()
                if after and after != before:
                    try:
                        data = json.loads(after)
                        to = data.get("to")
                        msg = data.get("message")
                        if to and msg:
                            ok = send_response(to, msg)
                            print(f"[POSTBACK] -> {to} ok={ok}")
                            if ok:
                                try:
                                    os.remove(OUTBOX_FILE)
                                except OSError:
                                    pass
                            return ok
                    except Exception as e:
                        print(f"[POSTBACK] bad outbox json: {e}")
                        return False
                time.sleep(0.5)

            if attempt == 1:
                print("[POSTBACK] timeout waiting for outbox reply; retrying /hooks/agent once")
                before = _read_outbox()
                resp = requests.post(
                    f"{openclaw_url}/hooks/agent",
                    headers={"Authorization": f"Bearer {token}"},
                    json=payload,
                    timeout=10,
                )
                print(f"[WAKE] OpenClaw /hooks/agent (retry) -> {resp.status_code}")

        print("[POSTBACK] timeout waiting for outbox reply")
        return False

    except Exception as e:
        print(f"[WAKE] Error calling OpenClaw: {e}")
        return False

def main():
    print(f"Forest Chat Bridge starting for '{BOT_NAME}'")
    print(f"   Polling: {FOREST_CHAT_URL}")
    print(f"   Interval: {POLL_INTERVAL}s")
    
    while True:
        messages = check_messages()
        
        for msg in messages:
            sender = msg.get('from', 'unknown')
            content = msg.get('message', '')
            print(f"\n[MSG] New message from {sender}: {content[:50]}...")
            
            # Wake OpenClaw with the message
            wake_openclaw(content, sender)
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
