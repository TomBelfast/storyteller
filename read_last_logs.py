import json
from datetime import datetime

# Read last 30 log entries
with open("logs/system_events.json", "r", encoding="utf-8") as f:
    lines = f.readlines()
    
last_logs = lines[-30:]

print("OSTATNIE 30 LOGÓW:")
print("=" * 80)
for line in last_logs:
    try:
        log = json.loads(line)
        record = log.get("record", {})
        time_str = record.get("time", {}).get("repr", "N/A")
        level = record.get("level", {}).get("name", "INFO")
        message = record.get("message", "")
        
        print(f"[{time_str}] {level}: {message}")
    except:
        pass
