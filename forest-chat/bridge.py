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

# Configuration
BOT_NAME = os.environ.get("FOREST_BOT_NAME", "cypress")  # or "redwood"
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

def wake_openclaw(message_text, sender):
    """
    Wake OpenClaw with the message.
    This uses the cron wake mechanism to inject the message.
    """
    # For now, we'll just print - the actual injection depends on OpenClaw's API
    print(f"[WAKE] Message from {sender}: {message_text}")
    
    # Option 1: Use openclaw CLI if available
    # subprocess.run(["openclaw", "chat", "--message", message_text])
    
    # Option 2: Write to a file that OpenClaw watches
    wake_file = os.path.expanduser(f"~/.openclaw/workspace/forest-inbox/{sender}.txt")
    os.makedirs(os.path.dirname(wake_file), exist_ok=True)
    with open(wake_file, 'w') as f:
        f.write(message_text)
    
    return True

def main():
    print(f"🌲 Forest Chat Bridge starting for '{BOT_NAME}'")
    print(f"   Polling: {FOREST_CHAT_URL}")
    print(f"   Interval: {POLL_INTERVAL}s")
    
    while True:
        messages = check_messages()
        
        for msg in messages:
            sender = msg.get('from', 'unknown')
            content = msg.get('message', '')
            print(f"\n📨 New message from {sender}: {content[:50]}...")
            
            # Wake OpenClaw with the message
            wake_openclaw(content, sender)
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
