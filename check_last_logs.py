import json

# Read last logs
with open('logs/system_events.json', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== LAST 20 LOGS ===\n")

for line in lines[-20:]:
    try:
        log = json.loads(line)
        record = log.get('record', {})
        time_str = record.get('time', {}).get('repr', 'N/A')[:19]
        level = record.get('level', {}).get('name', 'INFO')
        msg = record.get('message', '')
        
        print(f"{time_str} [{level:5s}] {msg}")
        
        # Show exception if present
        exc = record.get('exception')
        if exc:
            print(f"  EXCEPTION: {exc.get('type', 'Unknown')}: {exc.get('value', '')}")
    except:
        continue
