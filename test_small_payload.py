import requests
import json
from config import settings

api_url = settings.NOCODB_API_URL
table_id = settings.NOCODB_PROJECTS_TABLE_ID
headers = {"xc-token": settings.NOCODB_API_TOKEN}

# Test with 3 timestamps (small payload)
small_timestamps = [
    {"word": "Test", "start_time": 0.0, "end_time": 0.5},
    {"word": "Small", "start_time": 0.5, "end_time": 1.0},
    {"word": "Payload", "start_time": 1.0, "end_time": 1.5}
]

payload = [{
    "Id": 5,
    "Audio URL": "http://small-test.com/audio.mp3",
    "Production Script": json.dumps(small_timestamps),
    "Word Count": 1.5
}]

print(f"Payload size: {len(json.dumps(payload))} bytes")
print(f"Sending...")

resp = requests.patch(
    f"{api_url}/api/v2/tables/{table_id}/records",
    json=payload,
    headers=headers
)

print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")

# Verify
get_resp = requests.get(f"{api_url}/api/v2/tables/{table_id}/records/5", headers=headers)
data = get_resp.json()
print(f"\nVerification:")
print(f"Word Count: {data.get('Word Count')}")
print(f"Production Script length: {len(data.get('Production Script', ''))}")
print(f"Audio URL: {data.get('Audio URL')}")
