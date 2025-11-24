import json

# Read last 150 logs
with open('logs/system_events.json', 'r', encoding='utf-8') as f:
    lines = f.readlines()

output_lines = ["=" * 80, "KOKORO DIRECT TEST LOGS (LAST 150)", "=" * 80, ""]

for line in lines[-150:]:
    try:
        log = json.loads(line)
        record = log.get('record', {})
        time_str = record.get('time', {}).get('repr', 'N/A')[:19]
        level = record.get('level', {}).get('name', 'INFO')
        msg = record.get('message', '')
        
        output_lines.append(f"{time_str} [{level:5s}] {msg}")
    except:
        continue

with open('KOKORO_TEST_LOGS.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

# Use logger to confirm
from utils.logger import logger
logger.info(f"Saved {len(output_lines)} lines to KOKORO_TEST_LOGS.txt")
