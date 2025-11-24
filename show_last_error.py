import json

def print_last_error():
    try:
        with open("logs/system_events.json", "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for line in reversed(lines):
            try:
                data = json.loads(line)
                record = data.get("record", {})
                if record.get("level", {}).get("name") == "ERROR":
                    print(f"TIMESTAMP: {record.get('time', {}).get('repr')}")
                    print("LAST ERROR MESSAGE:")
                    print(record["message"])
                    if "exception" in record:
                        print("EXCEPTION:")
                        print(record["exception"])
                    return
            except:
                continue
        print("No errors found in last lines.")
    except Exception as e:
        print(f"Failed to read logs: {e}")

if __name__ == "__main__":
    print_last_error()
