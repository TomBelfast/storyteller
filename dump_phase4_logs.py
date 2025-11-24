import json

# Read last 100 logs to capture the full test
with open('logs/system_events.json', 'r', encoding='utf-8') as f:
    lines = f.readlines()

output_lines = ["=" * 80, "LAST 100 LOGS (PHASE 4 TEST)", "=" * 80, ""]

for line in lines[-100:]:
    try:
        log = json.loads(line)
        record = log.get('record', {})
        time_str = record.get('time', {}).get('repr', 'N/A')[:19]
        level = record.get('level', {}).get('name', 'INFO')
        msg = record.get('message', '')
        
        output_lines.append(f"{time_str} [{level:5s}] {msg}")
        
        # Show exception if present
        exc = record.get('exception')
        if exc:
            exc_text = exc.get('text', '')
            if exc_text:
                output_lines.append(f"  EXCEPTION TRACEBACK:")
                for exc_line in exc_text.split('\n')[:10]:
                    output_lines.append(f"    {exc_line}")
    except:
        continue

with open('PHASE4_LOGS.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print(f"Saved {len(output_lines)} lines to PHASE4_LOGS.txt")
