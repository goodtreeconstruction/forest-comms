#!/usr/bin/env python3
"""
BigC CDP - Cypress → BigC Communication via Chrome DevTools Protocol

Sends messages to Claude Desktop by injecting into the input field.
Uses smart wait: polls for Stop button to disappear before sending.

Based on claude_scout.py from central-command-dashboard.

Usage:
    from bigc_cdp import send_to_bigc
    send_to_bigc("PING: Task complete!")

Requirements:
    - Claude Desktop running with remote debugging enabled
    - pip install websocket-client requests
"""

# TODO: Cypress to push actual implementation
# This is a placeholder showing the expected interface

import json
import time
import requests
import websocket
from typing import Optional, Dict, Any

DEBUG_PORT = 9222
CLAUDE_URL_FILTER = "claude.ai"


def get_websocket_url() -> Optional[str]:
    """Find Claude Desktop page via CDP."""
    try:
        resp = requests.get(f"http://127.0.0.1:{DEBUG_PORT}/json", timeout=2)
        targets = resp.json()
        for t in targets:
            if t.get("type") == "page" and CLAUDE_URL_FILTER in t.get("url", ""):
                return t.get("webSocketDebuggerUrl")
    except:
        pass
    return None


def execute_js(js: str, return_value: bool = False) -> Any:
    """Execute JavaScript via CDP."""
    ws_url = get_websocket_url()
    if not ws_url:
        return None
    
    try:
        ws = websocket.create_connection(ws_url, timeout=5)
        params = {"expression": js}
        if return_value:
            params["returnByValue"] = True
        ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": params}))
        result = json.loads(ws.recv())
        ws.close()
        
        if return_value:
            return result.get("result", {}).get("result", {}).get("value")
        return result
    except Exception as e:
        print(f"[bigc_cdp] CDP error: {e}")
        return None


def check_ready() -> Dict[str, bool]:
    """
    Check if Claude is ready to receive a message.
    Returns: {has_text, stop_button, ready}
    """
    js = """
    (function() {
        const input = document.querySelector(div[contenteditable=true]);
        const hasText = input && input.innerText.trim().length > 0;
        const buttons = Array.from(document.querySelectorAll(button));
        const stopBtn = buttons.find(b => (b.getAttribute(aria-label) || ).includes(Stop));
        return {
            has_text: hasText,
            stop_button: !!stopBtn,
            ready: hasText && !stopBtn
        };
    })();
    """
    result = execute_js(js, return_value=True)
    return result or {"has_text": False, "stop_button": False, "ready": False}


def wait_for_ready(timeout: float = 30.0) -> bool:
    """Wait for Claude to be ready (no Stop button)."""
    start = time.time()
    while time.time() - start < timeout:
        state = check_ready()
        if not state.get("stop_button"):
            return True
        time.sleep(0.5)
    return False


def set_input_text(text: str) -> bool:
    """Set text in Claude input box."""
    safe_text = json.dumps(text)
    js = f"""
    (function() {{
        const input = document.querySelector(div[contenteditable=true]);
        if (!input) return false;
        input.focus();
        input.innerHTML = {safe_text};
        input.dispatchEvent(new Event(input, {{bubbles: true}}));
        return true;
    }})();
    """
    result = execute_js(js, return_value=True)
    return result == True


def press_enter() -> bool:
    """Press Enter to send message."""
    js = """
    (function() {
        const input = document.querySelector(div[contenteditable=true]);
        if (!input) return false;
        input.focus();
        input.dispatchEvent(new KeyboardEvent(keydown, {
            key: Enter, code: Enter, keyCode: 13, which: 13, bubbles: true
        }));
        return true;
    })();
    """
    result = execute_js(js, return_value=True)
    return result == True


def send_to_bigc(message: str, timeout: float = 30.0) -> bool:
    """
    Send a message to BigC (Claude Desktop).
    
    1. Wait for Claude to be ready (no Stop button)
    2. Set input text
    3. Wait for DOM update
    4. Press Enter
    
    Args:
        message: Text to send
        timeout: Max seconds to wait for ready state
    
    Returns:
        True if sent successfully
    """
    print(f"[bigc_cdp] Waiting for ready...")
    if not wait_for_ready(timeout):
        print(f"[bigc_cdp] Timeout waiting for ready")
        return False
    
    print(f"[bigc_cdp] Setting input text...")
    if not set_input_text(message):
        print(f"[bigc_cdp] Failed to set input")
        return False
    
    time.sleep(0.3)  # DOM update
    
    print(f"[bigc_cdp] Sending...")
    if not press_enter():
        print(f"[bigc_cdp] Failed to press Enter")
        return False
    
    print(f"[bigc_cdp] ✓ Sent!")
    return True


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
        send_to_bigc(msg)
    else:
        print("Usage: python bigc_cdp.py <message>")

