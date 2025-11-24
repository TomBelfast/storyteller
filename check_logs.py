import json

def read_last_errors():
    log_file = "logs/system_events.json"
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        print("Last 5 ERROR logs:")
        count = 0
        for line in reversed(lines):
            try:
                log = json.loads(line)
                record = log.get("record", {})
                level = record.get("level", {}).get("name")
                if level == "ERROR":
                    print(f"[{record['time']['repr']}] {record['message']}")
                    if record.get("exception"):
                        print(f"Exception: {record['exception']}")
                    count += 1
                    if count >= 5: break
            except:
                continue
    except Exception as e:
        print(f"Error reading logs: {e}")

if __name__ == "__main__":
    read_last_errors()
