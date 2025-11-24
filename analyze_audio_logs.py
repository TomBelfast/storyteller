import json
from datetime import datetime

# Read logs and filter for audio-related entries
with open('logs/system_events.json', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== AUDIO GENERATION LOGS (Last 40 relevant entries) ===\n")

keywords = ['audio', 'chapter', 'clean', 'kokoro', 'timestamp', 'duration', 'characters', 'generating']
relevant_logs = []

for line in lines[-150:]:  # Check last 150 logs
    try:
        log = json.loads(line)
        record = log.get('record', {})
        message = record.get('message', '').lower()
        
        if any(kw in message for kw in keywords):
            time_str = record.get('time', {}).get('repr', 'N/A')[:19]
            level = record.get('level', {}).get('name', 'INFO')
            msg = record.get('message', '')
            relevant_logs.append(f"{time_str} [{level:5s}] {msg}")
    except:
        continue

# Print last 40 relevant logs
for log in relevant_logs[-40:]:
    print(log)
