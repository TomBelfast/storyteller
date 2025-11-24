import json

with open('logs/system_events.json', 'r', encoding='utf-8') as f:
    lines = f.readlines()

output = []
output.append(f"=== LAST 20 VISUAL-RELATED LOGS ===\n")

visual_logs = []
for line in lines[-100:]:  # Check last 100
    try:
        entry = json.loads(line)
        record = entry['record']
        msg = record['message'].lower()
        
        if 'visual' in msg or 'plan' in msg or 'shot' in msg or 'scene' in msg:
            level = record['level']['name']
            message = record['message']
            exc = record.get('exception')
            
            visual_logs.append({
                'level': level,
                'message': message,
                'has_exception': bool(exc and exc.get('type'))
            })
    except:
        pass

for i, log in enumerate(visual_logs[-20:], 1):
    marker = "ERROR " if log['has_exception'] else ""
    output.append(f"{i}. [{log['level']}] {marker}{log['message']}\n")

output.append(f"\n=== EXCEPTIONS ===\n")

for line in lines[-50:]:
    try:
        entry = json.loads(line)
        record = entry['record']
        exc = record.get('exception')
        
        if exc and exc.get('type'):
            output.append(f"Exception: {exc.get('type')}\n")
            output.append(f"Value: {str(exc.get('value', ''))[:300]}\n")
            output.append("-" * 80 + "\n")
    except:
        pass

# Write to file
with open('log_analysis_output.txt', 'w', encoding='utf-8') as out:
    out.writelines(output)

print("Analysis written to log_analysis_output.txt")
