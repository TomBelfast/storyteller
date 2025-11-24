import requests
import json
from config import settings

api_url = settings.NOCODB_API_URL
table_id = settings.NOCODB_PROJECTS_TABLE_ID
headers = {"xc-token": settings.NOCODB_API_TOKEN}

# Test minimal payload with Word Count and Production Script
payload = [{
    "Id": 5,
    "Word Count": 179,
    "Production Script": "TEST DIRECT UPDATE"
}]

print(f"Sending payload: {json.dumps(payload, indent=2)}")

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
print(f"Production Script: {data.get('Production Script')}")
