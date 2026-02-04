#!/usr/bin/env python3
"""
BigC CDP Communication Tool
Direct communication with Claude Desktop via Chrome DevTools Protocol

Usage:
    python bigc_cdp.py send "Your message here"
    python bigc_cdp.py read
    python bigc_cdp.py read --wait 10
    python bigc_cdp.py status
    python bigc_cdp.py chats
"""

import json
import asyncio
import argparse
import sys
import websockets
import aiohttp

MACHINES = {
    "redwood": {"host": "192.168.100.2", "port": 9222},
    "elm":     {"host": "100.93.49.28",  "port": 9222},
}
DEFAULT_MACHINE = "redwood"

# Legacy fallback
CDP_HOST = MACHINES[DEFAULT_MACHINE]["host"]
CDP_PORT = MACHINES[DEFAULT_MACHINE]["port"]

def get_machine(name=None):
    """Get host/port for a machine."""
    name = (name or DEFAULT_MACHINE).lower()
    if name not in MACHINES:
        print(f"ERROR: Unknown machine '{name}'. Available: {', '.join(MACHINES.keys())}")
        sys.exit(1)
    return MACHINES[name]["host"], MACHINES[name]["port"]

async def get_claude_tab(machine=None):
    """Find the Claude.ai tab."""
    host, port = get_machine(machine)
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://{host}:{port}/json") as resp:
            tabs = await resp.json()
            for tab in tabs:
                if "claude.ai" in tab.get("url", ""):
                    return tab
            # Fallback to first page type
            for tab in tabs:
                if tab.get("type") == "page" and "claude" in tab.get("title", "").lower():
                    return tab
    return None

async def check_ready_to_send(ws) -> dict:
    """Check if Claude is ready to receive a message (no stop button visible)."""
    js_check = '''
    (function() {
        const input = document.querySelector('div[contenteditable="true"]') ||
                      document.querySelector('textarea');
        const hasText = input && (input.innerText || input.value || '').trim().length > 0;
        
        // Check for Stop button (indicates Claude is still responding)
        const buttons = Array.from(document.querySelectorAll('button'));
        const stopBtn = buttons.find(b => {
            const label = b.getAttribute('aria-label') || '';
            const text = b.textContent || '';
            return label.includes('Stop') || text.includes('Stop');
        });
        
        return {
            has_text: hasText,
            stop_button: !!stopBtn,
            ready: hasText && !stopBtn
        };
    })();
    '''
    await ws.send(json.dumps({'id': 99, 'method': 'Runtime.evaluate',
                               'params': {'expression': js_check, 'returnByValue': True}}))
    result = json.loads(await ws.recv())
    return result.get('result', {}).get('result', {}).get('value', {})

async def send_message(message: str):
    """Send a message to BigC with smart wait for send button readiness."""
    tab = await get_claude_tab()
    if not tab:
        print("ERROR: No Claude tab found")
        return False
    
    ws_url = tab["webSocketDebuggerUrl"]
    
    async with websockets.connect(ws_url) as ws:
        # Type the message
        js_type = f'''
        (function() {{
            const input = document.querySelector('div[contenteditable="true"]') ||
                          document.querySelector('textarea');
            if (!input) return {{"ok": false, "error": "No input found"}};
            input.focus();
            if (input.tagName === 'TEXTAREA') {{
                input.value = {json.dumps(message)};
            }} else {{
                input.innerText = {json.dumps(message)};
            }}
            input.dispatchEvent(new Event('input', {{bubbles: true}}));
            return {{"ok": true, "typed": true}};
        }})();
        '''
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 
                                   'params': {'expression': js_type, 'returnByValue': True}}))
        result = json.loads(await ws.recv())
        
        if not result.get('result', {}).get('result', {}).get('value', {}).get('ok'):
            print(f"ERROR typing: {result}")
            return False
        
        # Wait for DOM to update
        await asyncio.sleep(0.3)
        
        # Wait for send button to be ready (no Stop button visible)
        ready_timeout = 30  # Max 30 seconds
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < ready_timeout:
            state = await check_ready_to_send(ws)
            
            if not state.get('stop_button'):
                # Ready to send!
                break
            
            # Claude is still responding, wait
            print("⏳ Waiting for Claude to finish responding...")
            await asyncio.sleep(0.5)
        else:
            print("⚠️ Timeout waiting for ready state, sending anyway...")
        
        # Press Enter to send
        js_enter = '''
        (function() {
            const input = document.querySelector('div[contenteditable="true"]') ||
                          document.querySelector('textarea');
            if (!input) return {"ok": false};
            input.dispatchEvent(new KeyboardEvent('keydown', {
                key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true
            }));
            return {"ok": true, "sent": true};
        })();
        '''
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate',
                                   'params': {'expression': js_enter, 'returnByValue': True}}))
        await ws.recv()
        
        print(f"✅ Message sent to BigC: {message[:50]}...")
        return True

async def read_response(wait_seconds: int = 0):
    """Read the latest response from BigC."""
    tab = await get_claude_tab()
    if not tab:
        print("ERROR: No Claude tab found")
        return None
    
    ws_url = tab["webSocketDebuggerUrl"]
    
    if wait_seconds > 0:
        print(f"Waiting {wait_seconds}s for BigC to respond...")
        await asyncio.sleep(wait_seconds)
    
    async with websockets.connect(ws_url) as ws:
        js_read = '''
        (function() {
            // Try to get Claude's responses
            const responses = document.querySelectorAll('.font-claude-response');
            if (responses.length > 0) {
                const last = responses[responses.length - 1];
                return {
                    "ok": true,
                    "response": last.innerText,
                    "count": responses.length
                };
            }
            
            // Alternative: get from prose containers
            const prose = document.querySelectorAll('[class*="prose"]');
            if (prose.length > 0) {
                const last = prose[prose.length - 1];
                return {
                    "ok": true, 
                    "response": last.innerText,
                    "count": prose.length
                };
            }
            
            return {"ok": false, "error": "No responses found"};
        })();
        '''
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate',
                                   'params': {'expression': js_read, 'returnByValue': True}}))
        result = json.loads(await ws.recv())
        
        value = result.get('result', {}).get('result', {}).get('value', {})
        if value.get('ok'):
            print(f"📖 BigC's latest response:\n{'-'*50}")
            print(value.get('response', ''))
            print('-'*50)
            return value.get('response')
        else:
            print(f"ERROR: {value.get('error', 'Unknown error')}")
            return None

async def check_streaming():
    """Check if BigC is currently streaming a response."""
    tab = await get_claude_tab()
    if not tab:
        return False
    
    ws_url = tab["webSocketDebuggerUrl"]
    
    async with websockets.connect(ws_url) as ws:
        js_check = '''
        (function() {
            const streaming = document.querySelector('[data-is-streaming="true"]');
            const stopBtn = document.querySelector('button[aria-label="Stop response"]');
            return {
                "streaming": !!streaming,
                "stopVisible": stopBtn ? window.getComputedStyle(stopBtn).display !== 'none' : false
            };
        })();
        '''
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate',
                                   'params': {'expression': js_check, 'returnByValue': True}}))
        result = json.loads(await ws.recv())
        return result.get('result', {}).get('result', {}).get('value', {}).get('streaming', False)

async def get_status():
    """Get BigC connection status."""
    tab = await get_claude_tab()
    if not tab:
        print("❌ Cannot connect to BigC - no Claude tab found")
        return
    
    print(f"✅ Connected to BigC")
    print(f"   Title: {tab.get('title', 'Unknown')}")
    print(f"   URL: {tab.get('url', 'Unknown')}")
    
    streaming = await check_streaming()
    if streaming:
        print("   Status: 🔄 STREAMING (BigC is responding)")
    else:
        print("   Status: ⏳ IDLE")

async def list_chats():
    """List available chats."""
    tab = await get_claude_tab()
    if not tab:
        print("ERROR: No Claude tab found")
        return
    
    ws_url = tab["webSocketDebuggerUrl"]
    
    async with websockets.connect(ws_url) as ws:
        js_chats = '''
        (function() {
            const chats = [];
            document.querySelectorAll('a[href*="/chat/"]').forEach(el => {
                const text = (el.innerText || '').trim();
                const href = el.href;
                if (text && href && !chats.some(c => c.href === href)) {
                    chats.push({text: text.substring(0, 50), href: href});
                }
            });
            return chats.slice(0, 15);
        })();
        '''
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate',
                                   'params': {'expression': js_chats, 'returnByValue': True}}))
        result = json.loads(await ws.recv())
        
        chats = result.get('result', {}).get('result', {}).get('value', [])
        print(f"📋 BigC's recent chats ({len(chats)}):")
        for i, chat in enumerate(chats, 1):
            print(f"   {i}. {chat['text']}")

async def send_and_wait(message: str, wait: int = 15):
    """Send message and wait for response."""
    if not await send_message(message):
        return None
    
    # Wait for response
    print(f"Waiting {wait}s for BigC to respond...")
    await asyncio.sleep(wait)
    
    # Check if still streaming
    while await check_streaming():
        print("Still streaming, waiting...")
        await asyncio.sleep(3)
    
    return await read_response()

async def navigate_new_chat():
    """Navigate to a new Claude chat."""
    tab = await get_claude_tab()
    if not tab:
        print("ERROR: No Claude tab found")
        return False
    
    ws_url = tab["webSocketDebuggerUrl"]
    
    async with websockets.connect(ws_url) as ws:
        js_navigate = '''
        (function() {
            window.location.href = 'https://claude.ai/new';
            return {"ok": true};
        })();
        '''
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate',
                                   'params': {'expression': js_navigate, 'returnByValue': True}}))
        await ws.recv()
        print("🆕 Navigating to new Claude chat...")
        return True

async def select_model(model_name: str = "sonnet"):
    """Select a model in the Claude UI."""
    tab = await get_claude_tab()
    if not tab:
        print("ERROR: No Claude tab found")
        return False
    
    ws_url = tab["webSocketDebuggerUrl"]
    
    async with websockets.connect(ws_url) as ws:
        # Click the model selector button
        js_click_selector = '''
        (function() {
            const modelBtn = document.querySelector('button[data-testid="model-selector"]') ||
                             document.querySelector('button:has-text("Claude")') ||
                             Array.from(document.querySelectorAll('button')).find(b => 
                                 b.textContent.includes('Sonnet') || 
                                 b.textContent.includes('Opus') ||
                                 b.textContent.includes('Haiku'));
            if (modelBtn) {
                modelBtn.click();
                return {"ok": true, "clicked": "model selector"};
            }
            return {"ok": false, "error": "Model selector not found"};
        })();
        '''
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate',
                                   'params': {'expression': js_click_selector, 'returnByValue': True}}))
        result = json.loads(await ws.recv())
        
        if not result.get('result', {}).get('result', {}).get('value', {}).get('ok'):
            print(f"Warning: Could not click model selector")
        
        await asyncio.sleep(0.5)
        
        # Click the Sonnet option
        js_select = f'''
        (function() {{
            const options = document.querySelectorAll('[role="menuitem"], [role="option"], button');
            for (const opt of options) {{
                if (opt.textContent.toLowerCase().includes('{model_name.lower()}')) {{
                    opt.click();
                    return {{"ok": true, "selected": opt.textContent}};
                }}
            }}
            return {{"ok": false, "error": "Model option not found"}};
        }})();
        '''
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate',
                                   'params': {'expression': js_select, 'returnByValue': True}}))
        result = json.loads(await ws.recv())
        
        value = result.get('result', {}).get('result', {}).get('value', {})
        if value.get('ok'):
            print(f"✅ Selected model: {value.get('selected')}")
            return True
        else:
            print(f"Warning: {value.get('error')}")
            return False

async def forest_status():
    """Show status of all machines in the forest."""
    for name, info in MACHINES.items():
        host, port = info["host"], info["port"]
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{host}:{port}/json", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    tabs = await resp.json()
                    claude_tab = None
                    for tab in tabs:
                        if "claude.ai" in tab.get("url", ""):
                            claude_tab = tab
                            break
                    if claude_tab:
                        print(f"  🌲 {name:10s} ✅ Online | {claude_tab.get('title', 'Unknown')[:50]}")
                    else:
                        print(f"  🌲 {name:10s} ⚠️  Online (no Claude tab) | {len(tabs)} tabs open")
        except Exception:
            print(f"  🌲 {name:10s} ❌ Offline")

def main():
    parser = argparse.ArgumentParser(description="BigC CDP Communication Tool - Forest Edition 🌲")
    parser.add_argument('-m', '--machine', default=None, help='Target machine (redwood, elm). Default: redwood')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # send command
    send_parser = subparsers.add_parser('send', help='Send a message to BigC')
    send_parser.add_argument('message', help='Message to send')
    send_parser.add_argument('--wait', type=int, default=0, help='Wait N seconds and read response')
    
    # read command
    read_parser = subparsers.add_parser('read', help='Read latest response from BigC')
    read_parser.add_argument('--wait', type=int, default=0, help='Wait N seconds before reading')
    
    # status command
    subparsers.add_parser('status', help='Check BigC connection status')
    
    # forest command (all machines)
    subparsers.add_parser('forest', help='Show status of all forest machines')
    
    # chats command
    subparsers.add_parser('chats', help='List BigC recent chats')
    
    # chat command (send and wait for response)
    chat_parser = subparsers.add_parser('chat', help='Send message and wait for response')
    chat_parser.add_argument('message', help='Message to send')
    chat_parser.add_argument('--wait', type=int, default=15, help='Max seconds to wait for response')
    
    # new command (start new chat)
    subparsers.add_parser('new', help='Navigate to a new Claude chat')
    
    # model command (select model)
    model_parser = subparsers.add_parser('model', help='Select a model')
    model_parser.add_argument('name', help='Model name (sonnet, opus, haiku)')
    
    args = parser.parse_args()
    
    # Set machine target globally
    if args.machine:
        global CDP_HOST, CDP_PORT, DEFAULT_MACHINE
        DEFAULT_MACHINE = args.machine.lower()
        CDP_HOST, CDP_PORT = get_machine(DEFAULT_MACHINE)
    
    if args.command == 'send':
        asyncio.run(send_message(args.message))
        if args.wait > 0:
            asyncio.run(read_response(args.wait))
    elif args.command == 'read':
        asyncio.run(read_response(args.wait))
    elif args.command == 'status':
        asyncio.run(get_status())
    elif args.command == 'forest':
        print("🌲 Forest Status:")
        asyncio.run(forest_status())
    elif args.command == 'chats':
        asyncio.run(list_chats())
    elif args.command == 'chat':
        asyncio.run(send_and_wait(args.message, args.wait))
    elif args.command == 'new':
        asyncio.run(navigate_new_chat())
    elif args.command == 'model':
        asyncio.run(select_model(args.name))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
