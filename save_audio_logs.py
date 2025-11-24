import json

# Read last 200 logs
with open('logs/system_events.json', 'r', encoding='utf-8') as f:
    lines = f.readlines()

keywords = ['audio', 'chapter', 'clean', 'kokoro', 'timestamp', 'duration', 'characters', 'generating', 'text']
relevant_logs = []

for line in lines[-200:]:
    try:
        log = json.loads(line)
        record = log.get('record', {})
        message = record.get('message', '').lower()
        
        if any(kw in message for kw in keywords):
            time_str = record.get('time', {}).get('repr', 'N/A')[:19]
            level = record.get('level', {}).get('name', 'INFO')
            msg = record.get('message', '')
            relevant_logs.append({
                "time": time_str,
                "level": level,
                "message": msg
            })
    except:
        continue

# Save to JSON
with open('audio_logs.json', 'w', encoding='utf-8') as f:
    json.dump(relevant_logs[-50:], f, indent=2, ensure_ascii=False)

print(f"Saved {len(relevant_logs[-50:])} logs to audio_logs.json")
