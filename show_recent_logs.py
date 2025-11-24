import json

def show_recent_logs():
    try:
        with open("logs/system_events.json", "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        print("Last 10 logs:")
        for line in lines[-10:]:
            try:
                data = json.loads(line)
                record = data.get("record", {})
                time = record.get("time", {}).get("repr", "")
                level = record.get("level", {}).get("name", "")
                msg = record.get("message", "")
                print(f"[{time}] {level}: {msg}")
            except:
                continue
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    show_recent_logs()
