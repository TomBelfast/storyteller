import json
import sys

# Force UTF-8 output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

with open('logs/system_events.json', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
print(f"Total log entries: {len(lines)}")
print(f"Showing last 30:\n")
print("=" * 100)

# Get last 30 entries
for i, line in enumerate(lines[-30:], 1):
    try:
        entry = json.loads(line)
        record = entry.get('record', {})
        
        level = record.get('level', {}).get('name', 'INFO')
        message = record.get('message', '')
        module = record.get('name', '')
        function = record.get('function', '')
        exception_info = record.get('exception')
        
        print(f"\n[{i}] {level} | {module}.{function}")
        print(f"    Message: {message}")
        
        if exception_info and exception_info.get('type'):
            print(f"    EXCEPTION: {exception_info.get('type', 'Unknown')}")
            print(f"    Value: {exception_info.get('value', '')}")
            if exception_info.get('traceback'):
                tb = exception_info['traceback']
                # Show last 300 chars of traceback
                print(f"    Traceback:\n{tb[-300:]}")
            print("-" * 80)
            
    except Exception as e:
        print(f"Parse error on line {i}: {e}")
