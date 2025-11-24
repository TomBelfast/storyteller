import requests
import json
from config import settings

api_url = settings.NOCODB_API_URL
table_id = settings.NOCODB_PROJECTS_TABLE_ID
headers = {"xc-token": settings.NOCODB_API_TOKEN}

# Test with Visual Story JSON field
test_timestamps = [
    {"word": "Coffee's", "start_time": 0.0, "end_time": 0.5},
    {"word": "journey", "start_time": 0.5, "end_time": 1.0}
]

payload = [{
    "Id": 5,
    "Visual Story JSON": json.dumps(test_timestamps),
    "Word Count": 179.49
}]

print(f"Testing Visual Story JSON field...")
print(f"Payload: {json.dumps(payload, indent=2)}")

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
print(f"Visual Story JSON: {data.get('Visual Story JSON')}")
