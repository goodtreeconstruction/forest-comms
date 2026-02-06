Set-Location "C:\Users\Matthew\forest-comms\forest-chat"
$env:POLL_INTERVAL = "1"
$env:FOREST_BOT_NAME = "redwood"
$env:FOREST_CHAT_URL = "http://127.0.0.1:5001"
$env:OPENCLAW_URL = "http://127.0.0.1:18789"
$env:OPENCLAW_TOKEN = "9b4c7ffaaac9fa84a157dc42f4f936e481a8c0f609c2e3ec"
& "C:\Users\Matthew\forest-comms\forest-chat\.venv\Scripts\python.exe" -u -X utf8 bridge.py
